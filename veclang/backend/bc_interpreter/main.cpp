#include <cstdint>
#include <vector>
#include <cstring>
#include <fstream>
#include <iostream>

#include "vl_interpreter.h"
#include "vl_builtins.h"

#include "vl_program.h"
#include "../bc_common/cpp/vl_sedf.h"

#include <vector>
#include <fstream>
#include <string>
#include <chrono>
#include <cstdint>
#include <algorithm>

// Helper to write a 32-bit int into a byte buffer in little-endian format
void writeIntLE(std::vector<uint8_t> &buffer, size_t offset, uint32_t value)
{
    buffer[offset + 0] = value & 0xFF;
    buffer[offset + 1] = (value >> 8) & 0xFF;
    buffer[offset + 2] = (value >> 16) & 0xFF;
    buffer[offset + 3] = (value >> 24) & 0xFF;
}

// Clamp a float value to [0, 255] and cast to uint8
uint8_t clamp255(float v)
{
    return static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, v)));
}

// Build BMP data in memory
std::vector<uint8_t> buildBMP(const std::vector<vl_types::VlVec3> &pixels, int width, int height)
{
    const int padSize = (4 - (width * 3) % 4) % 4;
    const int stride = width * 3 + padSize;
    const int pixelArraySize = stride * height;
    const int fileSize = 54 + pixelArraySize;

    std::vector<uint8_t> data(fileSize, 0);

    // --- File header (14 bytes) ---
    data[0] = 'B';
    data[1] = 'M';
    writeIntLE(data, 2, fileSize); // File size
    writeIntLE(data, 10, 54);      // Pixel data offset

    // --- DIB header (40 bytes) ---
    writeIntLE(data, 14, 40); // DIB header size
    writeIntLE(data, 18, width);
    writeIntLE(data, 22, height);
    data[26] = 1;                         // Planes
    data[28] = 24;                        // Bits per pixel
    writeIntLE(data, 34, pixelArraySize); // Image size

    // --- Pixel data ---
    size_t pixelOffset = 54;
    for (int y = height - 1; y >= 0; --y)
    { // BMP is bottom-up
        for (int x = 0; x < width; ++x)
        {
            const auto &p = pixels[y * width + x];
            data[pixelOffset++] = clamp255(p.z); // Blue
            data[pixelOffset++] = clamp255(p.y); // Green
            data[pixelOffset++] = clamp255(p.x); // Red
        }
        pixelOffset += padSize; // padding (already zero-initialized)
    }

    return data;
}

// Write BMP file from pixel data
void writeBMPToFile(const std::string &filename, const std::vector<vl_types::VlVec3> &pixels, int width, int height)
{
    std::vector<uint8_t> bmpData = buildBMP(pixels, width, height);

    std::ofstream out(filename, std::ios::binary);
    if (!out)
    {
        throw std::runtime_error("Failed to open output file: " + filename);
    }

    out.write(reinterpret_cast<char *>(bmpData.data()), bmpData.size());
    out.close();
}

int main()
{
    using std::chrono::duration;
    using std::chrono::duration_cast;
    using std::chrono::high_resolution_clock;
    using std::chrono::milliseconds;

    vl_sedf::VlProgram program = vl_sedf::load("C:\\Users\\xiada\\Documents\\veclang\\veclang\\tests\\out.sedf");
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

    const uint32_t HEIGHT = 256;
    const uint32_t WIDTH = 256;

    vl_interpreter::Interpreter interpreter(program);

    auto t1 = high_resolution_clock::now();
    // std::vector<vl_types::VlVec3> data = interpreter.generate_img(program, HEIGHT, WIDTH);
    // writeBMPToFile("out.bmp", data, HEIGHT, WIDTH);
    interpreter.interpret_program();
    auto t2 = high_resolution_clock::now();

    /* Getting number of milliseconds as an integer. */
    auto ms_int = duration_cast<milliseconds>(t2 - t1);

    /* Getting number of milliseconds as a double. */
    duration<double, std::milli> ms_double = t2 - t1;

    std::cout << ms_int.count() << "ms\n";
    std::cout << ms_double.count() << "ms\n";

    return 0;
}