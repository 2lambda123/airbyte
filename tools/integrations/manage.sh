#!/usr/bin/env bash

set -e
set -x

. tools/lib/lib.sh

USAGE="
Usage: $(basename "$0") <cmd>
For publish, if you want to push the spec to the spec cache, provide a path to a service account key file that can write to the cache.
Available commands:
  scaffold
  test <integration_root_path>
  build  <integration_root_path> [<run_tests>]
  publish  <integration_root_path> [<run_tests>] [--publish_spec_to_cache] [--publish_spec_to_cache_with_key_file <path to keyfile>]
  publish_external  <image_name> <image_version>
"

_check_tag_exists() {
  DOCKER_CLI_EXPERIMENTAL=enabled docker manifest inspect "$1" > /dev/null
}

_error_if_tag_exists() {
    if _check_tag_exists "$1"; then
      error "You're trying to push a version that was already released ($1). Make sure you bump it up."
    fi
}

cmd_scaffold() {
  echo "Scaffolding connector"
  (
    cd airbyte-integrations/connector-templates/generator &&
    ./generate.sh "$@"
  )
}

cmd_build() {
  local path=$1; shift || error "Missing target (root path of integration) $USAGE"
  [ -d "$path" ] || error "Path must be the root path of the integration"

  local run_tests=$1; shift || run_tests=true

  echo "Building $path"
  ./gradlew --no-daemon "$(_to_gradle_path "$path" clean)"
  ./gradlew --no-daemon "$(_to_gradle_path "$path" build)"
}

cmd_test() {
  local path=$1; shift || error "Missing target (root path of integration) $USAGE"
  [ -d "$path" ] || error "Path must be the root path of the integration"

  echo "Running integration tests..."
  ./gradlew --no-daemon "$(_to_gradle_path "$path" integrationTest)"
}

# Bumps connector version in Dockerfile, definitions.yaml file
#
# NOTE: this does NOT update changelogs because the changelog markdown files do not have a reliable machine-readable
# format to automatically handle this. Someday it could though: https://github.com/airbytehq/airbyte/issues/12031
cmd_bump_version() {
  # Take params
  local connector_path
  local bump_version
  connector_path="$1"; shift || error "Missing target (path) $USAGE"
  bump_version="$1"; shift || error "Missing target (bump_version) $USAGE"

  # Set local constants
  connector=${connector_path#airbyte-integrations/connectors/}
  if [[ "$connector" =~ "source-" ]]; then
    connector_type="source"
  elif [[ "$connector" =~ "destination-" ]]; then
    connector_type="destination"
  else
    echo "Invalid connector_type from $connector"
    exit 1
  fi
  definitions_path="./airbyte-config/init/src/main/resources/seed/${connector_type}_definitions.yaml"
  dockerfile="$connector_path/Dockerfile"
  master_dockerfile="/tmp/master_${connector}_dockerfile"
  # This allows getting the contents of a file without checking it out
  git fetch origin --quiet
  git --no-pager show "origin/master:$dockerfile" > "$master_dockerfile"

  # Get connector version on current branch and from master. Because we need to know what
  # tag is on ths current branch for search/replace, but we need to know what version is in master
  # to know what to bump to.
  branch_version=$(_get_docker_image_version "$dockerfile")
  master_version=$(_get_docker_image_version "$master_dockerfile")
  local image_name; image_name=$(_get_docker_image_name "$dockerfile")
  rm "$master_dockerfile"

  ## Create bumped version based on master
  major_version=$(echo "$master_version" | cut -d. -f1)
  minor_version=$(echo "$master_version" | cut -d. -f2)
  patch_version=$(echo "$master_version" | cut -d. -f3)

  echo "major_version: $major_version"
  echo "minor_version: $minor_version"
  echo "patch_version: $patch_version"

  case "$bump_version" in
    "major")
      ((major_version++))
      minor_version=0
      patch_version=0
      ;;
    "minor")
      ((minor_version++))
      patch_version=0
      ;;
    "patch")
      ((patch_version++))
      ;;
    *)
      echo "Invalid bump_version option: $bump_version. Valid options are major, minor, patch"
      exit 1
      ;;
  esac

  bumped_version="$major_version.$minor_version.$patch_version"
  if [[ "$FORCE_BUMP" == "true" ]] || [[ "$bumped_version" != "$master_version" && "$bumped_version" != "$branch_version" ]]; then
    _error_if_tag_exists "$image_name:$bumped_version"
    echo "$connector:$branch_version will be bumped to $connector:$bumped_version"

    # Set outputs back to Github Actions for later steps
    echo ::set-output name=master_version::"${master_version}"
    echo ::set-output name=bumped_version::"${bumped_version}"
    echo ::set-output name=bumped::"true"
  else
    echo "No version bump was necessary, this PR has probably already been bumped"
    exit 0
  fi

  ## Write new version to files
  # 1) Dockerfile
  sed -i "s/$branch_version/$bumped_version/g" "$dockerfile"

  # 2) Definitions YAML file
  definitions_check=$(yq e ".. | select(has(\"dockerRepository\")) | select(.dockerRepository == \"$image_name\")" "$definitions_path")

  if [[ (-z "$definitions_check") ]]; then
    echo "Could not find $connector in $definitions_path, exiting 1"
    exit 1
  fi

  connector_name=$(yq e ".[] | select(has(\"dockerRepository\")) | select(.dockerRepository == \"$image_name\") | .name" "$definitions_path")
  yq e "(.[] | select(.name == \"$connector_name\").dockerImageTag)|=\"$bumped_version\"" -i "$definitions_path"

  echo "Woohoo! Successfully bumped $connector:$branch_version to $connector:$bumped_version"
}

