import abc

from veclang.frontend.parser.vl_ast import VlOperator


class Method:

    def __init__(self):
        pass


class Operation:

    def __init__(self):
        pass


class VlTypeABC(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def get_name():
        pass

    @staticmethod
    @abc.abstractmethod
    def get_size() -> int:
        """Returns the size of the type, in bytes"""

    @staticmethod
    @abc.abstractmethod
    def get_operations() -> list[Operation]:
        pass

    @staticmethod
    @abc.abstractmethod
    def get_methods() -> list[Method]:
        pass


class VlInt(VlTypeABC):

    @staticmethod
    def get_name():
        return "int"

    @staticmethod
    def get_size() -> int:
        return 4

    @staticmethod
    def get_operations() -> list[Operation]:
        pass

    @staticmethod
    def get_methods() -> list[Method]:
        pass


class VlReal(VlTypeABC):

    @staticmethod
    def get_name():
        return "real"

    @staticmethod
    def get_size() -> int:
        return 4

    @staticmethod
    def get_operations() -> list[Operation]:
        pass

    @staticmethod
    def get_methods() -> list[Method]:
        pass
