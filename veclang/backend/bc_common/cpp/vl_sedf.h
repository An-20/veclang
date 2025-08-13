#ifndef VL_SEDF_H
#define VL_SEDF_H

#include <iostream>
#include <cstdint>
#include <vector>
#include <map>

namespace vl_sedf
{
    constexpr uint32_t VL_SEDF_ID = 0x00010000;
    constexpr uint32_t VL_SEDF_VERSION = 0x00020000;

    struct VlFunction
    {
        std::string name;
        uint32_t stack_size;
        uint32_t instruction_offset;
        std::vector<uint8_t> arg_types;
        uint8_t return_type;
    };

    struct VlHeader
    {
        std::string magic; // Should always be "VECL"
        uint32_t version;
        std::map<std::string, uint32_t> flags;
        std::vector<VlFunction> functions;
        uint32_t globals_stack_size;
    };

    struct VlProgram
    {
        VlHeader header;
        std::vector<uint8_t> constants;
        std::vector<uint8_t> instructions;
    };

    VlProgram loadb(const std::vector<uint8_t> &data);
    VlProgram load(const std::string &filepath);
}

#endif // VL_SEDF_H
