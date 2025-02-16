import struct
import dataclasses


INSTRUCTION_LENGTH: int = 4


@dataclasses.dataclass
class Chunk:
    instructions: list[bytes]
    constants: bytearray

    def serialize(self):
        """
        A chunk can be serialized to a binary format with:
        - An int (4 bytes) representing the length of instructions, in bytes
        - An int (4 bytes) representing the length of constants, in bytes
        - Bytes containing instructions
        - Bytes containing constants
        """
        instructions_bytes_length = len(self.instructions) * INSTRUCTION_LENGTH
        constants_bytes_length = len(self.constants)
        header_bytes = struct.pack(
            "ii", instructions_bytes_length, constants_bytes_length
        )
        serialized = header_bytes + b"".join(self.instructions) + self.constants
        return serialized

    @staticmethod
    def deserialize(serialized):
        header_bytes = serialized[:8]
        instructions_bytes_length, constants_bytes_length = struct.unpack(
            "ii", header_bytes
        )
        if instructions_bytes_length + constants_bytes_length + 8 != len(serialized):
            raise Exception
        instruction_bytes = serialized[8 : 8 + instructions_bytes_length]
        instruction_list = [
            instruction_bytes[i : i + 4] for i in range(0, len(instruction_bytes), 4)
        ]
        constants_bytes = serialized[8 + instructions_bytes_length :]
        return Chunk(instruction_list, constants_bytes)
