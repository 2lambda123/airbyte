#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#
import datetime

from airbyte_cdk.sources.cac.interpolation.interpolation import Interpolation
from jinja2 import Environment


class JinjaInterpolation(Interpolation):
    def __init__(self):
        self._environment = Environment()
        self._environment.globals["now_local"] = datetime.datetime.now
        self._environment.globals["now_utc"] = lambda: datetime.datetime.now(datetime.timezone.utc)
        self._environment.globals["today_utc"] = lambda: datetime.datetime.now(datetime.timezone.utc).date()

    def eval(self, input_str: str, vars, config, stream_slice=None, stream_state=None):
        print(f"jinajinterpolation.eval: {input_str}")
        print(f"eval vars: {vars}")
        print(f"eval config: {config}")
        context = {"vars": vars, "config": config, "stream_slice": stream_slice, "stream_state": stream_state}
        print(f"context: {context}")
        print(f"type: {type(input_str)}")
        if isinstance(input_str, str):
            print("eval")
            ret = self._environment.from_string(input_str).render(context)
        else:
            print(f"noteval for {input_str}")
            ret = None
        print(f"interpolation result: {ret}")
        return ret
