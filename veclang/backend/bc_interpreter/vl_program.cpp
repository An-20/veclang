#include <cstdint>
#include <vector>
#include <cstring>
#include <fstream>
#include <iostream>

#include "vl_program.h"
#include "../bc_common/cpp/vl_sedf.h"

int main()
{
    vl_sedf::VlProgram program = vl_sedf::load("C:\\Users\\xiada\\Documents\\veclang\\veclang\\tests\\out2.sedf");
    std::cout << "Loaded VL SEDF program with magic: " << program.header.magic << "\n";
    std::cout << "Version: " << program.header.version << "\n";
    std::cout << "Functions:\n";
    for (const auto &func : program.header.functions)
    {
        std::cout << "  Name: " << func.name << ", Stack Size: " << func.stack_size
                  << ", Instruction Offset: " << func.instruction_offset
                  << ", Arg Types: ";
        for (auto type : func.arg_types)
            std::cout << (int)type << " ";
        std::cout << ", Return Type: " << (int)func.return_type << "\n";
    }
    std::cout << "Constants size: " << program.constants.size() << "\n";
    std::cout << "Instructions size: " << program.instructions.size() << "\n";
    // print constants bytes and instructions bytes
    std::cout << "Constants bytes: ";
    for (auto byte : program.constants)
        std::cout << (int)byte << " ";
    std::cout << "\n";

    std::cout << "Instructions bytes: ";
    for (auto byte : program.instructions)
        std::cout << (int)byte << " ";
    std::cout << "\n";
    return 0;
}
