#include <iostream>
#include <string>
#include <unordered_map>
#include <sstream>
#include <vector>
#include <stack>

#include "vl_types.h"
#include "vl_program.h"
#include "vl_builtins.h"
#include "vl_interpreter.h"

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
        call_stack.pop_back();
        // todo: mess with instruction_pointer to return to the caller
    }
}