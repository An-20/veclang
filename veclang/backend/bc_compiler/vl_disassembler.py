from veclang.backend.bc_common.py import VlProgram
from veclang.backend.bc_compiler.vl_instruction import OPCODE_MAP


def disassemble(bytecode: list[bytes]) -> str:
    out_str = ""
    max_opcode_len = max(
        len(OPCODE_MAP[x[0]].opcode_hr) if x[0] in OPCODE_MAP else 10 for x in bytecode
    )
    pad_len = max_opcode_len + 4

    for idx, operation in enumerate(bytecode):
        if len(operation) != 4:
            raise ValueError
        opcode = operation[0]
        if opcode not in OPCODE_MAP:
            out_str += "UNKNOWN_OPCODE\n"

        info = OPCODE_MAP[opcode]
        if info.num_operands == 0:
            out_str += (
                f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(pad_len)}\n"
            )
        elif info.num_operands == 1:
            operand_1 = int.from_bytes(operation[2:], byteorder="little")
            out_str += f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(pad_len)} 0x{operand_1:04X}\n"
        else:
            operand_1 = operation[1]
            operand_2 = int.from_bytes(operation[2:], byteorder="little")
            out_str += f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(pad_len)} 0x{operand_1:02X}   0x{operand_2:04X}\n"
    return out_str


def default_format(data: bytes) -> str:
    """Default formatter taken from CEDF"""
    lines = []
    width = 16
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:08X}  {hex_part:<48}  {ascii_part}")
    return "\n".join(lines)


def disassemble_vl_program(
    vl_program: VlProgram, include_constants: bool = True
) -> str:
    constants = vl_program["constants"]
    instructions = vl_program["instructions"]

    out_str = ""
    if include_constants:
        out_str = f"Constants:\n{default_format(constants)}\n\n"

    instructions_disassembled = disassemble(
        [instructions[i : i + 4] for i in range(0, len(instructions), 4)]
    )
    out_str += f"Instructions:\n{instructions_disassembled}"

    return out_str
