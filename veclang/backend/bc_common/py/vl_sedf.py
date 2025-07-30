import typing
from veclang.utils.cedf.cedf import SEDF


VL_SEDF_ID: int = 0x0001_0000


class VlFunction(typing.TypedDict):
    name: str
    stack_size: int
    instruction_offset: int
    arg_types: list[int]
    return_type: int


class VlHeader(typing.TypedDict):
    magic: str  # Should always be "VECL"
    version: int
    flags: dict
    functions: list[VlFunction]


class VlProgram(typing.TypedDict):
    header: VlHeader
    constants: bytes
    instructions: bytes


class VlSEDF(SEDF[VlProgram]):

    @staticmethod
    def check_header(header: dict) -> None:
        """
        The header for a Veclang SEDF should be a VlHeader type.
        """

    @classmethod
    def serialise(cls, instance: VlProgram) -> tuple[dict, bytes]:
        header: dict = instance["header"]
        header["constants_len"] = len(instance["constants"])
        header["instructions_len"] = len(instance["instructions"])
        payload: bytes = instance["constants"] + instance["instructions"]
        return header, payload

    @classmethod
    def deserialise(cls, header: dict, payload: bytes) -> VlProgram:
        constants_len = header.pop("constants_len")
        instructions_len = header.pop("instructions_len")
        if constants_len + instructions_len != len(payload):
            raise Exception(
                f"Expected payload with lengths {constants_len} and {instructions_len}, got {len(payload)}"
            )
        constants: bytes = payload[:constants_len]
        instructions: bytes = payload[constants_len:]
        return {"header": header, "constants": constants, "instructions": instructions}

    @staticmethod
    def get_sedf_id() -> int:
        return VL_SEDF_ID
