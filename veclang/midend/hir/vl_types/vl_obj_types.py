from veclang.midend.hir.vl_types.vl_type import (
    VlTypeABC,
    VlTypeStr,
    VlTypeType,
    VlOperation,
    VlMethod,
)


class VlComplex(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "complex", "OBJ", (8, 16)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
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
