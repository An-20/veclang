#ifndef VL_INTERPRETER_H
#define VL_INTERPRETER_H

#include <cstdint>
#include <stack>
#include <sstream>
#include <stdexcept>
#include <iostream>
#include "vl_types_val.h"
#include "vl_types_obj.h"
#include "vl_program.h"

#include "../bc_common/cpp/vl_sedf.h"

namespace vl_builtins
{
    class BuiltinsDelegate;
}

namespace vl_interpreter
{
    struct StackFrame
    {
        uint32_t return_address;
        uint32_t stack_start;
        uint32_t stack_size;
    };

    class Interpreter
    {
    public:
        void interpret(const vl_sedf::VlProgram &program)
        {
            constants = program.constants;
            instructions = program.instructions;
            instruction_pointer = 0;
            call_stack.clear();
            value_stack = std::stack<vl_types::RawValue>();
            object_stack = std::stack<vl_types::RawObject>();

            while (instruction_pointer < instructions.size())
            {
                const uint8_t *instruction = &instructions[instruction_pointer];
                interpret_instruction(instruction);
                instruction_pointer += 4;
            }
        }

    private:
        uint32_t instruction_pointer = 0;
        std::vector<uint8_t> constants;
        std::vector<uint8_t> instructions;

        std::vector<uint8_t> global_stack;
        std::vector<uint8_t> local_stack;
        std::vector<StackFrame> call_stack;

        std::stack<vl_types::RawValue> value_stack;
        std::stack<vl_types::RawObject> object_stack;

        uint32_t get_local_stack_offset()
        {
            if (call_stack.empty())
                return 0;
            return call_stack.back().stack_start;
        }

        void interpret_instruction(const uint8_t *instruction)
        {
            uint8_t opcode = instruction[0];
            switch (opcode)
            {
            case vl_program::OP_CONSTANT_VAL_DIRECT:
                op_constant_val_direct(instruction);
                break;
            case vl_program::OP_CONSTANT_OBJ_DIRECT:
                op_constant_obj_direct(instruction);
                break;
            case vl_program::OP_CONSTANT_VAL_TABLE:
                op_constant_val_table(instruction);
                break;
            case vl_program::OP_CONSTANT_OBJ_TABLE:
                op_constant_obj_table(instruction);
                break;
            case vl_program::OP_POP_VAL:
                op_pop_val(instruction);
                break;
            case vl_program::OP_POP_OBJ:
                op_pop_obj(instruction);
                break;
            case vl_program::OP_CALL:
                op_call(instruction);
                break;
            case vl_program::OP_CALL_BUILTIN:
                op_call_builtin(instruction);
                break;
            case vl_program::OP_RETURN:
                op_return(instruction);
                break;
            case vl_program::OP_GET_LOCAL_VAL:
                op_get_local_val(instruction);
                break;
            case vl_program::OP_SET_LOCAL_VAL:
                op_set_local_val(instruction);
                break;
            case vl_program::OP_GET_GLOBAL_VAL:
                op_get_global_val(instruction);
                break;
            case vl_program::OP_SET_GLOBAL_VAL:
                op_set_global_val(instruction);
                break;
            case vl_program::OP_GET_LOCAL_OBJ:
                op_get_local_obj(instruction);
                break;
            case vl_program::OP_SET_LOCAL_OBJ:
                op_set_local_obj(instruction);
                break;
            case vl_program::OP_GET_GLOBAL_OBJ:
                op_get_global_obj(instruction);
                break;
            case vl_program::OP_SET_GLOBAL_OBJ:
                op_set_global_obj(instruction);
                break;
            case vl_program::OP_JMP:
                op_jmp(instruction);
                break;
            case vl_program::OP_JMP_IF_TRUE:
                op_jmp_if_true(instruction);
                break;
            case vl_program::OP_JMP_IF_FALSE:
                op_jmp_if_false(instruction);
                break;

            default:
                std::cerr << "Unknown opcode: " << static_cast<int>(opcode) << std::endl;
                break;
            }
        }

