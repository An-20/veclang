from veclang.midend.vl_core.vl_type import (
    VlTypeABC,
    VlTypeStr,
    VlTypeType,
    VlOperation,
    VlConstOperation,
    VlMethod,
    VlCast,
)


class VlNull(VlTypeABC):

    def __init__(self, underlying: None) -> None:
        if underlying is not None:
            raise ValueError(
                f"Underlying value of VlNull must be a Python None, not '{type(underlying)}'"
            )
        self.underlying: None = None

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "null", "VAL", (0, 0)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        return []

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlInt(VlTypeABC):

    def __init__(self, underlying: int) -> None:
        if not isinstance(underlying, int):
            raise ValueError(
                f"Underlying value of VlInt must be a Python int, not '{type(underlying)}'"
            )
        self.underlying: int = underlying

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "int", "VAL", (4, 8)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        return [
            VlConstOperation(
                "BINARY",
                "EQUAL_TO",
                ["int"],
                "bool",
                lambda x, y: x == y,
                "OP_INT_EQUAL",
                extra_opcode_hr="OP_INT_JMP_IF_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["int"],
                "bool",
                lambda x, y: x != y,
                "OP_INT_NOT_EQUAL",
                extra_opcode_hr="OP_INT_JMP_IF_NOT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN",
                ["int"],
                "bool",
                lambda x, y: x > y,
                "OP_INT_GREATER",
                extra_opcode_hr="OP_INT_JMP_IF_GREATER",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN_OR_EQUAL",
                ["int"],
                "bool",
                lambda x, y: x >= y,
                "OP_INT_GREATER_OR_EQUAL",
                extra_opcode_hr="OP_INT_JMP_IF_GREATER_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN",
                ["int"],
                "bool",
                lambda x, y: x < y,
                "OP_INT_LESS",
                extra_opcode_hr="OP_INT_JMP_IF_LESS",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN_OR_EQUAL",
                ["int"],
                "bool",
                lambda x, y: x <= y,
                "OP_INT_LESS_OR_EQUAL",
                extra_opcode_hr="OP_INT_JMP_IF_LESS_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY", "PLUS", ["int"], "int", lambda x, y: x + y, "OP_INT_ADD"
            ),
            VlConstOperation(
                "BINARY",
                "MINUS",
                ["int"],
                "int",
                lambda x, y: x - y,
                "OP_INT_SUB",
            ),
            VlConstOperation(
                "BINARY",
                "TIMES",
                ["int"],
                "int",
                lambda x, y: x * y,
                "OP_INT_MUL",
            ),
            VlConstOperation(
                "BINARY",
                "DIVIDE",
                ["int"],
                "int",
                lambda x, y: x // y,
                "OP_INT_DIV",
            ),
            VlConstOperation(
                "BINARY",
                "MODULUS",
                ["int"],
                "int",
                lambda x, y: x % y,
                "OP_INT_MOD",
            ),
            VlConstOperation(
                "BINARY",
                "EXPONENTIATION",
                ["int"],
                "int",
                lambda x, y: x**y,
                "OP_INT_EXP",
            ),
            VlConstOperation(
                "UNARY",
                "UNARY_MINUS",
                [],
                "int",
                lambda x: -x,
                "OP_INT_NEG",
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_AND",
                ["int"],
                "int",
                lambda x, y: x & y,
                "OP_INT_AND",
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_OR",
                ["int"],
                "int",
                lambda x, y: x | y,
                "OP_INT_OR",
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_XOR",
                ["int"],
                "int",
                lambda x, y: x ^ y,
                "OP_INT_XOR",
            ),
            VlConstOperation(
                "UNARY",
                "BITWISE_NOT",
                ["int"],
                "int",
                lambda x: (1 << 64) - 1 - x,
                "OP_INT_NOT",
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_LEFT_SHIFT",
                ["int"],
                "int",
                lambda x, y: x << y,
                "OP_INT_LEFT_SHIFT",
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_RIGHT_SHIFT",
                ["int"],
                "int",
                lambda x, y: x >> y,
                "OP_INT_RIGHT_SHIFT",
            ),
        ]

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlBool(VlTypeABC):

    def __init__(self, underlying: bool) -> None:
        if not isinstance(underlying, bool):
            raise ValueError(
                f"Underlying value of VlBool must be a Python bool, not '{type(underlying)}'"
            )
        self.underlying: bool = underlying

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "bool", "VAL", (4, 8)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        return [
            VlConstOperation(
                "BINARY",
                "EQUAL_TO",
                ["bool"],
                "bool",
                lambda x, y: x == y,
                "OP_INT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["bool"],
                "bool",
                lambda x, y: x != y,
                "OP_INT_NOT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "BOOLEAN_AND",
                ["bool"],
                "bool",
                lambda x, y: x and y,
                "OP_BOOLEAN_AND",
            ),
            VlConstOperation(
                "BINARY",
                "BOOLEAN_OR",
                ["bool"],
                "bool",
                lambda x, y: x or y,
                "OP_BOOLEAN_OR",
            ),
            VlConstOperation(
                "UNARY",
                "BOOLEAN_NOT",
                [],
                "bool",
                lambda x: not x,
                "OP_BOOLEAN_NOT",
            ),
        ]

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlReal(VlTypeABC):

    def __init__(self, underlying: float) -> None:
        if not isinstance(underlying, float):
            raise ValueError(
                f"Underlying value of VlReal must be a Python float, not '{type(underlying)}'"
            )
        self.underlying: float = underlying

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "real", "VAL", (4, 8)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        return [
            VlConstOperation(
                "BINARY",
                "EQUAL_TO",
                ["real"],
                "bool",
                lambda x, y: x == y,
                "OP_REAL_EQUAL",
                extra_opcode_hr="OP_REAL_JMP_IF_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["real"],
                "bool",
                lambda x, y: x != y,
                "OP_REAL_NOT_EQUAL",
                extra_opcode_hr="OP_REAL_JMP_IF_NOT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN",
                ["real"],
                "bool",
                lambda x, y: x > y,
                "OP_REAL_GREATER",
                extra_opcode_hr="OP_REAL_JMP_IF_GREATER",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN_OR_EQUAL",
                ["real"],
                "bool",
                lambda x, y: x >= y,
                "OP_REAL_GREATER_OR_EQUAL",
                extra_opcode_hr="OP_REAL_JMP_IF_GREATER_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN",
                ["real"],
                "bool",
                lambda x, y: x < y,
                "OP_REAL_LESS",
                extra_opcode_hr="OP_REAL_JMP_IF_LESS",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN_OR_EQUAL",
                ["real"],
                "bool",
                lambda x, y: x <= y,
                "OP_REAL_LESS_OR_EQUAL",
                extra_opcode_hr="OP_REAL_JMP_IF_LESS_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "PLUS",
                ["real"],
                "real",
                lambda x, y: x + y,
                "OP_REAL_ADD",
            ),
            VlConstOperation(
                "BINARY",
                "MINUS",
                ["real"],
                "real",
                lambda x, y: x - y,
                "OP_REAL_SUB",
            ),
            VlConstOperation(
                "BINARY",
                "TIMES",
                ["real"],
                "real",
                lambda x, y: x * y,
                "OP_REAL_MUL",
            ),
            VlConstOperation(
                "BINARY",
                "DIVIDE",
                ["real"],
                "real",
                lambda x, y: x // y,
                "OP_REAL_DIV",
            ),
            VlConstOperation(
                "BINARY",
                "MODULUS",
                ["real"],
                "real",
                lambda x, y: x % y,
                "OP_REAL_MOD",
            ),
            VlConstOperation(
                "BINARY",
                "EXPONENTIATION",
                ["real"],
                "real",
                lambda x, y: x**y,
                "OP_REAL_EXP",
            ),
            VlConstOperation(
                "UNARY",
                "UNARY_MINUS",
                [],
                "real",
                lambda x: -x,
                "OP_REAL_NEG",
            ),
        ]

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass
