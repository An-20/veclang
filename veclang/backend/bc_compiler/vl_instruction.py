import typing


Opcode = typing.Literal[0x00, 0x01, 0x02, 0x03, 0x10, 0x11, 0x12, 0x13]


class Instruction:

    def __init__(
        self, opcode: int, opcode_hr: str, num_operands: typing.Literal[0, 1, 2]
    ) -> None:
        self.opcode: int = opcode
        self.opcode_hr: str = opcode_hr
        self.num_operands: typing.Literal[0, 1, 2] = num_operands

    def additional_checks(self, operands: tuple[bytes]):
        pass

    def pack(self, operands: tuple[bytes]) -> bytes:
        self.additional_checks(operands)
        if len(operands) != self.num_operands:
            raise ValueError(
                f"Instruction '{self.opcode_hr}' takes {self.num_operands} operands."
            )
        if self.num_operands == 0:
            return bytes([self.opcode, 0, 0, 0])

        elif self.num_operands == 1:
            if not isinstance(operands[0], bytes) or len(operands[0]) != 2:
                raise ValueError(
                    f"Instruction '{self.opcode_hr}' takes 1 2-byte operand."
                )
            return bytes([self.opcode] + [0] + list(operands[0]))

        elif self.num_operands == 2:
            if not isinstance(operands[0], bytes) or len(operands[0]) != 1:
                raise ValueError(
                    f"Instruction '{self.opcode_hr}' first operand is 1 byte."
                )
            if not isinstance(operands[1], bytes) or len(operands[1]) != 2:
                raise ValueError(
                    f"Instruction '{self.opcode_hr}' second operand is 2 bytes."
                )
            return bytes([self.opcode] + list(operands[0]) + list(operands[1]))
        else:
            raise ValueError("Unsupported number of operands")


class MatVecInstruction(Instruction):

    def additional_checks(self, operands: list[bytes]):
        if int.from_bytes(operands[0]) not in [2, 3, 4]:
            raise ValueError(
                f"First operand of instruction '{self.opcode_hr}' must be 2, 3, or 4"
            )


