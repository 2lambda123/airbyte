#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
from enum import Enum
from pathlib import Path

from ci_connector_ops.utils import Connector
from dagger import Container


class StepStatus(Enum):
    SUCCESS = "🟢"
    FAILURE = "🔴"
    SKIPPED = "🟡"

    def from_exit_code(exit_code: int):
        if exit_code == 0:
            return StepStatus.SUCCESS
        if exit_code == 1:
            return StepStatus.FAILURE

    def __str__(self) -> str:
        return self.value


async def check_path_in_workdir(container: Container, path: str):
    workdir = (await container.with_exec(["pwd"]).stdout()).strip()
    mounts = await container.mounts()
    if workdir in mounts:
        expected_file_path = Path(workdir[1:]) / path
        return expected_file_path.is_file() or expected_file_path.is_dir()
    else:
        return False


def write_connector_secrets_to_local_storage(connector: Connector, gsm_credentials: str):
    """Download and write connector's secrets locally.

    Args:
        connector (Connector): The connector for which you want to download secrets.
        gsm_credentials (str): The credentials to connect to GSM.
    """
    connector_secrets = connector.get_secret_manager(gsm_credentials).read_from_gsm()

    for secret in connector_secrets:
        secret_directory = Path(secret.directory)
        secret_directory.mkdir(parents=True, exist_ok=True)
        filepath = secret_directory / secret.configuration_file_name
        with open(filepath, "w") as file:
            file.write(secret.value)
