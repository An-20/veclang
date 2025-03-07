from veclang.midend.hir.vl_types.vl_type import (
    VlTypeABC,
    VlTypeStr,
    VlTypeType,
    VlOperation,
    VlMethod,
)


class VlInt(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "int", "VAL", (4, 8)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass


class VlBool(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "bool", "VAL", (4, 8)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass


class VlReal(VlTypeABC):

    @staticmethod
    def get_info() -> tuple[VlTypeStr, VlTypeType, tuple[int, int]]:
        return "real", "VAL", (4, 8)

    @staticmethod
    def get_operations() -> list[VlOperation]:
        pass

    @staticmethod
    def get_methods() -> list[VlMethod]:
        pass
