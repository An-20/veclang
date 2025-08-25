import struct
import veclang.midend.vl_core.vl_types_val as vl_types_val
from veclang.midend.vl_core.vl_type import (
    VlTypeABC,
    VlTypeStr,
    VlTypeCode,
    VlTypeType,
    VlOperation,
    VlConstexprOperation,
    VlMethod,
    VlCast,
)


def obj_to_bytes_32(values: list[float]) -> bytes:
    return b"".join(struct.pack("<f", x) for x in values)


def obj_to_bytes_64(values: list[float]) -> bytes:
    return b"".join(struct.pack("<d", x) for x in values)


class VlComplex(VlTypeABC):

    def __init__(self, underlying: complex) -> None:
        if not isinstance(underlying, complex):
            raise ValueError(
                f"Underlying value of VlComplex must be a Python complex, not '{type(underlying)}'"
            )
        self.underlying: complex
        super().__init__(underlying)

    def to_bytes_32(self) -> bytes:
        return obj_to_bytes_32([self.underlying.real, self.underlying.imag])

    def to_bytes_64(self) -> bytes:
        return obj_to_bytes_64([self.underlying.real, self.underlying.imag])

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        return "complex", 0x03, "OBJ", (8, 16)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        return [
            VlConstexprOperation(
                "BINARY",
                "EQUAL_TO",
                ["complex"],
                "bool",
                lambda x, y: vl_types_val.VlBool(x == y),
                "OP_COMPLEX_EQUAL",
            ),
            VlConstexprOperation(
                "BINARY",
                "NOT_EQUAL_TO",
                ["complex"],
                "bool",
                lambda x, y: vl_types_val.VlBool(x != y),
                "OP_COMPLEX_NOT_EQUAL",
            ),
            VlConstexprOperation(
                "BINARY",
                "PLUS",
                ["complex"],
                "complex",
                lambda x, y: VlComplex(x + y),
                "OP_COMPLEX_ADD",
            ),
            VlConstexprOperation(
                "BINARY",
                "MINUS",
                ["complex"],
                "complex",
                lambda x, y: VlComplex(x - y),
                "OP_COMPLEX_SUB",
            ),
            VlConstexprOperation(
                "BINARY",
                "TIMES",
                ["complex"],
                "complex",
                lambda x, y: VlComplex(x * y),
                "OP_COMPLEX_MUL",
            ),
            VlConstexprOperation(
                "BINARY",
                "DIVIDE",
                ["complex"],
                "complex",
                lambda x, y: VlComplex(x / y),
                "OP_COMPLEX_DIV",
            ),
            VlConstexprOperation(
                "BINARY",
                "EXPONENTIATION",
                ["complex"],
                "complex",
                lambda x, y: VlComplex(x**y),
                "OP_COMPLEX_EXP",
            ),
            VlConstexprOperation(
                "UNARY",
                "UNARY_MINUS",
                ["complex"],
                "complex",
                lambda x: VlComplex(-x),
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
                0x1200,
                "Returns a `real` representing the real component of a `complex`.",
            ),
            VlMethod(
                "im",
                ["complex"],
                "real",
                0x1201,
                "Returns a `real` representing the real component of a `complex`.",
            ),
        ]

    @staticmethod
    def get_casts() -> list[VlCast]:
        return []


class VlMat2(VlTypeABC):

    def to_bytes_32(self) -> bytes:
        pass  # TODO: FIXME

    def to_bytes_64(self) -> bytes:
        pass  # TODO: FIXME

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        return "mat2", 0x07, "OBJ", (16, 32)

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

    def to_bytes_32(self) -> bytes:
        pass  # TODO: FIXME

    def to_bytes_64(self) -> bytes:
        pass  # TODO: FIXME

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        return "mat3", 0x08, "OBJ", (36, 72)

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

    def to_bytes_32(self) -> bytes:
        pass  # TODO: FIXME

    def to_bytes_64(self) -> bytes:
        pass  # TODO: FIXME

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        return "mat4", 0x09, "OBJ", (64, 128)

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

    def to_bytes_32(self) -> bytes:
        pass  # TODO: FIXME

    def to_bytes_64(self) -> bytes:
        pass  # TODO: FIXME

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        return "vec2", 0x04, "OBJ", (8, 16)

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

    def __init__(self, underlying: list[float]) -> None:
        if (
            not isinstance(underlying, list)
            or not (all(isinstance(x, float) for x in underlying))
            or len(underlying) != 3
        ):
            raise ValueError(
                f"Underlying value of VlVec3 must be a Python list float of length 3, not '{underlying}'"
            )
        self.underlying: list[float]
        super().__init__(underlying)

    def to_bytes_32(self) -> bytes:
        return obj_to_bytes_32(self.underlying)

    def to_bytes_64(self) -> bytes:
        return obj_to_bytes_64(self.underlying)

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        return "vec3", 0x05, "OBJ", (12, 24)

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

    def to_bytes_32(self) -> bytes:
        pass  # TODO: FIXME

    def to_bytes_64(self) -> bytes:
        pass  # TODO: FIXME

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeCode, VlTypeType, tuple[int, int]]:
        return "vec4", 0x06, "OBJ", (16, 32)

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
