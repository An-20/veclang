import abc
import typing
import dataclasses

from veclang.frontend.parser.vl_ast import VlOperatorType


VlOperatorArity = typing.Literal["UNARY", "BINARY", "TERNARY"]

VlTypeStr = typing.Literal[
    "null",
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
    "null",
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

    def __init__(
        self,
        name: str,
        arg_types: list[VlTypeStr],
        return_type: VlTypeStr,
        id_code: int,
        help_str: str,
    ) -> None:
        self.name: str = name
        self.arg_types: list[VlTypeStr] = arg_types
        self.return_type: VlTypeStr = return_type
        self.id_code: int = id_code
        self.help_str: str = help_str


class VlOperation(abc.ABC):
    """boip"""

    def __init__(
        self,
        op_arity: VlOperatorArity,
        op_type: VlOperatorType,
        operand_types: list[VlTypeStr],
        result_type: VlTypeStr,
        opcode_hr: str,
        extra_opcode_hr: str | None = None,
    ) -> None:
        self.op_arity: VlOperatorArity = op_arity
        self.op_type: VlOperatorType = op_type
        self.operand_types: list[VlTypeStr] = operand_types
        self.opcode_hr: str = opcode_hr
        self.result_type: str = result_type
        self.extra_opcode_hr: str | None = extra_opcode_hr


class VlConstOperation(VlOperation):

    def __init__(
        self,
        op_arity: VlOperatorArity,
        op_type: VlOperatorType,
        operand_types: list[VlTypeStr],
        result_type: VlTypeStr,
        eval_fn: typing.Callable,
        opcode_hr: str,
        extra_opcode_hr: str | None = None,
    ) -> None:
        super().__init__(
            op_arity, op_type, operand_types, result_type, opcode_hr, extra_opcode_hr
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

    def __init__(self, to_type: VlTypeStr, method_name: str) -> None:
        self.to_type: VlTypeStr = to_type
        self.method_name: str = method_name


class VlTypeABC(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        """
        Gets basic information about the type, including:
        - its identifier
        - its type ("VAL" or "OBJ")
        - its size in bytes in 32-bit and 64-bit modes
        :return: tuple[type_name, type_type, tuple[32bit_bytes, 64bit_byte]]
        """
        pass

    @classmethod
    def to_vl_type_str(cls) -> VlTypeStr:
        return cls.get_info()[0]

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


@dataclasses.dataclass
class VlFunctionParameterTypeProfile:
    identifier: str
    vl_type: VlType


@dataclasses.dataclass
class VlFunctionTypeProfile:
    identifier: str
    parameters: list[VlFunctionParameterTypeProfile]
    return_type: VlType


class VlBuiltinFunction:

    def __init__(
        self,
        name: str,
        arg_types: list[VlTypeStr],
        return_type: VlTypeStr,
        id_code: int,
        help_str: str,
    ) -> None:
        self.name: str = name
        self.arg_types: list[VlTypeStr] = arg_types
        self.return_type: VlTypeStr = return_type
        self.id_code: int = id_code
        self.help_str: str = help_str
