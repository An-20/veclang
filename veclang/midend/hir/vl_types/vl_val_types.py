from veclang.midend.hir.vl_types.vl_type import (
    VlTypeABC,
    VlTypeStr,
    VlTypeType,
    VlOperation,
    VlConstOperation,
    VlMethod,
    VlCast,
)


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
                "OP_INT_EQUAL",
                "bool",
                lambda x, y: x == y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["int"],
                "OP_INT_NOT_EQUAL",
                "bool",
                lambda x, y: x != y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_NOT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN",
                ["int"],
                "OP_INT_GREATER",
                "bool",
                lambda x, y: x > y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_GREATER",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN_OR_EQUAL",
                ["int"],
                "OP_INT_GREATER_OR_EQUAL",
                "bool",
                lambda x, y: x >= y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_GREATER_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN",
                ["int"],
                "OP_INT_LESS",
                "bool",
                lambda x, y: x < y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_LESS",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN_OR_EQUAL",
                ["int"],
                "OP_INT_LESS_OR_EQUAL",
                "bool",
                lambda x, y: x <= y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_LESS_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY", "PLUS", ["int"], "OP_INT_ADD", "int", lambda x, y: x + y
            ),
            VlConstOperation(
                "BINARY",
                "MINUS",
                ["int"],
                "OP_INT_SUB",
                "int",
                lambda x, y: x - y,
            ),
            VlConstOperation(
                "BINARY",
                "TIMES",
                ["int"],
                "OP_INT_MUL",
                "int",
                lambda x, y: x * y,
            ),
            VlConstOperation(
                "BINARY",
                "DIVIDE",
                ["int"],
                "OP_INT_DIV",
                "int",
                lambda x, y: x // y,
            ),
            VlConstOperation(
                "BINARY",
                "MODULUS",
                ["int"],
                "OP_INT_MOD",
                "int",
                lambda x, y: x % y,
            ),
            VlConstOperation(
                "BINARY",
                "EXPONENTIATION",
                ["int"],
                "OP_INT_EXP",
                "int",
                lambda x, y: x**y,
            ),
            VlConstOperation(
                "UNARY",
                "UNARY_MINUS",
                [],
                "OP_INT_NEG",
                "int",
                lambda x: -x,
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_AND",
                ["int"],
                "OP_INT_AND",
                "int",
                lambda x, y: x & y,
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_OR",
                ["int"],
                "OP_INT_OR",
                "int",
                lambda x, y: x | y,
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_XOR",
                ["int"],
                "OP_INT_XOR",
                "int",
                lambda x, y: x ^ y,
            ),
            VlConstOperation(
                "UNARY",
                "BITWISE_NOT",
                ["int"],
                "OP_INT_NOT",
                "int",
                lambda x: (1 << 64) - 1 - x,
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_LEFT_SHIFT",
                ["int"],
                "OP_INT_LEFT_SHIFT",
                "int",
                lambda x, y: x << y,
            ),
            VlConstOperation(
                "BINARY",
                "BITWISE_RIGHT_SHIFT",
                ["int"],
                "OP_INT_RIGHT_SHIFT",
                "int",
                lambda x, y: x >> y,
            ),
        ]

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


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
                "OP_INT_EQUAL",
                "bool",
                lambda x, y: x == y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["bool"],
                "OP_INT_NOT_EQUAL",
                "bool",
                lambda x, y: x != y,
                fast_jmp_opcode_hr="OP_INT_JMP_IF_NOT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "BOOLEAN_AND",
                ["bool"],
                "OP_BOOLEAN_AND",
                "bool",
                lambda x, y: x and y,
            ),
            VlConstOperation(
                "BINARY",
                "BOOLEAN_OR",
                ["bool"],
                "OP_BOOLEAN_OR",
                "bool",
                lambda x, y: x or y,
            ),
            VlConstOperation(
                "UNARY", "BOOLEAN_NOT", [], "OP_BOOLEAN_NOT", "bool", lambda x: not x
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
                "OP_REAL_EQUAL",
                "bool",
                lambda x, y: x == y,
                fast_jmp_opcode_hr="OP_REAL_JMP_IF_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["real"],
                "OP_REAL_NOT_EQUAL",
                "bool",
                lambda x, y: x != y,
                fast_jmp_opcode_hr="OP_REAL_JMP_IF_NOT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN",
                ["real"],
                "OP_REAL_GREATER",
                "bool",
                lambda x, y: x > y,
                fast_jmp_opcode_hr="OP_REAL_JMP_IF_GREATER",
            ),
            VlConstOperation(
                "BINARY",
                "GREATER_THAN_OR_EQUAL",
                ["real"],
                "OP_REAL_GREATER_OR_EQUAL",
                "bool",
                lambda x, y: x >= y,
                fast_jmp_opcode_hr="OP_REAL_JMP_IF_GREATER_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN",
                ["real"],
                "OP_REAL_LESS",
                "bool",
                lambda x, y: x < y,
                fast_jmp_opcode_hr="OP_REAL_JMP_IF_LESS",
            ),
            VlConstOperation(
                "BINARY",
                "LESS_THAN_OR_EQUAL",
                ["real"],
                "OP_REAL_LESS_OR_EQUAL",
                "bool",
                lambda x, y: x <= y,
                fast_jmp_opcode_hr="OP_REAL_JMP_IF_LESS_OR_EQUAL",
            ),
            VlConstOperation(
                "BINARY", "PLUS", ["real"], "OP_REAL_ADD", "real", lambda x, y: x + y
            ),
            VlConstOperation(
                "BINARY",
                "MINUS",
                ["real"],
                "OP_REAL_SUB",
                "real",
                lambda x, y: x - y,
            ),
            VlConstOperation(
                "BINARY",
                "TIMES",
                ["real"],
                "OP_REAL_MUL",
                "real",
                lambda x, y: x * y,
            ),
            VlConstOperation(
                "BINARY",
                "DIVIDE",
                ["real"],
                "OP_REAL_DIV",
                "real",
                lambda x, y: x // y,
            ),
            VlConstOperation(
                "BINARY",
                "MODULUS",
                ["real"],
                "OP_REAL_MOD",
                "real",
                lambda x, y: x % y,
            ),
            VlConstOperation(
                "BINARY",
                "EXPONENTIATION",
                ["real"],
                "OP_REAL_EXP",
                "real",
                lambda x, y: x**y,
            ),
            VlConstOperation(
                "UNARY",
                "UNARY_MINUS",
                [],
                "OP_REAL_NEG",
                "real",
                lambda x: -x,
            ),
        ]

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass
