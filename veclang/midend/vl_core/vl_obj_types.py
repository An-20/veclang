from veclang.midend.vl_core.vl_type import (
    VlTypeABC,
    VlTypeStr,
    VlTypeType,
    VlOperation,
    VlConstOperation,
    VlMethod,
    VlCast,
)


class VlComplex(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "complex", "OBJ", (8, 16)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        return [
            VlConstOperation(
                "BINARY",
                "EQUAL_TO",
                ["complex"],
                "OP_COMPLEX_EQUAL",
                "bool",
                lambda x, y: x == y,
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["complex"],
                "OP_COMPLEX_NOT_EQUAL",
                "bool",
                lambda x, y: x != y,
            ),
            VlConstOperation(
                "BINARY",
                "PLUS",
                ["complex"],
                "OP_COMPLEX_ADD",
                "complex",
                lambda x, y: x + y,
            ),
            VlConstOperation(
                "BINARY",
                "MINUS",
                ["complex"],
                "OP_COMPLEX_SUB",
                "complex",
                lambda x, y: x - y,
            ),
            VlConstOperation(
                "BINARY",
                "TIMES",
                ["complex"],
                "OP_COMPLEX_MUL",
                "complex",
                lambda x, y: x * y,
            ),
            VlConstOperation(
                "BINARY",
                "DIVIDE",
                ["complex"],
                "OP_COMPLEX_DIV",
                "complex",
                lambda x, y: x / y,
            ),
            VlConstOperation(
                "BINARY",
                "EXPONENTIATION",
                ["complex"],
                "OP_COMPLEX_EXP",
                "complex",
                lambda x, y: x**y,
            ),
            VlConstOperation(
                "UNARY",
                "UNARY_MINUS",
                ["complex"],
                "OP_COMPLEX_NEG",
                "complex",
                lambda x: -x,
            ),
        ]

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlMat2(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "mat2", "OBJ", (8, 16)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass
