import re
import typing
import dataclasses

from veclang.frontend.parser.vl_ast import ASTPositionInfo, VlOperatorType
from veclang.midend.vl_core import VlType, VlTypeABC


VlQualifier = typing.Literal[
    "constexpr",
    "const",
    "var",
]
VlQualifierValues: list[VlQualifier] = [
    "constexpr",
    "const",
    "var",
]


def vl_qualifier_to_hr(qualifier: VlQualifier) -> str:
    if qualifier not in VlQualifierValues:
        raise ValueError(f"IE: Unknown VlQualifier '{qualifier}'")
    return {
        "constexpr": "constexpr",
        "const": "constant",
        "var": "variable",
    }[qualifier]


@dataclasses.dataclass
class IdentifierData:
    ast_position_info: ASTPositionInfo
    vl_qualifier: VlQualifier
    vl_type: VlType
    vl_value: VlTypeABC
    ref_read_count: int
    ref_write_count: int

    is_parameter: bool


@dataclasses.dataclass
class Scope:
    fn_name: str | None
    fn_return_type: VlType
    loop_name: str | None
    selection_name: str | None
    ast_position_info: ASTPositionInfo

    # Tuple of [type_or_value, is_variable
    data: dict[str, IdentifierData]


DiagnosticCode = typing.Literal[
    "E000",
    "E100",
    "E101",
    "E102",
    "E103",
    "E110",
    "E111",
    "E112",
    "E120",
    "E121",
    "E122",
    "E200",
    "E201",
    "E202",
    "E210",
    "E300",
    "E310",
    "E311",
    "E320",
    "E321",
    "E330",
    "E331",
    "E900",
    "W001",
    "W002",
    "W010",
    "W011",
    "W012",
    "W013",
    "X000",
    "X001",
    "X002",
    "X003",
    "X100",
]


@dataclasses.dataclass
class Diagnostic:

    def __init__(
        self,
        position_info: ASTPositionInfo,
        code: DiagnosticCode,
        stack_trace: str,
        message: str,
    ) -> None:
        self.line_no: int = position_info.line_number
        self.char_no: int = position_info.line_character_number
        self.code: DiagnosticCode = code
        self.stack_trace: str = stack_trace
        self.message: str = message

    def __str__(self) -> str:
        if self.code.startswith("X"):
            diagnostic_type = "weak warning"
        elif self.code.startswith("W"):
            diagnostic_type = "warning"
        elif self.code.startswith("E"):
            diagnostic_type = "error"
        else:
            raise ValueError(f"Unknown diagnostic code '{self.code}'")
        return (
            f"{diagnostic_type.capitalize()} {self.code} at {self.line_no}:{self.char_no}:"
            f" '{self.message}'"
        )


class FatalCompileError(RuntimeError):
    pass


def format_operator(operator: VlOperatorType) -> str:
    return {
        "PLUS_ASSIGNMENT": "+=",
        "MINUS_ASSIGNMENT": "-=",
        "TIMES_ASSIGNMENT": "*=",
        "DIVIDE_ASSIGNMENT": "/=",
        "MODULUS_ASSIGNMENT": "%=",
        "PLUS": "+",
        "MINUS": "-",
        "TIMES": "*",
        "DIVIDE": "/",
        "MODULUS": "%",
        "INTEGER_DIVIDE": "//",
        "EXPONENTIATION": "^",
        "BOOLEAN_AND": "&&",
        "BOOLEAN_OR": "||",
        "BITWISE_AND": "&",
        "BITWISE_OR": "|",
        "BITWISE_XOR": "^",
        "BITWISE_LEFT_SHIFT": "<<",
        "BITWISE_RIGHT_SHIFT": ">>",
        "EQUAL_TO": "==",
        "NOT_EQUAL_TO": "!=",
        "LESS_THAN": "<",
        "LESS_THAN_OR_EQUAL": "<=",
        "GREATER_THAN": ">",
        "GREATER_THAN_OR_EQUAL": ">=",
        "BOOLEAN_NOT": "!",
        "BITWISE_NOT": "~",
        "UNARY_PLUS": "+",
        "UNARY_MINUS": "-",
    }.get(operator, __default=operator)


def check_constant_case(input_str: str) -> bool:
    """Checks if a string uses constant case"""
    # allow single char
    if len(input_str) == 1:
        return True
    allowed_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "_"
    return all([char in allowed_characters for char in input_str])


def check_snake_case(input_str: str) -> bool:
    """Checks if a string uses snake case"""
    if input_str == "_":
        return True
    pattern = r"^[a-z0-9]+(_[a-z0-9]+)*$"
    return bool(re.match(pattern, input_str))
