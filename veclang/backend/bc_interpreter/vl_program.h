#ifndef VL_PROGRAM_H
#define VL_PROGRAM_H

#include <vector>
#include <cstdint>

namespace vl_program
{

    enum Opcode : uint8_t
    {
        OP_CONSTANT_VAL_DIRECT = 0x00,
        OP_CONSTANT_OBJ_DIRECT = 0x01,
        OP_CONSTANT_VAL_TABLE = 0x02,
        OP_CONSTANT_OBJ_TABLE = 0x03,
        OP_POP_VAL = 0x04,
        OP_POP_OBJ = 0x05,
        OP_CALL_BUILTIN = 0x06,
        OP_CALL = 0x07,
        OP_RETURN = 0x08,
        OP_GET_LOCAL_VAL = 0x10,
        OP_SET_LOCAL_VAL = 0x11,
        OP_GET_GLOBAL_VAL = 0x12,
        OP_SET_GLOBAL_VAL = 0x13,
        OP_GET_LOCAL_OBJ = 0x14,
        OP_SET_LOCAL_OBJ = 0x15,
        OP_GET_GLOBAL_OBJ = 0x16,
        OP_SET_GLOBAL_OBJ = 0x17,
        OP_JMP = 0x20,
        OP_JMP_IF_TRUE = 0x21,
        OP_JMP_IF_FALSE = 0x22,
        OP_INT_EQUAL = 0x80,
        OP_INT_NOT_EQUAL = 0x81,
        OP_INT_GREATER = 0x82,
        OP_INT_GREATER_OR_EQUAL = 0x83,
        OP_INT_LESS = 0x84,
        OP_INT_LESS_OR_EQUAL = 0x85,
        OP_INT_ADD = 0x86,
        OP_INT_SUB = 0x87,
        OP_INT_MUL = 0x88,
        OP_INT_DIV = 0x89,
        OP_INT_MOD = 0x8A,
        OP_INT_EXP = 0x8B,
        OP_INT_NEG = 0x8C,
        OP_INT_AND = 0x8D,
        OP_INT_OR = 0x8E,
        OP_INT_XOR = 0x8F,
        OP_INT_NOT = 0x90,
        OP_INT_LEFT_SHIFT = 0x91,
        OP_INT_RIGHT_SHIFT = 0x92,
        OP_INT_JMP_IF_EQUAL = 0x93,
        OP_INT_JMP_IF_NOT_EQUAL = 0x94,
        OP_INT_JMP_IF_GREATER = 0x95,
        OP_INT_JMP_IF_GREATER_OR_EQUAL = 0x96,
        OP_INT_JMP_IF_LESS = 0x97,
        OP_INT_JMP_IF_LESS_OR_EQUAL = 0x98,
        OP_BOOLEAN_AND = 0x9C,
        OP_BOOLEAN_OR = 0x9D,
        OP_BOOLEAN_NOT = 0x9E,
        OP_REAL_EQUAL = 0xA0,
        OP_REAL_NOT_EQUAL = 0xA1,
        OP_REAL_GREATER = 0xA2,
        OP_REAL_GREATER_OR_EQUAL = 0xA3,
        OP_REAL_LESS = 0xA4,
        OP_REAL_LESS_OR_EQUAL = 0xA5,
        OP_REAL_ADD = 0xA6,
        OP_REAL_SUB = 0xA7,
        OP_REAL_MUL = 0xA8,
        OP_REAL_DIV = 0xA9,
        OP_REAL_MOD = 0xAA,
        OP_REAL_EXP = 0xAB,
        OP_REAL_NEG = 0xAC,
        OP_COMPLEX_EQUAL = 0xB0,
        OP_COMPLEX_NOT_EQUAL = 0xB1,
        OP_COMPLEX_ADD = 0xB2,
        OP_COMPLEX_SUB = 0xB3,
        OP_COMPLEX_MUL = 0xB4,
        OP_COMPLEX_DIV = 0xB5,
        OP_COMPLEX_EXP = 0xB6,
        OP_COMPLEX_NEG = 0xB7,
        OP_REAL_JMP_IF_EQUAL = 0xBA,
        OP_REAL_JMP_IF_NOT_EQUAL = 0xBB,
        OP_REAL_JMP_IF_GREATER = 0xBC,
        OP_REAL_JMP_IF_GREATER_OR_EQUAL = 0xBD,
        OP_REAL_JMP_IF_LESS = 0xBE,
        OP_REAL_JMP_IF_LESS_OR_EQUAL = 0xBF,
        OP_VECTOR_ADD = 0xC0,
        OP_VECTOR_SUB = 0xC1,
        OP_VECTOR_MUL = 0xC2,
        OP_VECTOR_DIV = 0xC3,
        OP_VECTOR_NEG = 0xC4,
        OP_VECTOR_SCL = 0xC5,
        OP_VECTOR_DOT = 0xC6,
        OP_VECTOR_CRS = 0xC7,
        OP_MATRIX_ADD = 0xC8,
        OP_MATRIX_SUB = 0xC9,
        OP_MATRIX_MUL = 0xCA,
        OP_MATRIX_NEG = 0xCB,
        OP_MATRIX_SCL = 0xCC
    };

    enum type_code : uint8_t
    {
        VL_INT = 0x00,
        VL_BOOL = 0x01,
        VL_REAL = 0x02,
        VL_COMPLEX = 0x03,
        VL_VEC2 = 0x04,
        VL_VEC3 = 0x05,
        VL_VEC4 = 0x06,
        VL_MAT2 = 0x07,
        VL_MAT3 = 0x08,
        VL_MAT4 = 0x09
    };

    size_t get_type_canonical_size(type_code type);

}

#endif // VL_PROGRAM_H
