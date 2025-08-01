#include <iostream>
#include <string>
#include <unordered_map>
#include <sstream>
#include <vector>
#include <stack>

#include "vl_types.h"
#include "vl_program.h"

struct StackFrame
{
};

class Interpreter
{
public:
    void interpret(const std::string &code)
    {
        std::istringstream stream(code);
        std::string line;
        while (std::getline(stream, line))
        {
            interpret_instruction(reinterpret_cast<const uint8_t *>(line.data()));
        }
    }

private:
    std::vector<uint8_t> constants;
    std::vector<uint8_t> stack;
    std::vector<StackFrame> call_stack;
    std::stack<vl_data::RawValue> value_stack;
    std::stack<vl_data::RawObject> object_stack;

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
        // Handle other opcodes...
        default:
            std::cerr << "Unknown opcode: " << static_cast<int>(opcode) << "\n";
            break;
        }
    }

    void op_constant_val_direct(const uint8_t *instruction)
    {
        uint16_t value_16b = get_1_operand(instruction);
        vl_data::RawValue value;
        value.bits = value_16b;
        value_stack.push(value);
    }

    void op_constant_obj_direct(const uint8_t *instruction)
    {
        throw std::runtime_error("OP_CONSTANT_OBJ_DIRECT not implemented yet");
    }

    void op_constant_val_table(const uint8_t *instruction)
    {
        uint16_t offset_16b = get_1_operand(instruction);
        if (offset_16b >= constants.size())
        {
            std::cerr << "Index out of bounds: " << offset_16b << "\n";
            return;
        }
        vl_data::RawValue value;
        std::memcpy(&value.bits, constants.data() + offset_16b, 4); // todo: fix for variable runtime precision
        value_stack.push(value);
    }

    void op_constant_obj_table(const uint8_t *instruction)
    {
        auto [type_8b, offset_16b] = get_2_operands(instruction);
        if (offset_16b >= constants.size())
        {
            std::cerr << "Index out of bounds: " << offset_16b << "\n";
            return;
        }
        size_t type_size = vl_program::get_type_canonical_size(static_cast<vl_program::type_code>(type_8b));
        vl_data::RawObject object;
        std::memcpy(&object.bits, constants.data() + offset_16b, type_size);
        object_stack.push(object);
    }
};
