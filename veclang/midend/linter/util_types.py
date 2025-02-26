"""Utility types"""

import typing
import dataclasses

from veclang.frontend.parser.vl_ast import ASTPositionInfo


IdentifiedTypeProfiles = dict[str, VlType]


@dataclasses.dataclass
class FunctionTypesProfile:
    parameter_types: IdentifiedTypeProfiles
    return_type: VlType


@dataclasses.dataclass
class FunctionTypeContext:
    variable_types: IdentifiedTypeProfiles
    constant_types: IdentifiedTypeProfiles


LinterCodeLiteral = typing.Literal[
    "W000",
    "W010",
    "W011",
    "W012",
    "W020",
    "W021",
    "E000",
    "E001",
    "E002",
    "E010",
    "E011",
    "E100",
    "E101",
    "E102",
    "E103",
    "E104",
    "E105",
    "E106",
    "E107",
    "E108",
    "E109",
    "E110",
    "E111",
    "E112",
    "E113",
    "E120",
    "E121",
    "E122",
    "E123",
    "E200",
    "E201",
    "E210",
    "E211",
    "E300",
    "E301",
    "E310",
    "E311",
    "E312",
    "E320",
    "E321",
    "E330",
    "E331",
    "E400",
    "E401",
    "E410",
    "E500",
]


class LinterItemDict(typing.TypedDict):
    """A linter item as a dictionary"""

    line_no: int
    char_no: int
    code: str
    stack_trace: str
    message: str


class LinterItem:
    """
    A generic linter item
    """

    def __init__(
        self,
        position_info: ASTPositionInfo,
        code: LinterCodeLiteral,
        stack_trace: str,
        message: str,
    ) -> None:
        self.line_no: int = position_info.line_number
        self.char_no: int = position_info.line_character_number
        self.code: LinterCodeLiteral = code
        self.stack_trace: str = stack_trace
        self.message: str = message

    def __str__(self) -> str:
        item_type = "warning" if self.code[0] == "W" else "error"
        return f"Linter {item_type} on line {self.line_no}, char {self.char_no} ({self.code}): '{self.message}'"

    def __repr__(self):
        return str(self)

    def to_dict(self) -> LinterItemDict:
        """Returns LinterItemDict from LinterItem"""
        return {
            "line_no": self.line_no,
            "char_no": self.char_no,
            "code": self.code,
            "stack_trace": self.stack_trace,
            "message": self.message,
        }
