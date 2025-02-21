import abc
import typing

from veclang.frontend.parser.vl_ast import VlOperator


VlTypeStr = typing.Literal[
    "int",
    "bool",
    "real",
    "complex",
    "vec2",
    "vec3",
    "vec4",
    "mat2",
    "mat3",
    "mat4",
]
VlTypeStrs = [
    "int",
    "bool",
    "real",
    "complex",
    "vec2",
    "vec3",
    "vec4",
    "mat2",
    "mat3",
    "mat4",
]


class Method:

    def __init__(self):
        pass


class Operation:

    def __init__(self):
        pass


class VlTypeABC(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def get_name() -> VlTypeStr:
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
    def get_name() -> VlTypeStr:
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
    def get_name() -> VlTypeStr:
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


VlType = typing.Type[VlTypeABC]