OpcodeMap: dict[int, Instruction] = {
    0x00: Instruction(0x00, "OP_CONSTANT_VAL_DIRECT", 1),
    0x01: Instruction(0x01, "OP_CONSTANT_OBJ_DIRECT", 2),
    0x02: Instruction(0x02, "OP_CONSTANT_VAL_TABLE", 1),
    0x03: Instruction(0x03, "OP_CONSTANT_OBJ_TABLE", 2),
    0x04: Instruction(0x04, "OP_POP_VAL", 0),
    0x05: Instruction(0x05, "OP_POP_OBJ", 0),
    0x06: Instruction(0x06, "OP_CALL_BUILTIN", 1),
    0x07: Instruction(0x07, "OP_CALL", 1),
    0x08: Instruction(0x08, "OP_RETURN", 0),
    0x10: Instruction(0x10, "OP_GET_LOCAL_VAL", 1),
    0x11: Instruction(0x11, "OP_SET_LOCAL_VAL", 1),
    0x12: Instruction(0x12, "OP_GET_GLOBAL_VAL", 1),
    0x13: Instruction(0x13, "OP_SET_GLOBAL_VAL", 1),
    0x14: Instruction(0x14, "OP_GET_LOCAL_OBJ", 2),
    0x15: Instruction(0x15, "OP_SET_LOCAL_OBJ", 2),
    0x16: Instruction(0x16, "OP_GET_GLOBAL_OBJ", 2),
    0x17: Instruction(0x17, "OP_SET_GLOBAL_OBJ", 2),
    0x20: Instruction(0x20, "OP_JMP", 1),
    0x21: Instruction(0x21, "OP_JMP_IF_TRUE", 1),
    0x22: Instruction(0x22, "OP_JMP_IF_FALSE", 1),
    # ========================================
    # 0x80 - 0xDF - OPERATIONS
    # ========================================
    # 0x80 - 0x9F - INTEGER OPERATIONS AND BOOLEAN OPERATIONS
    0x80: Instruction(0x80, "OP_INT_EQUAL", 0),
    0x81: Instruction(0x81, "OP_INT_NOT_EQUAL", 0),
    0x82: Instruction(0x82, "OP_INT_GREATER", 0),
    0x83: Instruction(0x83, "OP_INT_GREATER_OR_EQUAL", 0),
    0x84: Instruction(0x84, "OP_INT_LESS", 0),
    0x85: Instruction(0x85, "OP_INT_LESS_OR_EQUAL", 0),
    0x86: Instruction(0x86, "OP_INT_ADD", 0),
    0x87: Instruction(0x87, "OP_INT_SUB", 0),
    0x88: Instruction(0x88, "OP_INT_MUL", 0),
    0x89: Instruction(0x89, "OP_INT_DIV", 0),
    0x8A: Instruction(0x8A, "OP_INT_MOD", 0),
    0x8B: Instruction(0x8B, "OP_INT_EXP", 0),
    0x8C: Instruction(0x8C, "OP_INT_NEG", 0),
    0x8D: Instruction(0x8D, "OP_INT_AND", 0),
    0x8E: Instruction(0x8E, "OP_INT_OR", 0),
    0x8F: Instruction(0x8F, "OP_INT_XOR", 0),
    0x90: Instruction(0x90, "OP_INT_NOT", 0),
    0x91: Instruction(0x91, "OP_INT_LEFT_SHIFT", 0),
    0x92: Instruction(0x92, "OP_INT_RIGHT_SHIFT", 0),
    0x9C: Instruction(0x9C, "OP_BOOLEAN_AND", 0),
    0x9D: Instruction(0x9D, "OP_BOOLEAN_OR", 0),
    0x9E: Instruction(0x9E, "OP_BOOLEAN_NOT", 0),
    # 0xA0 - 0xAF - REAL OPERATIONS
    0xA0: Instruction(0xA0, "OP_REAL_EQUAL", 0),
    0xA1: Instruction(0xA1, "OP_REAL_NOT_EQUAL", 0),
    0xA2: Instruction(0xA2, "OP_REAL_GREATER", 0),
    0xA3: Instruction(0xA3, "OP_REAL_GREATER_OR_EQUAL", 0),
    0xA4: Instruction(0xA4, "OP_REAL_LESS", 0),
    0xA5: Instruction(0xA5, "OP_REAL_LESS_OR_EQUAL", 0),
    0xA6: Instruction(0xA6, "OP_REAL_ADD", 0),
    0xA7: Instruction(0xA7, "OP_REAL_SUB", 0),
    0xA8: Instruction(0xA8, "OP_REAL_MUL", 0),
    0xA9: Instruction(0xA9, "OP_REAL_DIV", 0),
    0xAA: Instruction(0xAA, "OP_REAL_MOD", 0),
    0xAB: Instruction(0xAB, "OP_REAL_EXP", 0),
    0xAC: Instruction(0xAC, "OP_REAL_NEG", 0),
    # 0xB0 - 0xBF - COMPLEX OPERATIONS AND EXTENDED REAL COMPARISONS
    0xB0: Instruction(0xB0, "OP_COMPLEX_EQUAL", 0),
    0xB1: Instruction(0xB1, "OP_COMPLEX_NOT_EQUAL", 0),
    0xB2: Instruction(0xB2, "OP_COMPLEX_ADD", 0),
    0xB3: Instruction(0xB3, "OP_COMPLEX_SUB", 0),
    0xB4: Instruction(0xB4, "OP_COMPLEX_MUL", 0),
    0xB5: Instruction(0xB5, "OP_COMPLEX_DIV", 0),
    0xB6: Instruction(0xB6, "OP_COMPLEX_EXP", 0),
    0xB7: Instruction(0xB7, "OP_COMPLEX_NEG", 0),
    # 0xC0 - 0xCF - VECTOR AND MATRIX OPERATIONS
    0xC0: MatVecInstruction(0xC0, "OP_VECTOR_ADD", 1),
    0xC1: MatVecInstruction(0xC1, "OP_VECTOR_SUB", 1),
    0xC2: MatVecInstruction(0xC2, "OP_VECTOR_MUL", 1),
    0xC3: MatVecInstruction(0xC3, "OP_VECTOR_DIV", 1),
    0xC4: MatVecInstruction(0xC4, "OP_VECTOR_NEG", 1),
    0xC5: MatVecInstruction(0xC5, "OP_VECTOR_SCL", 1),
    0xC6: MatVecInstruction(0xC6, "OP_VECTOR_DOT", 1),
    0xC7: MatVecInstruction(0xC7, "OP_VECTOR_CRS", 1),
    0xC8: MatVecInstruction(0xC8, "OP_MATRIX_ADD", 1),
    0xC9: MatVecInstruction(0xC9, "OP_MATRIX_SUB", 1),
    0xCA: MatVecInstruction(0xCA, "OP_MATRIX_MUL", 1),
    0xCB: MatVecInstruction(0xCB, "OP_MATRIX_NEG", 1),
    0xCC: MatVecInstruction(0xCC, "OP_MATRIX_SCL", 1),
    # ========================================
    # 0xD0 - 0xFF - RESERVED
    # ========================================
}
OpcodeHRMap: dict[str, Instruction] = {v.opcode_hr: v for k, v in OpcodeMap.items()}
