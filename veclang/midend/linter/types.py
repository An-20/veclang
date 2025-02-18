import abc

from veclang.frontend.parser.vl_ast import VlOperator
from veclang.midend.vl_hir import VlType


class Method:

    def __init__(self):
        pass


class Operation:

    def __init__(self):
        pass


class VlTypeABC(abc.ABC):

    @staticmethod
    def get_name():
        pass

    @staticmethod
    def get_operations() -> list[Operation]:
        pass

    @staticmethod
    def get_methods() -> list[Method]:
        pass
