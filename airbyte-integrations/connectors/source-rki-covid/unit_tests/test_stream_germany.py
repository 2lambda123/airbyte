#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from source_rki_covid.source import RkiCovidStream, Germany


@pytest.fixture
def patch_germany_class(mocker):
    # Mock abstract methods to enable instantiating abstract class
    mocker.patch.object(Germany, "primary_key", None)


def test_path(patch_germany_class):
    stream = Germany()
    expected_params = {"path": "germany"}
    assert stream.path() == expected_params.get("path")