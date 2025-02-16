"""Utility types"""

import typing


class PositionInfo(typing.NamedTuple):
    """Position info of an AST node"""

    line_number: typing.Optional[int]
    line_character_number: typing.Optional[int]


class TypeProfile(typing.NamedTuple):
    """A type profile"""

    type_name: str
    type_qualifier: str


class IdentifiedTypeProfile(typing.NamedTuple):
    """A type profile attached to an identifier"""

    identifier: str
    type_name: str
    type_qualifier: str


class FunctionTypesProfile(typing.NamedTuple):
    """A function profile"""

    return_type: TypeProfile
    input_types: typing.List[IdentifiedTypeProfile]


IdentifierTypesContext = typing.Dict[str, TypeProfile]
FunctionTypesContext = typing.Dict[str, FunctionTypesProfile]


LinterWeakWarningCodeLiteral = typing.Literal["X000", "X001", "X002"]

LinterStrongWarningCodeLiteral = typing.Literal[
    "W000", "W010", "W011", "W012", "W020", "W021"
]

LinterErrorCodeLiteral = typing.Literal[
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
    A generic linter weak item
    """

    def __init__(
        self,
        position_info: PositionInfo,
        code: LinterWeakWarningCodeLiteral,
        stack_trace: str,
        message: str,
    ) -> None:
        self.line_no: int = position_info.line_number
        self.char_no: int = position_info.line_character_number
        self.code: LinterWeakWarningCodeLiteral = code
        self.stack_trace: str = stack_trace
        self.message: str = message

    def __str__(self) -> str:
        return f"Linter weak warning on line {self.line_no}, char {self.char_no} ({self.code}): '{self.message}'"

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


LinterItems = typing.List[LinterItem]
