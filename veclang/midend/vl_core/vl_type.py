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
VlTypeStrs: list[VlTypeStr] = [
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

VlTypeCode = typing.Literal[
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x06, 0x07, 0x08, 0x09
]
VlTypeCodes: list[VlTypeCode] = [
    0x00,
    0x01,
    0x02,
    0x03,
    0x04,
    0x05,
    0x06,
    0x06,
    0x07,
    0x08,
    0x09,
]

VlTypeType = typing.Literal["VAL", "OBJ"]


class VlMethod:

    def __init__(
        self,
        name: str,
        arg_types: list[VlTypeStr],
        return_type: VlTypeStr,
        fn_id: int,
        help_str: str,
    ) -> None:
        self.name: str = name
        self.arg_types: list[VlTypeStr] = arg_types
        self.return_type: VlTypeStr = return_type
        self.fn_id: int = fn_id
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


class VlConstexprOperation(VlOperation):
    """
    A VlConstexprOperation has an eval_fn that gets passed the underlying Python objects as a arguments,
    but must return a VlTypeABC.
    """

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

    def evaluate(self, *args: "VlTypeABC") -> "VlTypeABC":
        if self.op_arity == "UNARY" and len(args) != 1:
            raise ValueError("Unary operation must take exactly 1 operand.")
        elif self.op_arity == "BINARY" and len(args) != 2:
            raise ValueError("Binary operation must take exactly 2 operands.")
        elif self.op_arity == "TERNARY" and len(args) != 3:
            raise ValueError("Ternary operation must take exactly 3 operands.")
        elif self.op_arity not in ["UNARY", "BINARY", "TERNARY"]:
            raise ValueError(f"Unknown operation arity: '{self.op_type}'.")
        return self.eval_fn(*[arg.underlying for arg in args])


class VlCast:

    def __init__(self, to_type: VlTypeStr, fn_id: int, is_widening: bool) -> None:
        self.to_type: VlTypeStr = to_type
        self.fn_id: int = fn_id
        self.is_widening: bool = is_widening


class VlConstexprCast(VlCast):
    """
    A VlConstexprCast has an eval_fn that gets passed the underlying Python object as an argument,
    but must return a VlTypeABC.
    """

    def __init__(
        self,
        to_type: VlTypeStr,
        fn_id: int,
        is_widening: bool,
        eval_fn: typing.Callable,
    ) -> None:
        super().__init__(to_type, fn_id, is_widening)
        self.eval_fn = eval_fn

    def evaluate(self, arg: "VlTypeABC") -> "VlTypeABC":
        return self.eval_fn(arg.underlying)


class VlTypeABC(abc.ABC):

    def __init__(self, underlying: typing.Any) -> None:
        self.underlying = underlying

    @staticmethod
    @abc.abstractmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        """
        Gets basic information about the type, including:
        - its identifier
        - its type code
        - its type ("VAL" or "OBJ")
        - its canonical size in bytes in 32-bit and 64-bit runtime precision
        :return: tuple[type_name, type_type, tuple[32bit_bytes, 64bit_byte]]
        """
        pass

    @classmethod
    def to_vl_type_str(cls) -> VlTypeStr:
        return cls.get_info()[0]

    @classmethod
    def to_vl_type_code(cls):
        return cls.get_info()[1]

    @classmethod
    def is_val(cls) -> bool:
        if cls.get_info()[2] in ["VAL", "OBJ"]:
            return cls.get_info()[2] == "VAL"
        else:
            raise ValueError(f"Unknown VlTypeType '{cls.get_info()[2]}'")

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
    def get_properties() -> list[VlMethod]:
        """
        A property is just syntactic sugar for calling a method on a piece of data where:
        - The only argument passed to the method is the piece of data itself
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def get_casts() -> list[VlCast]:
        pass

    @abc.abstractmethod
    def to_bytes_32(self) -> bytes:
        pass

    @abc.abstractmethod
    def to_bytes_64(self) -> bytes:
        pass


VlType = typing.Type[VlTypeABC]


@dataclasses.dataclass
class VlFunctionParameterTypeProfile:
    identifier: str
    vl_type: VlType


@dataclasses.dataclass
class VlBuiltinFunctionTypeProfile:
    identifier: str
    builtin_fn_id: int
    parameters: list[VlFunctionParameterTypeProfile]
    return_type: VlType


@dataclasses.dataclass
class VlUserdefFunctionTypeProfile:
    identifier: str
    userdef_fn_idx: int
    parameters: list[VlFunctionParameterTypeProfile]
    return_type: VlType
