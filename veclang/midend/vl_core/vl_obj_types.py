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
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlMat2(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "mat2", "OBJ", (16, 32)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlMat3(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "mat3", "OBJ", (36, 72)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlMat4(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "mat4", "OBJ", (64, 128)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlVec2(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "vec2", "OBJ", (8, 16)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlVec3(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "vec3", "OBJ", (12, 24)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass


class VlVec4(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "vec4", "OBJ", (16, 32)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass

    @staticmethod
    def get_casts() -> list[VlCast]:
        pass
