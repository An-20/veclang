from veclang.backend.bc_common.py import VlProgram
from veclang.backend.bc_compiler.vl_instruction import OpcodeMap


def disassemble(bytecode: list[bytes]) -> str:
    out_str = ""
    for idx, operation in enumerate(bytecode):
        if len(operation) != 4:
            raise ValueError
        opcode = operation[0]
        if opcode not in OpcodeMap:
            out_str += "UNKNOWN_OPCODE\n"

        info = OpcodeMap[opcode]
        if info.num_operands == 0:
            out_str += f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(30)}\n"
        elif info.num_operands == 1:
            operand_1 = int.from_bytes(operation[2:])
            out_str += f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(30)} 0x{operand_1:04X}\n"
        else:
            operand_1 = operation[1]
            operand_2 = int.from_bytes(operation[2:])
            out_str += f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(30)} 0x{operand_1:02X}   0x{operand_2:04X}\n"
    return out_str


def disassemble_vl_program(vl_program: VlProgram) -> str:
    instructions = vl_program["instructions"]
    return disassemble(
        [instructions[i : i + 4] for i in range(0, len(instructions), 4)]
    )