# Generate new spec, publish to GCS, generate updated seeds.yaml file. Runs after cmd_bump_version
cmd_process_build() {
  local connector_path
  connector_path="$1"; shift || error "Missing target (path) $USAGE"
  dockerfile="$connector_path/Dockerfile"
  local image_name; image_name=$(_get_docker_image_name "$dockerfile")
  bumped_version=$(_get_docker_image_version "$dockerfile")

  _publish_spec_to_cache "$image_name" "$bumped_version"
  ./gradlew :airbyte-config:init:processResources
}

# TODO: also should be post merge step
# Checking if the image was successfully registered on DockerHub
# see the description of this PR to understand why this is needed https://github.com/airbytehq/airbyte/pull/11654/
_ensure_docker_image_registered() {
  local image_name; image_name="$1"
  local image_version; image_version="$1"

  # Checking if the image was successfully registered on DockerHub
  # see the description of this PR to understand why this is needed https://github.com/airbytehq/airbyte/pull/11654/
  sleep 5

  # To work for private repos we need a token as well
  DOCKER_USERNAME=${DOCKER_USERNAME:-airbytebot}
  DOCKER_TOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"username": "'${DOCKER_USERNAME}'", "password": "'${DOCKER_PASSWORD}'"}' https://hub.docker.com/v2/users/login/ | jq -r .token)
  TAG_URL="https://hub.docker.com/v2/repositories/${image_name}/tags/${image_version}"
  DOCKERHUB_RESPONSE_CODE=$(curl --silent --output /dev/null --write-out "%{http_code}" -H "Authorization: JWT ${DOCKER_TOKEN}" "${TAG_URL}")
  if [[ "${DOCKERHUB_RESPONSE_CODE}" == "404" ]]; then
    echo "Tag ${image_version} was not registered on DockerHub for image ${image_name}, please try to bump the version again." && exit 1
  fi
}

# We generate a spec based on the built image rather than using spec.json because not all connectors actually
# use spec.json, some use a python pydantic file, and Java based connectors can place spec.json in the src dir
_generate_spec() {
  local versioned_image; versioned_image="$1"

  docker run --rm "$versioned_image" spec | \
    # 1. filter out any lines that are not valid json.
    jq -R "fromjson? | ." | \
    # 2. grab any json that has a spec in it.
    # 3. if there are more than one, take the first one.
    # 4. if there are none, throw an error.
    jq -s "map(select(.spec != null)) | map(.spec) | first | if . != null then . else error(\"no spec found\") end"
}

