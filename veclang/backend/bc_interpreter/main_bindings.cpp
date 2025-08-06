#include <emscripten/bind.h>

#include <cstdint>
#include <vector>
#include <cstring>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <algorithm>

#include "vl_interpreter.h"
#include "vl_builtins.h"

#include "vl_program.h"
#include "../bc_common/cpp/vl_sedf.h"

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

using namespace emscripten;

std::vector<uint8_t> generate_img(std::vector<uint8_t> program_data, uint32_t dim)
{
    const uint32_t HEIGHT = dim;
    const uint32_t WIDTH = dim;

    vl_sedf::VlProgram program = vl_sedf::loadb(program_data);
    vl_interpreter::Interpreter interpreter;
    std::vector<vl_types::VlVec3> data = interpreter.generate_img(program, HEIGHT, WIDTH);
    std::vector<uint8_t> bmp_data = buildBMP(data, HEIGHT, WIDTH);
    return bmp_data;
}

EMSCRIPTEN_BINDINGS(module)
{
    function("generate_img", &generate_img);
    register_vector<uint8_t>("vector_uint8");
}