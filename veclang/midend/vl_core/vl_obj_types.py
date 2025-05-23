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

    def __init__(self, underlying: complex) -> None:
        if not isinstance(underlying, complex):
            raise ValueError(
                f"Underlying value of VlComplex must be a Python complex, not '{type(underlying)}'"
            )
        self.underlying: complex = underlying

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
                "bool",
                lambda x, y: x == y,
                "OP_COMPLEX_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["complex"],
                "bool",
                lambda x, y: x != y,
                "OP_COMPLEX_NOT_EQUAL",
            ),
            VlConstOperation(
                "BINARY",
                "PLUS",
                ["complex"],
                "complex",
                lambda x, y: x + y,
                "OP_COMPLEX_ADD",
            ),
            VlConstOperation(
                "BINARY",
                "MINUS",
                ["complex"],
                "complex",
                lambda x, y: x - y,
                "OP_COMPLEX_SUB",
            ),
            VlConstOperation(
                "BINARY",
                "TIMES",
                ["complex"],
                "complex",
                lambda x, y: x * y,
                "OP_COMPLEX_MUL",
            ),
            VlConstOperation(
                "BINARY",
                "DIVIDE",
                ["complex"],
                "complex",
                lambda x, y: x / y,
                "OP_COMPLEX_DIV",
            ),
            VlConstOperation(
                "BINARY",
                "EXPONENTIATION",
                ["complex"],
                "complex",
                lambda x, y: x**y,
                "OP_COMPLEX_EXP",
            ),
            VlConstOperation(
                "UNARY",
                "UNARY_MINUS",
                ["complex"],
                "complex",
                lambda x: -x,
                "OP_COMPLEX_NEG",
            ),
        ]

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_properties() -> list[VlMethod]:
        return [
            VlMethod(
                "re",
                ["complex"],
                "real",
                0x1000,
                "Returns a `real` representing the real component of a `complex`.",
            ),
            VlMethod(
                "im",
                ["complex"],
                "real",
                0x1001,
                "Returns a `real` representing the real component of a `complex`.",
            ),
        ]

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlMat2(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "mat2", "OBJ", (16, 32)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_properties() -> list[VlMethod]:
        return []

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlMat3(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "mat3", "OBJ", (36, 72)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_properties() -> list[VlMethod]:
        return []

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlMat4(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "mat4", "OBJ", (64, 128)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_properties() -> list[VlMethod]:
        return []

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlVec2(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "vec2", "OBJ", (8, 16)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_properties() -> list[VlMethod]:
        return []

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlVec3(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "vec3", "OBJ", (12, 24)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_properties() -> list[VlMethod]:
        return []

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlVec4(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "vec4", "OBJ", (16, 32)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        return []

    @staticmethod
    def get_properties() -> list[VlMethod]:
        return []

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []
