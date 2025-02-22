import abc
import typing

from veclang.frontend.parser.vl_ast import VlOperatorType


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


class Operation(abc.ABC):
    """boip"""

    @abc.abstractmethod
    def emit_bytecode(self):
        pass


class UnaryOperation:
    def __init__(self) -> None:
        pass


class VlTypeABC(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def get_name() -> VlTypeStr:
        pass

    @staticmethod
    @abc.abstractmethod
    def is_val() -> bool:
        pass

    @classmethod
    def is_obj(cls) -> bool:
        return not cls.is_val()

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
    def is_val() -> bool:
        return True

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
    def is_val() -> bool:
        return True

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
