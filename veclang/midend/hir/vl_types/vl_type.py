import abc
import typing

from veclang.frontend.parser.vl_ast import VlOperatorType


VlOperatorArity = typing.Literal["UNARY", "BINARY", "TERNARY"]

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

VlTypeType = typing.Literal["VAL", "OBJ"]


class VlMethod:

    def __init__(self):
        pass


class VlOperation(abc.ABC):
    """boip"""

    def __init__(
        self,
        op_arity: VlOperatorArity,
        op_type: VlOperatorType,
        operand_types: list[VlTypeStr],
        opcode_hr: str,
    ):
        self.op_arity: VlOperatorArity = op_arity
        self.op_type: VlOperatorType = op_type
        self.operand_types: list[VlTypeStr] = operand_types
        self.opcode_hr: str = opcode_hr


class VlConstOperation(VlOperation):

    @abc.abstractmethod
    def evaluate(self, *args):
        if self.op_arity == "UNARY" and len(args) != 0:
            raise ValueError("Unary operation must take exactly 1 operand.")
        elif self.op_arity == "BINARY" and len(args) != 1:
            raise ValueError("Binary operation must take exactly 2 operands.")
        elif self.op_arity == "TERNARY" and len(args) != 2:
            raise ValueError("Ternary operation must take exactly 3 operands.")
        else:
            raise ValueError(f"Unknown operation arity: '{self.op_type}'.")


class VlTypeABC(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        """
        Gets basic information about the type, including:
        - its name
        - its type ("VAL" or "OBJ")
        - its size in bytes in 32-bit and 64-bit modes
        :return: tuple[type_name, type_type, tuple[32bit_bytes, 64bit_byte]]
        """
        pass

    @classmethod
    def is_val(cls) -> bool:
        if cls.get_info()[1] in ["VAL", "OBJ"]:
            return cls.get_info()[1] == "VAL"
        else:
            raise ValueError(f"Unknown VlTypeType '{cls.get_info()[1]}'")

    @classmethod
    def is_obj(cls) -> bool:
        return not cls.is_val()

    @staticmethod
    @abc.abstractmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    @abc.abstractmethod
    def get_methods() -> list[VlMethod]:
        pass


VlType = typing.Type[VlTypeABC]
