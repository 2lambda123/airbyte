from magibyte.operations.base_operation import BaseOperation


class BaseState(BaseOperation):

    def get(self, context):
        raise NotImplementedError()
