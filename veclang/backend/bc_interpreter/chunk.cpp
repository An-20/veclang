#include <cstdint>
#include <vector>
#include <cstring>
#include <fstream>
#include <iostream>

#include "chunk.h"


Chunk deserialize_chunk(const std::vector<uint8_t>& data) {
    Chunk chunk;
    size_t offset = 0;

    // Read the length of instructions (in bytes)
    uint32_t instructions_bytes_length;
    std::memcpy(&instructions_bytes_length, data.data() + offset, sizeof(uint32_t));
    offset += sizeof(uint32_t);

    // Read the length of constants (in bytes)
    uint32_t constants_bytes_length;
    std::memcpy(&constants_bytes_length, data.data() + offset, sizeof(uint32_t));
    offset += sizeof(uint32_t);

    // Read the instructions
    size_t num_instructions = instructions_bytes_length / 4;
    chunk.instructions.resize(num_instructions);
    std::memcpy(chunk.instructions.data(), data.data() + offset, instructions_bytes_length);
    offset += instructions_bytes_length;

    // Read the constants
    size_t num_constants = constants_bytes_length;
    chunk.constants.resize(num_constants);
    std::memcpy(chunk.constants.data(), data.data() + offset, constants_bytes_length);

    return chunk;
}


int main() {
    // Open the file in binary mode
    std::ifstream file("chunk.bin", std::ios::binary);
    if (!file) {
        std::cerr << "Failed to open file." << std::endl;
        return 1;
    }

    std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

    Chunk chunk = deserialize_chunk(data);

    std::cout << "Instructions: ";
    for (const auto& instr : chunk.instructions) {
        std::cout << instr << " ";
    }
    std::cout << std::endl;

    std::cout << "Constants: ";
    for (const auto& constant : chunk.constants) {
        std::cout << constant << " ";
    }
    std::cout << std::endl;

    return 0;
}
