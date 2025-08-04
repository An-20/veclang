#include "vl_interpreter.h"

#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <stack>

#include "vl_program.h"
#include "vl_builtins.h"
#include "vl_types_val.h"
#include "vl_types_obj.h"

uint16_t get_1_operand(const uint8_t *instruction)
{
    // get a uint16_t operand from the third and fourth bytes of the instruction
    return (static_cast<uint16_t>(instruction[2]) << 8) | instruction[3];
}

std::pair<uint8_t, uint16_t> get_2_operands(const uint8_t *instruction)
{
    // get a uint8_t opcode from the second byte
    // and a uint16_t operand from the third and fourth bytes of the instruction
    uint8_t operand_1 = instruction[1];
    uint16_t operand_2 = get_1_operand(instruction);
    return {operand_1, operand_2};
}

namespace vl_interpreter
{
    void Interpreter::op_constant_val_direct(const uint8_t *instruction)
    {
        uint16_t value_16b = get_1_operand(instruction);
        vl_types::RawValue value;
        value.bits = value_16b;
        value_stack.push(value);
    }

    void Interpreter::op_constant_obj_direct(const uint8_t *instruction)
    {
        throw std::runtime_error("OP_CONSTANT_OBJ_DIRECT not implemented yet");
    }

    void Interpreter::op_constant_val_table(const uint8_t *instruction)
    {
        uint16_t offset_16b = get_1_operand(instruction);
        if (offset_16b >= constants.size())
        {
            std::cerr << "Index out of bounds: " << offset_16b << "\n";
            return;
        }
        vl_types::RawValue value;
        std::memcpy(&value.bits, constants.data() + offset_16b, 4); // todo: fix for variable runtime precision
        value_stack.push(value);
    }

    void Interpreter::op_constant_obj_table(const uint8_t *instruction)
    {
        auto [type_8b, offset_16b] = get_2_operands(instruction);
        if (offset_16b >= constants.size())
        {
            std::cerr << "Index out of bounds: " << offset_16b << "\n";
            return;
        }
        size_t type_size = vl_program::get_type_canonical_size(static_cast<vl_program::type_code>(type_8b));
        vl_types::RawObject object;
        std::memcpy(&object.bits, constants.data() + offset_16b, type_size);
        object_stack.push(object);
    }

    void Interpreter::op_pop_val(const uint8_t *instruction)
    {
        if (value_stack.empty())
        {
            std::cerr << "Value stack underflow\n";
            return;
        }
        value_stack.pop();
    }

    void Interpreter::op_pop_obj(const uint8_t *instruction)
    {
        if (object_stack.empty())
        {
            std::cerr << "Object stack underflow\n";
            return;
        }
        object_stack.pop();
    }

    void Interpreter::op_call_builtin(const uint8_t *instruction)
    {
        uint16_t builtin_id = get_1_operand(instruction);
        vl_builtins::BuiltinsDelegate delegate(*this);
        vl_builtins::call_builtin(delegate, builtin_id);
    }

    void Interpreter::op_call(const uint8_t *instruction)
    {
        uint16_t func_id = get_1_operand(instruction);
        throw std::runtime_error("Function call not implemented yet: " + std::to_string(func_id));
    }

    void Interpreter::op_return(const uint8_t *instruction)
    {
        if (call_stack.empty())
        {
            std::cerr << "Call stack underflow\n";
            return;
        }
        instruction_pointer = call_stack.top().return_address;
        call_stack.pop();
        // TODO: mess with instruction_pointer to return to the caller
    }

    void Interpreter::op_get_local_val(const uint8_t *instruction)
    {
        uint32_t offset = get_1_operand(instruction) + get_local_stack_offset();
        vl_types::RawValue value;
        memcpy(&value.bits, local_stack.data() + offset, sizeof(vl_types::RawValue));
        value_stack.push(value);
    }

    void Interpreter::op_set_local_val(const uint8_t *instruction)
    {
        uint32_t offset = get_1_operand(instruction) + get_local_stack_offset();
        vl_types::RawValue value = value_stack.top();
        memcpy(local_stack.data() + offset, &value.bits, sizeof(vl_types::RawValue));
        value_stack.pop();
    }

    void Interpreter::op_get_global_val(const uint8_t *instruction)
    {
        uint32_t offset = get_1_operand(instruction);
        vl_types::RawValue value;
        memcpy(&value.bits, global_stack.data() + offset, sizeof(vl_types::RawValue));
        value_stack.push(value);
    }

    void Interpreter::op_set_global_val(const uint8_t *instruction)
    {
        uint32_t offset = get_1_operand(instruction);
        vl_types::RawValue value = value_stack.top();
        memcpy(global_stack.data() + offset, &value.bits, sizeof(vl_types::RawValue));
        value_stack.pop();
    }

