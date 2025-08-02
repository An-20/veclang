#include "vl_sedf.h"

#include "../../../utils/cedf/cedf.hpp"

#include "../lib/json.hpp"
using json = nlohmann::json;

namespace vl_sedf
{
    VlProgram loadb(const std::vector<uint8_t> &data)
    {
        uint32_t sedf_id;
        std::string json_out;
        std::vector<uint8_t> payload_out;
        au_cedf::decode_cedf_from_bytes(data, sedf_id, json_out, payload_out);

        if (sedf_id != VL_SEDF_ID)
            throw std::runtime_error("Invalid VL SEDF ID, got " + std::to_string(sedf_id) + ", expected " + std::to_string(VL_SEDF_ID));

        json j = json::parse(json_out);
        VlProgram program;
        program.header.magic = j["magic"].get<std::string>();
        if (program.header.magic != "VECL")
            throw std::runtime_error("Invalid magic in VL SEDF header, got '" + program.header.magic + "', expected 'VECL'");
        program.header.version = j["version"].get<uint32_t>();
        if (program.header.version != VL_SEDF_VERSION)
            throw std::runtime_error("Unsupported VL SEDF version, got " + std::to_string(program.header.version) + ", expected 1");
        for (const auto &flag : j["flags"].items())
        {
            program.header.flags[flag.key()] = flag.value().get<uint32_t>();
        }
        for (const auto &func : j["functions"])
        {
            VlFunction vl_func;
            vl_func.name = func["name"].get<std::string>();
            vl_func.stack_size = func["stack_size"].get<uint32_t>();
            vl_func.instruction_offset = func["instruction_offset"].get<uint32_t>();
            vl_func.arg_types = func["arg_types"].get<std::vector<uint8_t>>();
            vl_func.return_type = func["return_type"].get<uint8_t>();
            program.header.functions.push_back(vl_func);
        }
        program.header.globals_stack_size = j["globals_stack_size"].get<uint32_t>();
        if (j["constants_len"].get<size_t>() + j["instructions_len"].get<size_t>() != payload_out.size())
            throw std::runtime_error("Payload size does not match declared sizes in JSON header");
        program.constants = std::vector<uint8_t>(payload_out.begin(), payload_out.begin() + j["constants_len"].get<size_t>());
        program.instructions = std::vector<uint8_t>(payload_out.begin() + j["constants_len"].get<size_t>(), payload_out.end());
        return program;
    }

    VlProgram load(const std::string &filepath)
    {
        std::vector<uint8_t> data = au_cedf::loadf(filepath);
        return loadb(data);
    }
}
