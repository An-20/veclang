#ifndef VL_INTERPRETER_H
#define VL_INTERPRETER_H

#include <cstdint>
#include <stack>
#include <sstream>
#include <stdexcept>
#include <iostream>
#include "vl_types.h"
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
        std::vector<uint8_t> stack;
        std::vector<StackFrame> call_stack;
        std::stack<vl_types::RawValue> value_stack;
        std::stack<vl_types::RawObject> object_stack;

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
            case vl_program::OP_CALL_BUILTIN:
                op_call_builtin(instruction);
                break;
            case vl_program::OP_POP_VAL:
                op_pop_val(instruction);
                break;
            case vl_program::OP_POP_OBJ:
                op_pop_obj(instruction);
                break;
            // Handle other opcodes...
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

        friend class vl_builtins::BuiltinsDelegate;
    };

}

#endif // VL_INTERPRETER_H