# Generates spec from container and pushes it into a GCS bucket which Airbyte can pull from to more efficiently
# get a connector's spec to render the UI rather than running a container first
_publish_spec_to_cache() {
  local image_name; image_name=$1
  local image_version; image_version=$2

  if [[ "${publish_spec_to_cache}" == "true" ]]; then
    echo "Publishing and writing to spec cache."

    # Create tmp spec file
    local tmp_spec_file; tmp_spec_file=$(mktemp)
    _generate_spec "$image_name:$image_version" > "$tmp_spec_file"

    echo "Created $image_name:$image_version spec file:"

    # use service account key file is provided.
    if [[ -n "${spec_cache_writer_sa_key_file}" ]]; then
      echo "Using provided service account key"
      gcloud auth activate-service-account --key-file "$spec_cache_writer_sa_key_file"
    else
      echo "Using environment gcloud"
    fi

    gsutil cp "$tmp_spec_file" "gs://io-airbyte-cloud-spec-cache/specs/$image_name/$image_version/spec.json"
  else
    echo "Publishing without writing to spec cache."
  fi
}

cmd_publish() {
  local path=$1; shift || error "Missing target (root path of integration) $USAGE"
  [ -d "$path" ] || error "Path must be the root path of the integration"

  local publish_spec_to_cache
  local spec_cache_writer_sa_key_file

  while [ $# -ne 0 ]; do
    case "$1" in
    --publish_spec_to_cache)
      publish_spec_to_cache=true
      shift 1
      ;;
    --publish_spec_to_cache_with_key_file)
      publish_spec_to_cache=true
      spec_cache_writer_sa_key_file="$2"
      shift 2
      ;;
    *)
      error "Unknown option: $1"
      ;;
    esac
  done

  if [[ ! $path =~ "connectors" ]]
  then
     # Do not publish spec to cache in case this is not a connector
     publish_spec_to_cache=false
  fi

  # setting local variables for docker image versioning
  local image_name; image_name=$(_get_docker_image_name "$path"/Dockerfile)
  local image_version; image_version=$(_get_docker_image_version "$path"/Dockerfile)
  local versioned_image=$image_name:$image_version
  local latest_image=$image_name:latest

  echo "image_name $image_name"
  echo "versioned_image $versioned_image"
  echo "latest_image $latest_image"

  # before we start working sanity check that this version has not been published yet, so that we do not spend a lot of
  # time building, running tests to realize this version is a duplicate.
  _error_if_tag_exists "$versioned_image"

  if [[ "airbyte/normalization" == "${image_name}" ]]; then
    echo "Publishing normalization images (version: $versioned_image)"
    GIT_REVISION=$(git rev-parse HEAD)
    VERSION=$image_version GIT_REVISION=$GIT_REVISION docker-compose -f airbyte-integrations/bases/base-normalization/docker-compose.build.yaml build
    VERSION=$image_version GIT_REVISION=$GIT_REVISION docker-compose -f airbyte-integrations/bases/base-normalization/docker-compose.build.yaml push
    VERSION=latest         GIT_REVISION=$GIT_REVISION docker-compose -f airbyte-integrations/bases/base-normalization/docker-compose.build.yaml build
    VERSION=latest         GIT_REVISION=$GIT_REVISION docker-compose -f airbyte-integrations/bases/base-normalization/docker-compose.build.yaml push
  else
    docker tag "$image_name:dev" "$versioned_image"
    docker tag "$image_name:dev" "$latest_image"

    echo "Publishing new version ($versioned_image)"
#    docker push "$versioned_image"
#    docker push "$latest_image"
  fi

  _ensure_docker_image_registered "$image_name" "$image_version"
}

cmd_publish_external() {
  local image_name=$1; shift || error "Missing target (image name) $USAGE"
  # Get version from the command
  local image_version=$1; shift || error "Missing target (image version) $USAGE"

  echo "image $image_name:$image_version"

  echo "Publishing and writing to spec cache."
  # publish spec to cache. do so, by running get spec locally and then pushing it to gcs.
  local tmp_spec_file; tmp_spec_file=$(mktemp)
  docker run --rm "$image_name:$image_version" spec | \
    # 1. filter out any lines that are not valid json.
    jq -R "fromjson? | ." | \
    # 2. grab any json that has a spec in it.
    # 3. if there are more than one, take the first one.
    # 4. if there are none, throw an error.
    jq -s "map(select(.spec != null)) | map(.spec) | first | if . != null then . else error(\"no spec found\") end" \
    > "$tmp_spec_file"

  echo "Using environment gcloud"

  gsutil cp "$tmp_spec_file" "gs://io-airbyte-cloud-spec-cache/specs/$image_name/$image_version/spec.json"
}

main() {
  assert_root

  local cmd=$1; shift || error "Missing cmd $USAGE"
  cmd_"$cmd" "$@"
}

main "$@"
