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
        result_type: VlTypeStr,
        fast_jmp_opcode_hr: str | None = None,
    ) -> None:
        self.op_arity: VlOperatorArity = op_arity
        self.op_type: VlOperatorType = op_type
        self.operand_types: list[VlTypeStr] = operand_types
        self.opcode_hr: str = opcode_hr
        self.result_type: str = result_type
        self.fast_jmp_opcode_hr: str | None = fast_jmp_opcode_hr


class VlConstOperation(VlOperation):

    def __init__(
        self,
        op_arity: VlOperatorArity,
        op_type: VlOperatorType,
        operand_types: list[VlTypeStr],
        opcode_hr: str,
        result_type: VlTypeStr,
        eval_fn: typing.Callable,
        fast_jmp_opcode_hr: str | None = None,
    ) -> None:
        super().__init__(
            op_arity,
            op_type,
            operand_types,
            opcode_hr,
            result_type,
            fast_jmp_opcode_hr,
        )
        self.eval_fn: typing.Callable = eval_fn

    def evaluate(self, *args):
        if self.op_arity == "UNARY" and len(args) != 0:
            raise ValueError("Unary operation must take exactly 1 operand.")
        elif self.op_arity == "BINARY" and len(args) != 1:
            raise ValueError("Binary operation must take exactly 2 operands.")
        elif self.op_arity == "TERNARY" and len(args) != 2:
            raise ValueError("Ternary operation must take exactly 3 operands.")
        elif self.op_arity not in ["UNARY", "BINARY", "TERNARY"]:
            raise ValueError(f"Unknown operation arity: '{self.op_type}'.")
        return self.eval_fn(args)


class VlCast:

    def __init__(self, to_type: VlTypeStr) -> None:
        self.to_type: VlTypeStr = to_type


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

    @staticmethod
    @abc.abstractmethod
    def get_casts() -> list[VlCast]:
        pass


VlType = typing.Type[VlTypeABC]