    void Interpreter::op_get_local_obj(const uint8_t *instruction)
    {
        auto [type_8b, offset_16b] = get_2_operands(instruction);
        auto adj_offset = offset_16b + get_local_stack_offset();
        vl_types::RawObject object;
        size_t type_size = vl_program::get_type_canonical_size(static_cast<vl_program::type_code>(type_8b));
        memcpy(&object.bits, local_stack.data() + adj_offset, type_size);
        object_stack.push(object);
    }

    void Interpreter::op_set_local_obj(const uint8_t *instruction)
    {
        auto [type_8b, offset_16b] = get_2_operands(instruction);
        auto adj_offset = offset_16b + get_local_stack_offset();
        vl_types::RawObject object = object_stack.top();
        size_t type_size = vl_program::get_type_canonical_size(static_cast<vl_program::type_code>(type_8b));
        memcpy(local_stack.data() + adj_offset, &object.bits, type_size);
        object_stack.pop();
    }

    void Interpreter::op_get_global_obj(const uint8_t *instruction)
    {
        auto [type_8b, offset_16b] = get_2_operands(instruction);
        vl_types::RawObject object;
        size_t type_size = vl_program::get_type_canonical_size(static_cast<vl_program::type_code>(type_8b));
        memcpy(&object.bits, global_stack.data() + offset_16b, type_size);
        object_stack.push(object);
    }

    void Interpreter::op_set_global_obj(const uint8_t *instruction)
    {
        auto [type_8b, offset_16b] = get_2_operands(instruction);
        vl_types::RawObject object = object_stack.top();
        size_t type_size = vl_program::get_type_canonical_size(static_cast<vl_program::type_code>(type_8b));
        memcpy(global_stack.data() + offset_16b, &object.bits, type_size);
        object_stack.pop();
    }

    void Interpreter::op_jmp(const uint8_t *instruction)
    {
        uint16_t offset = get_1_operand(instruction);
        instruction_pointer = offset;
    }

    void Interpreter::op_jmp_if_true(const uint8_t *instruction)
    {
        uint16_t offset = get_1_operand(instruction);
        if (value_stack.empty())
        {
            std::cerr << "Value stack underflow\n";
            return;
        }
        vl_types::RawValue condition = value_stack.top();
        if (condition.bits != 0)
        {
            instruction_pointer = offset;
        }
        value_stack.pop();
    }

    void Interpreter::op_jmp_if_false(const uint8_t *instruction)
    {
        uint16_t offset = get_1_operand(instruction);
        if (value_stack.empty())
        {
            std::cerr << "Value stack underflow\n";
            return;
        }
        vl_types::RawValue condition = value_stack.top();
        if (condition.bits == 0)
        {
            instruction_pointer = offset;
        }
        value_stack.pop();
    }

// Macro to define binary value operations using vl_types functions
#define DEFINE_BINARY_VAL_OP(opname)                          \
    void Interpreter::op_##opname(const uint8_t *instruction) \
    {                                                         \
        vl_types::RawValue a = value_stack.top();             \
        value_stack.pop();                                    \
        vl_types::RawValue b = value_stack.top();             \
        value_stack.pop();                                    \
        vl_types::RawValue result = vl_types::opname(a, b);   \
        value_stack.push(result);                             \
    }

    DEFINE_BINARY_VAL_OP(int_equal)
    DEFINE_BINARY_VAL_OP(int_not_equal)
    DEFINE_BINARY_VAL_OP(int_greater)
    DEFINE_BINARY_VAL_OP(int_greater_or_equal)
    DEFINE_BINARY_VAL_OP(int_less)
    DEFINE_BINARY_VAL_OP(int_less_or_equal)
    DEFINE_BINARY_VAL_OP(int_add)
    DEFINE_BINARY_VAL_OP(int_sub)
    DEFINE_BINARY_VAL_OP(int_mul)
    DEFINE_BINARY_VAL_OP(int_div)
    DEFINE_BINARY_VAL_OP(int_mod)
    DEFINE_BINARY_VAL_OP(int_pow)
    DEFINE_BINARY_VAL_OP(int_and)
    DEFINE_BINARY_VAL_OP(int_or)
    DEFINE_BINARY_VAL_OP(int_xor)
    DEFINE_BINARY_VAL_OP(int_left_shift)
    DEFINE_BINARY_VAL_OP(int_right_shift)
    DEFINE_BINARY_VAL_OP(boolean_and)
    DEFINE_BINARY_VAL_OP(boolean_or)