        void op_constant_val_direct(const uint8_t *instruction);
        void op_constant_obj_direct(const uint8_t *instruction);
        void op_constant_val_table(const uint8_t *instruction);
        void op_constant_obj_table(const uint8_t *instruction);
        void op_pop_val(const uint8_t *instruction);
        void op_pop_obj(const uint8_t *instruction);
        void op_call_builtin(const uint8_t *instruction);
        void op_call(const uint8_t *instruction);
        void op_return(const uint8_t *instruction);
        void op_get_local_val(const uint8_t *instruction);
        void op_set_local_val(const uint8_t *instruction);
        void op_get_global_val(const uint8_t *instruction);
        void op_set_global_val(const uint8_t *instruction);
        void op_get_local_obj(const uint8_t *instruction);
        void op_set_local_obj(const uint8_t *instruction);
        void op_get_global_obj(const uint8_t *instruction);
        void op_set_global_obj(const uint8_t *instruction);
        void op_jmp(const uint8_t *instruction);
        void op_jmp_if_true(const uint8_t *instruction);
        void op_jmp_if_false(const uint8_t *instruction);

        void op_int_equal(const uint8_t *instruction);
        void op_int_not_equal(const uint8_t *instruction);
        void op_int_greater(const uint8_t *instruction);
        void op_int_greater_or_equal(const uint8_t *instruction);
        void op_int_less(const uint8_t *instruction);
        void op_int_less_or_equal(const uint8_t *instruction);
        void op_int_add(const uint8_t *instruction);
        void op_int_sub(const uint8_t *instruction);
        void op_int_mul(const uint8_t *instruction);
        void op_int_div(const uint8_t *instruction);
        void op_int_mod(const uint8_t *instruction);
        void op_int_pow(const uint8_t *instruction);
        void op_int_neg(const uint8_t *instruction);
        void op_int_and(const uint8_t *instruction);
        void op_int_or(const uint8_t *instruction);
        void op_int_xor(const uint8_t *instruction);
        void op_int_not(const uint8_t *instruction);
        void op_int_left_shift(const uint8_t *instruction);
        void op_int_right_shift(const uint8_t *instruction);
        void op_boolean_and(const uint8_t *instruction);
        void op_boolean_or(const uint8_t *instruction);
        void op_boolean_not(const uint8_t *instruction);
        void op_real_equal(const uint8_t *instruction);
        void op_real_not_equal(const uint8_t *instruction);
        void op_real_greater(const uint8_t *instruction);
        void op_real_greater_or_equal(const uint8_t *instruction);
        void op_real_less(const uint8_t *instruction);
        void op_real_less_or_equal(const uint8_t *instruction);
        void op_real_add(const uint8_t *instruction);
        void op_real_sub(const uint8_t *instruction);
        void op_real_mul(const uint8_t *instruction);
        void op_real_div(const uint8_t *instruction);
        void op_real_mod(const uint8_t *instruction);
        void op_real_pow(const uint8_t *instruction);
        void op_real_neg(const uint8_t *instruction);
        void op_complex_equal(const uint8_t *instruction);
        void op_complex_not_equal(const uint8_t *instruction);
        void op_complex_add(const uint8_t *instruction);
        void op_complex_sub(const uint8_t *instruction);
        void op_complex_mul(const uint8_t *instruction);
        void op_complex_div(const uint8_t *instruction);
        void op_complex_pow(const uint8_t *instruction);
        void op_complex_neg(const uint8_t *instruction);
        void op_vector_add(const uint8_t *instruction);
        void op_vector_sub(const uint8_t *instruction);
        void op_vector_mul(const uint8_t *instruction);
        void op_vector_div(const uint8_t *instruction);
        void op_vector_neg(const uint8_t *instruction);
        void op_vector_scl(const uint8_t *instruction);
        void op_vector_dot(const uint8_t *instruction);
        void op_vector_crs(const uint8_t *instruction);
        void op_matrix_add(const uint8_t *instruction);
        void op_matrix_sub(const uint8_t *instruction);
        void op_matrix_mul(const uint8_t *instruction);
        void op_matrix_neg(const uint8_t *instruction);
        void op_matrix_scl(const uint8_t *instruction);

        friend class vl_builtins::BuiltinsDelegate;
    };

}

#endif // VL_INTERPRETER_H
