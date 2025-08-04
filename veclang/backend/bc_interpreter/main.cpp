#include <cstdint>
#include <vector>
#include <cstring>
#include <fstream>
#include <iostream>

#include "vl_interpreter.h"
#include "vl_builtins.h"

#include "vl_program.h"
#include "../bc_common/cpp/vl_sedf.h"

void writeBMP(const std::string &filename, const std::vector<vl_types::VlVec3> &pixels, int width, int height)
{
    const int padSize = (4 - (width * 3) % 4) % 4;
    const int stride = (width * 3) + padSize;
    const int fileSize = 54 + stride * height;

    uint8_t fileHeader[14] = {
        'B', 'M',   // Signature
        0, 0, 0, 0, // File size
        0, 0, 0, 0, // Reserved
        54, 0, 0, 0 // Pixel data offset
    };

    uint8_t infoHeader[40] = {
        40, 0, 0, 0, // Header size
        0, 0, 0, 0,  // Image width
        0, 0, 0, 0,  // Image height
        1, 0,        // Planes
        24, 0,       // Bits per pixel
        0, 0, 0, 0,  // Compression
        0, 0, 0, 0,  // Image size
        0, 0, 0, 0,  // X pixels per meter
        0, 0, 0, 0,  // Y pixels per meter
        0, 0, 0, 0,  // Total colors
        0, 0, 0, 0   // Important colors
    };

    // Set file size
    fileHeader[2] = (uint8_t)(fileSize);
    fileHeader[3] = (uint8_t)(fileSize >> 8);
    fileHeader[4] = (uint8_t)(fileSize >> 16);
    fileHeader[5] = (uint8_t)(fileSize >> 24);

    // Set width and height
    infoHeader[4] = (uint8_t)(width);
    infoHeader[5] = (uint8_t)(width >> 8);
    infoHeader[6] = (uint8_t)(width >> 16);
    infoHeader[7] = (uint8_t)(width >> 24);

    infoHeader[8] = (uint8_t)(height);
    infoHeader[9] = (uint8_t)(height >> 8);
    infoHeader[10] = (uint8_t)(height >> 16);
    infoHeader[11] = (uint8_t)(height >> 24);

    std::ofstream out(filename, std::ios::binary);
    out.write(reinterpret_cast<char *>(fileHeader), sizeof(fileHeader));
    out.write(reinterpret_cast<char *>(infoHeader), sizeof(infoHeader));

    std::vector<uint8_t> padding(padSize, 0);

    for (int y = height - 1; y >= 0; --y)
    { // BMP files are bottom-up
        for (int x = 0; x < width; ++x)
        {
            const vl_types::VlVec3 &pixel = pixels[y * width + x];
            uint8_t rgb[] = {
                static_cast<uint8_t>(pixel.x),
                static_cast<uint8_t>(pixel.y),
                static_cast<uint8_t>(pixel.z)};
            out.write(reinterpret_cast<char *>(rgb), sizeof(rgb));
        }
        out.write(reinterpret_cast<char *>(padding.data()), padSize);
    }

    out.close();
}

int main()
{
    vl_sedf::VlProgram program = vl_sedf::load("C:\\Users\\xiada\\Documents\\veclang\\veclang\\tests\\outmandle.sedf");
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
    std::cout << "Globals stack Size: " << program.header.globals_stack_size << "\n\n";
    // print constants bytes and instructions bytes
    std::cout << "Constants bytes: ";
    for (auto byte : program.constants)
        std::cout << (int)byte << " ";
    std::cout << "\n";

    std::cout << "Instructions bytes: ";
    for (auto byte : program.instructions)
        std::cout << (int)byte << " ";
    std::cout << "\n\n";

    vl_interpreter::Interpreter interpreter;
    vl_types::RawObject out = interpreter.interpret_tl_fn(program, 254, 256, 255, 256);
    vl_types::VlVec3 vec3 = vl_types::ro_to_vec3(out);
    std::cout << "out: " << vec3.x << " " << vec3.y << " " << vec3.z << "\n";

    std::vector<vl_types::VlVec3> data = interpreter.generate_img(program);
    writeBMP("out.bmp", data, 256, 256);

    return 0;
}