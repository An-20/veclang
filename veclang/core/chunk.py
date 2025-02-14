import dataclasses


@dataclasses.dataclass
class Chunk:
    code: bytearray
    constants: bytearray
