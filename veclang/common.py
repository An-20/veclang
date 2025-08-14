import typing
import dataclasses


COMPILER_VERSION_STR: str = "1.0.0"
LANGUAGE_VERSION_STR: str = "2.0.0"
LANGUAGE_VERSION_INT: int = 0x0002_0000


@dataclasses.dataclass
class CompilerFlags:
    runtime_precision: typing.Literal[32, 64]


DiagnosticCode = typing.Literal[
    "E000",
    "E100",
    "E101",
    "E102",
    "E103",
    "E104",
    "E105",
    "E106",
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
    "W014",
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
        line_no: int,
        char_no: int,
        code: DiagnosticCode,
        stack_trace: str,
        message: str,
    ) -> None:
        self.line_no: int = line_no
        self.char_no: int = char_no
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

    def __repr__(self):
        return str(self)


class FatalCompileError(RuntimeError):
    pass
