from veclang.backend.bc_compiler.vl_instruction import OpcodeMap


def disassemble(bytecode: list[bytes]):
    for idx, operation in enumerate(bytecode):
        if len(operation) != 4:
            raise ValueError
        opcode = operation[0]
        if opcode not in OpcodeMap:
            print("UNKNOWN_OPCODE")

        info = OpcodeMap[opcode]
        if info.num_operands == 0:
            print(f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(30)}")
        elif info.num_operands == 1:
            operand_1 = int.from_bytes(operation[2:])
            print(
                f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(30)} 0x{operand_1:04X}"
            )
        else:
            operand_1 = operation[1]
            operand_2 = int.from_bytes(operation[2:])
            print(
                f"{idx:04} {idx:04X} 0x{opcode:02X} {info.opcode_hr.ljust(30)} 0x{operand_1:02X}   0x{operand_2:04X}"
            )
