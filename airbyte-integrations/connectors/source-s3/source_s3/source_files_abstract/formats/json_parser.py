#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from typing import Any, BinaryIO, Iterator, Mapping, TextIO, Union

import pyarrow as pa
from pyarrow import json as pa_json

from .abstract_file_parser import AbstractFileParser
from .json_spec import JsonFormat


class JsonParser(AbstractFileParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.format_model = None

    @property
    def is_binary(self) -> bool:
        return True

    @property
    def format(self) -> JsonFormat:
        if self.format_model is None:
            self.format_model = JsonFormat.parse_obj(self._format)
        return self.format_model

    def _read_options(self) -> Mapping[str, str]:
        """
        https://arrow.apache.org/docs/python/generated/pyarrow.csv.ReadOptions.html
        build ReadOptions object like: pa.json.ReadOptions(**self._read_options())
        """
        return {**{"block_size": self.format.block_size, "use_threads": True}}

    def _parse_options(self) -> Mapping[str, str]:
        """
        https://arrow.apache.org/docs/python/generated/pyarrow.json.ParseOptions.html
         build ParseOptions object like: pa.json.ParseOptions(**self._parse_options())
        """

        return {"newlines_in_values": self.format.newlines_in_values, "unexpected_field_behavior": self.format.unexpected_field_behavior}

    def _read_table(self, file: Union[TextIO, BinaryIO]) -> pa.Table:
        return pa_json.read_json(file, pa.json.ReadOptions(**self._read_options()), pa.json.ParseOptions(**self._parse_options()))

    def get_inferred_schema(self, file: Union[TextIO, BinaryIO]) -> Mapping[str, Any]:
        """
        https://arrow.apache.org/docs/python/generated/pyarrow.json.read_json.html
        Json reader support multi thread hence, donot need to add external process
        https://arrow.apache.org/docs/python/generated/pyarrow.json.ReadOptions.html
        """
        table = self._read_table(file)
        schema_dict = {field.name: field.type for field in table.schema}
        return self.json_schema_to_pyarrow_schema(schema_dict, reverse=True)

    def stream_records(self, file: Union[TextIO, BinaryIO]) -> Iterator[Mapping[str, Any]]:
        """
        https://arrow.apache.org/docs/python/generated/pyarrow.json.read_json.html

        """
        table = self._read_table(file)
        yield from table.to_pylist()
