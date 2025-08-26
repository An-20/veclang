#include "vl_program.h"

#include <cstdint>
#include <vector>
#include <cstring>
#include <fstream>
#include <iostream>

#include "../bc_common/cpp/vl_sedf.h"

namespace vl_program
{
    size_t get_type_canonical_size(type_code type)
    {
        switch (type)
        {
        case VL_INT:
            return 8;
        case VL_BOOL:
            return 1;
        case VL_REAL:
            return 8;
        case VL_COMPLEX:
            return 16;
        case VL_VEC2:
            return 16;
        case VL_VEC3:
            return 24;
        case VL_VEC4:
            return 32;
        case VL_MAT2:
            return 32;
        case VL_MAT3:
            return 64;
        case VL_MAT4:
            return 128;
        case VL_STR:
            return 128;
        default:
            throw std::runtime_error("Unknown type code");
        }
    }
}
