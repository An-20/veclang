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

        StackFrame(uint32_t return_address_, uint32_t stack_start_, uint32_t stack_size_) : return_address(return_address_), stack_start(stack_start_), stack_size(stack_size_) {}
    };

    class Interpreter
    {
    public:
        void interpret(const vl_sedf::VlProgram &program)
        {
            constants = program.constants;
            instructions = program.instructions;
            instruction_pointer = 0;
            uint32_t num_instructions = instructions.size() / 4;

            global_stack = std::vector<uint8_t>(program.header.globals_stack_size);
            local_stack = std::vector<uint8_t>();
            call_stack = std::stack<StackFrame>();
            value_stack = std::stack<vl_types::RawValue>();
            object_stack = std::stack<vl_types::RawObject>();

            while (instruction_pointer < num_instructions)
            {
                const uint8_t *instruction = &instructions[instruction_pointer * 4];
                instruction_pointer += 1;
                interpret_instruction(instruction);
            }
        }

        std::vector<vl_types::VlVec3> generate_img(
            const vl_sedf::VlProgram &program,
            const uint32_t height,
            const uint32_t width)
        {
            constants = program.constants;
            instructions = program.instructions;
            uint32_t num_instructions = instructions.size() / 4;
            uint32_t local_stack_size = program.header.functions.at(0).stack_size;

            global_stack = std::vector<uint8_t>(program.header.globals_stack_size);
            local_stack = std::vector<uint8_t>(local_stack_size);
            call_stack = std::stack<StackFrame>();
            value_stack = std::stack<vl_types::RawValue>();
            object_stack = std::stack<vl_types::RawObject>();

            std::vector<vl_types::VlVec3> output;
            output.reserve(height * width);

            uint32_t total = 0;

            for (uint32_t y = 0; y < height; y++)
            {
                for (uint32_t x = 0; x < width; x++)
                {
                    instruction_pointer = 0;
                    call_stack.push(StackFrame(num_instructions, 0, local_stack_size));

                    value_stack.push(vl_types::int_to_rv(x));
                    value_stack.push(vl_types::int_to_rv(y));
                    value_stack.push(vl_types::int_to_rv(width));
                    value_stack.push(vl_types::int_to_rv(height));

                    while (instruction_pointer < num_instructions)
                    {
                        const uint8_t *instruction = &instructions[instruction_pointer * 4];
                        instruction_pointer += 1;
                        total++;
                        interpret_instruction(instruction);
                    }

                    output.push_back(vl_types::ro_to_vec3(object_stack.top()));
                    object_stack.pop();
                }
                // std::cout << "done with row " << y << std::endl;
            }
            std::cout << total << std::endl;
            return output;
        }

    private:
        uint32_t instruction_pointer = 0;
        std::vector<uint8_t> constants;
        std::vector<uint8_t> instructions;

        std::vector<uint8_t> global_stack;
        std::vector<uint8_t> local_stack;
        std::stack<StackFrame> call_stack;

        std::stack<vl_types::RawValue> value_stack;
        std::stack<vl_types::RawObject> object_stack;

        uint32_t get_local_stack_offset()
        {
            if (call_stack.empty())
                return 0;
            return call_stack.top().stack_start;
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
            case vl_program::OP_INT_EQUAL:
                op_int_equal(instruction);
                break;
            case vl_program::OP_INT_NOT_EQUAL:
                op_int_not_equal(instruction);
                break;
            case vl_program::OP_INT_GREATER:
                op_int_greater(instruction);
                break;
            case vl_program::OP_INT_GREATER_OR_EQUAL:
                op_int_greater_or_equal(instruction);
                break;
            case vl_program::OP_INT_LESS:
                op_int_less(instruction);
                break;
            case vl_program::OP_INT_LESS_OR_EQUAL:
                op_int_less_or_equal(instruction);
                break;
            case vl_program::OP_INT_ADD:
                op_int_add(instruction);
                break;
            case vl_program::OP_INT_SUB:
                op_int_sub(instruction);
                break;
            case vl_program::OP_INT_MUL:
                op_int_mul(instruction);
                break;
            case vl_program::OP_INT_DIV:
                op_int_div(instruction);
                break;
            case vl_program::OP_INT_MOD:
                op_int_mod(instruction);
                break;
            case vl_program::OP_INT_POW:
                op_int_pow(instruction);
                break;
            case vl_program::OP_INT_NEG:
                op_int_neg(instruction);
                break;
            case vl_program::OP_INT_AND:
                op_int_and(instruction);
                break;
            case vl_program::OP_INT_OR:
                op_int_or(instruction);
                break;
            case vl_program::OP_INT_XOR:
                op_int_xor(instruction);
                break;
            case vl_program::OP_INT_NOT:
                op_int_not(instruction);
                break;
            case vl_program::OP_INT_LEFT_SHIFT:
                op_int_left_shift(instruction);
                break;
            case vl_program::OP_INT_RIGHT_SHIFT:
                op_int_right_shift(instruction);
                break;
            case vl_program::OP_BOOLEAN_AND:
                op_boolean_and(instruction);
                break;
            case vl_program::OP_BOOLEAN_OR:
                op_boolean_or(instruction);
                break;
            case vl_program::OP_BOOLEAN_NOT:
                op_boolean_not(instruction);
                break;
            case vl_program::OP_REAL_EQUAL:
                op_real_equal(instruction);
                break;
            case vl_program::OP_REAL_NOT_EQUAL:
                op_real_not_equal(instruction);
                break;
            case vl_program::OP_REAL_GREATER:
                op_real_greater(instruction);
                break;
            case vl_program::OP_REAL_GREATER_OR_EQUAL:
                op_real_greater_or_equal(instruction);
                break;
            case vl_program::OP_REAL_LESS:
                op_real_less(instruction);
                break;
            case vl_program::OP_REAL_LESS_OR_EQUAL:
                op_real_less_or_equal(instruction);
                break;
            case vl_program::OP_REAL_ADD:
                op_real_add(instruction);
                break;
            case vl_program::OP_REAL_SUB:
                op_real_sub(instruction);
                break;
            case vl_program::OP_REAL_MUL:
                op_real_mul(instruction);
                break;
            case vl_program::OP_REAL_DIV:
                op_real_div(instruction);
                break;
            case vl_program::OP_REAL_MOD:
                op_real_mod(instruction);
                break;
            case vl_program::OP_REAL_POW:
                op_real_pow(instruction);
                break;
            case vl_program::OP_REAL_NEG:
                op_real_neg(instruction);
                break;
            case vl_program::OP_COMPLEX_EQUAL:
                op_complex_equal(instruction);
                break;
            case vl_program::OP_COMPLEX_NOT_EQUAL:
                op_complex_not_equal(instruction);
                break;
            case vl_program::OP_COMPLEX_ADD:
                op_complex_add(instruction);
                break;
            case vl_program::OP_COMPLEX_SUB:
                op_complex_sub(instruction);
                break;
            case vl_program::OP_COMPLEX_MUL:
                op_complex_mul(instruction);
                break;
            case vl_program::OP_COMPLEX_DIV:
                op_complex_div(instruction);
                break;
            case vl_program::OP_COMPLEX_POW:
                op_complex_pow(instruction);
                break;
            case vl_program::OP_COMPLEX_NEG:
                op_complex_neg(instruction);
                break;
            case vl_program::OP_VECTOR_ADD:
                op_vector_add(instruction);
                break;
            case vl_program::OP_VECTOR_SUB:
                op_vector_sub(instruction);
                break;
            case vl_program::OP_VECTOR_MUL:
                op_vector_mul(instruction);
                break;
            case vl_program::OP_VECTOR_DIV:
                op_vector_div(instruction);
                break;
            case vl_program::OP_VECTOR_NEG:
                op_vector_neg(instruction);
                break;
            case vl_program::OP_VECTOR_SCL:
                op_vector_scl(instruction);
                break;
            case vl_program::OP_VECTOR_DOT:
                op_vector_dot(instruction);
                break;
            case vl_program::OP_VECTOR_CRS:
                op_vector_crs(instruction);
                break;
            case vl_program::OP_MATRIX_ADD:
                op_matrix_add(instruction);
                break;
            case vl_program::OP_MATRIX_SUB:
                op_matrix_sub(instruction);
                break;
            case vl_program::OP_MATRIX_MUL:
                op_matrix_mul(instruction);
                break;
            case vl_program::OP_MATRIX_NEG:
                op_matrix_neg(instruction);
                break;
            case vl_program::OP_MATRIX_SCL:
                op_matrix_scl(instruction);
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
