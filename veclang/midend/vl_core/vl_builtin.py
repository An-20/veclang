from veclang.midend.vl_core.vl_type import VlTypeStr
from veclang.midend.vl_core.vl_val_types import VlNull, VlInt, VlReal, VlBool
from veclang.midend.vl_core.vl_obj_types import VlComplex


class VlBuiltinFunction:

    def __init__(
        self,
        name: str,
        arg_types: list[VlTypeStr],
        return_type: VlTypeStr,
        id_code: int,
        help_str: str,
    ) -> None:
        self.name: str = name
        self.arg_types: list[VlTypeStr] = arg_types
        self.return_type: VlTypeStr = return_type
        self.id_code: int = id_code
        self.help_str: str = help_str


VL_ALL_TYPES = [VlNull, VlInt, VlReal, VlBool]
