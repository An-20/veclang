#include <cstdint>
#include <cstring>

namespace vl_data
{
    struct VlMat2
    {
        float data[4];
    };

    struct VlMat3
    {
        float data[9];
    };

    struct VlMat4
    {
        float data[16];
    };

    struct VlVec2
    {
        float x, y;
    };

    struct VlVec3
    {
        float x, y, z;
    };

    struct VlVec4
    {
        float x, y, z, w;
    };

    struct VlComplex
    {
        float real, imag;
    };

    struct RawValue
    {
        uint32_t bits;
    };

    struct RawObject
    {
        uint32_t bits[16];
    };

    uint32_t rv_to_int(const RawValue &rv)
    {
        return rv.bits;
    }

    float rv_to_float(const RawValue &rv)
    {
        float value;
        std::memcpy(&value, &rv.bits, sizeof(float));
        return value;
    }

}
