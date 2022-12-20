#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

import json
import logging
from typing import Any, Dict
from airbyte_cdk.models import (
    AirbyteMessage,
    AirbyteRecordMessage,
    AirbyteStream,
    AirbyteStateMessage,
    ConfiguredAirbyteStream,
    ConfiguredAirbyteCatalog,
    SyncMode,
    DestinationSyncMode,
    Type,
)
import responses
from destination_convex.client import ConvexClient

from destination_convex.config import ConvexConfig
from destination_convex.destination import DestinationConvex
import pytest


@pytest.fixture(name="config")
def config_fixture() -> ConvexConfig:
    with open("secrets/local_config.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture(name="client")
def client_fixture(config) -> ConvexClient:
    return ConvexClient(config)


@pytest.fixture(name="configured_catalog")
def configured_catalog_fixture() -> ConfiguredAirbyteCatalog:
    stream_schema = {"type": "object", "properties": {"string_col": {"type": "str"}, "int_col": {"type": "integer"}}}

    append_stream = ConfiguredAirbyteStream(
        stream=AirbyteStream(name="append_stream", json_schema=stream_schema, supported_sync_modes=[SyncMode.incremental]),
        sync_mode=SyncMode.incremental,
        destination_sync_mode=DestinationSyncMode.append,
    )

    overwrite_stream = ConfiguredAirbyteStream(
        stream=AirbyteStream(name="overwrite_stream", json_schema=stream_schema, supported_sync_modes=[SyncMode.incremental]),
        sync_mode=SyncMode.incremental,
        destination_sync_mode=DestinationSyncMode.overwrite,
    )

    return ConfiguredAirbyteCatalog(streams=[append_stream, overwrite_stream])


def _state(data: Dict[str, Any]) -> AirbyteMessage:
    return AirbyteMessage(type=Type.STATE, state=AirbyteStateMessage(data=data))


def _record(stream: str, str_value: str, int_value: int) -> AirbyteMessage:
    return AirbyteMessage(
        type=Type.RECORD, record=AirbyteRecordMessage(stream=stream, data={"str_col": str_value, "int_col": int_value}, emitted_at=0)
    )


def setup_responses(config):
    responses.add(responses.PUT, f"{config['deployment_url']}/api/clear_tables", status=200)
    responses.add(responses.POST, f"{config['deployment_url']}/api/airbyte_ingress", status=200)
    responses.add(responses.GET, f"{config['deployment_url']}/version", status=200)


@responses.activate
def test_check(config: ConvexConfig):
    setup_responses(config)
    destination = DestinationConvex()
    logger = logging.getLogger("airbyte")
    destination.check(logger, config)


@responses.activate
def test_write(config: ConvexConfig, configured_catalog: ConfiguredAirbyteCatalog):
    setup_responses(config)
    append_stream, overwrite_stream = configured_catalog.streams[0].stream.name, configured_catalog.streams[1].stream.name

    first_state_message = _state({"state": "1"})
    first_record_chunk = [_record(append_stream, str(i), i) for i in range(5)] + [_record(overwrite_stream, str(i), i) for i in range(5)]

    second_state_message = _state({"state": "2"})
    second_record_chunk = [_record(append_stream, str(i), i) for i in range(5, 10)] + [
        _record(overwrite_stream, str(i), i) for i in range(5, 10)
    ]

    destination = DestinationConvex()

    expected_states = [first_state_message, second_state_message]
    output_states = list(
        destination.write(
            config, configured_catalog, [*first_record_chunk, first_state_message, *second_record_chunk, second_state_message]
        )
    )
    assert expected_states == output_states, "Checkpoint state messages were expected from the destination"

    third_state_message = _state({"state": "3"})
    third_record_chunk = [_record(append_stream, str(i), i) for i in range(10, 15)] + [
        _record(overwrite_stream, str(i), i) for i in range(10, 15)
    ]

    output_states = list(destination.write(config, configured_catalog, [*third_record_chunk, third_state_message]))
    assert [third_state_message] == output_states
