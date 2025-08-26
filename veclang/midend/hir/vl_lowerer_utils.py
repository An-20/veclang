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

    is_loop_var: bool
    is_parameter: bool
    is_import: bool


@dataclasses.dataclass
class VlFnParamTypeProfile:
    identifier: str
    vl_type: VlType


@dataclasses.dataclass
class VlImportedFunctionProfile:
    fr_identifier: str
    builtin_fn_id: int
    parameters: list[VlFnParamTypeProfile]
    return_type: VlType

    ref_read_count: int


@dataclasses.dataclass
class VlUserdefFunctionProfile:
    identifier: str
    userdef_fn_idx: int
    parameters: list[VlFnParamTypeProfile]
    return_type: VlType
    attribute_tags: dict[str, int]

    ref_read_count: int


@dataclasses.dataclass
class Scope:
    fn_name: str | None
    fn_return_type: VlType
    loop_name: str | None
    selection_name: str | None
    ast_position_info: ASTPositionInfo

    # Tuple of [type_or_value, is_variable
    data: dict[str, IdentifierData]
    imported_functions: dict[str, VlImportedFunctionProfile]


def format_operator(operator: VlOperatorType) -> str:
    operator_hr_map = {
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
    }
    if operator not in operator_hr_map:
        raise ValueError(f"IE: unknown operator '{operator}'")
    return operator_hr_map[operator]


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