    DEFINE_BINARY_VAL_OP(real_equal)
    DEFINE_BINARY_VAL_OP(real_not_equal)
    DEFINE_BINARY_VAL_OP(real_greater)
    DEFINE_BINARY_VAL_OP(real_greater_or_equal)
    DEFINE_BINARY_VAL_OP(real_less)
    DEFINE_BINARY_VAL_OP(real_less_or_equal)
    DEFINE_BINARY_VAL_OP(real_add)
    DEFINE_BINARY_VAL_OP(real_sub)
    DEFINE_BINARY_VAL_OP(real_mul)
    DEFINE_BINARY_VAL_OP(real_div)
    DEFINE_BINARY_VAL_OP(real_mod)
    DEFINE_BINARY_VAL_OP(real_pow)

#undef DEFINE_BINARY_VAL_OP

// Macro to define unary value operations using vl_types functions
#define DEFINE_UNARY_VAL_OP(opname)                           \
    void Interpreter::op_##opname(const uint8_t *instruction) \
    {                                                         \
        vl_types::RawValue value = value_stack.top();         \
        value_stack.pop();                                    \
        vl_types::RawValue result = vl_types::opname(value);  \
        value_stack.push(result);                             \
    }

    DEFINE_UNARY_VAL_OP(int_neg)
    DEFINE_UNARY_VAL_OP(int_not)
    DEFINE_UNARY_VAL_OP(real_neg)
    DEFINE_UNARY_VAL_OP(boolean_not)

#undef DEFINE_UNARY_VAL_OP

// Macro to define binary object operations returning a value using vl_types functions
#define DEFINE_BINARY_OBJ_OP_RET_VAL(opname)                  \
    void Interpreter::op_##opname(const uint8_t *instruction) \
    {                                                         \
        vl_types::RawObject a = object_stack.top();           \
        object_stack.pop();                                   \
        vl_types::RawObject b = object_stack.top();           \
        object_stack.pop();                                   \
        vl_types::RawValue result = vl_types::opname(a, b);   \
        value_stack.push(result);                             \
    }

    DEFINE_BINARY_OBJ_OP_RET_VAL(complex_equal);
    DEFINE_BINARY_OBJ_OP_RET_VAL(complex_not_equal);

#undef DEFINE_BINARY_OBJ_OP_RET_VAL

// Macro to define binary object operations using vl_types functions
#define DEFINE_BINARY_OBJ_OP_RET_OBJ(opname)                  \
    void Interpreter::op_##opname(const uint8_t *instruction) \
    {                                                         \
        vl_types::RawObject a = object_stack.top();           \
        object_stack.pop();                                   \
        vl_types::RawObject b = object_stack.top();           \
        object_stack.pop();                                   \
        vl_types::RawObject result = vl_types::opname(a, b);  \
        object_stack.push(result);                            \
    }

    DEFINE_BINARY_OBJ_OP_RET_OBJ(complex_add);
    DEFINE_BINARY_OBJ_OP_RET_OBJ(complex_sub);
    DEFINE_BINARY_OBJ_OP_RET_OBJ(complex_mul);
    DEFINE_BINARY_OBJ_OP_RET_OBJ(complex_div);
    DEFINE_BINARY_OBJ_OP_RET_OBJ(complex_pow);

    void Interpreter::op_complex_neg(const uint8_t *instruction)
    {
        vl_types::RawObject a = object_stack.top();
        object_stack.pop();
        vl_types::RawObject result = vl_types::complex_neg(a);
        object_stack.push(result);
    }

    void Interpreter::op_vector_add(const uint8_t *instruction) { std::cerr << "op_vector_add unimplemented"; }
    void Interpreter::op_vector_sub(const uint8_t *instruction) { std::cerr << "op_vector_sub unimplemented"; }
    void Interpreter::op_vector_mul(const uint8_t *instruction) { std::cerr << "op_vector_mul unimplemented"; }
    void Interpreter::op_vector_div(const uint8_t *instruction) { std::cerr << "op_vector_div unimplemented"; }
    void Interpreter::op_vector_neg(const uint8_t *instruction) { std::cerr << "op_vector_neg unimplemented"; }
    void Interpreter::op_vector_scl(const uint8_t *instruction) { std::cerr << "op_vector_scl unimplemented"; }
    void Interpreter::op_vector_dot(const uint8_t *instruction) { std::cerr << "op_vector_dot unimplemented"; }
    void Interpreter::op_vector_crs(const uint8_t *instruction) { std::cerr << "op_vector_crs unimplemented"; }
    void Interpreter::op_matrix_add(const uint8_t *instruction) { std::cerr << "op_matrix_add unimplemented"; }
    void Interpreter::op_matrix_sub(const uint8_t *instruction) { std::cerr << "op_matrix_sub unimplemented"; }
    void Interpreter::op_matrix_mul(const uint8_t *instruction) { std::cerr << "op_matrix_mul unimplemented"; }
    void Interpreter::op_matrix_neg(const uint8_t *instruction) { std::cerr << "op_matrix_neg unimplemented"; }
    void Interpreter::op_matrix_scl(const uint8_t *instruction) { std::cerr << "op_matrix_scl unimplemented"; }

}
