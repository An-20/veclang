#ifndef VL_TYPES_H
#define VL_TYPES_H

#include <cstdint>
#include <cstring>
#include <cmath>
#include <stdexcept>

namespace vl_types
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

    inline RawValue null()
    {
        RawValue value;
        value.bits = 0;
        return value;
    }

    inline RawValue int_to_rv(int32_t value)
    {
        RawValue rv;
        rv.bits = static_cast<uint32_t>(value);
        return rv;
    }

    inline RawValue bool_to_rv(bool value)
    {
        RawValue rv;
        rv.bits = value ? 1 : 0;
        return rv;
    }

    inline RawValue float_to_rv(float value)
    {
        RawValue rv;
        std::memcpy(&rv.bits, &value, sizeof(float));
        return rv;
    }

    inline int32_t rv_to_int(const RawValue &rv)
    {
        return static_cast<int32_t>(rv.bits);
    }

    inline float rv_to_float(const RawValue &rv)
    {
        float value;
        std::memcpy(&value, &rv.bits, sizeof(float));
        return value;
    }

    inline VlComplex ro_to_complex(const RawObject &ro)
    {
        float real, imag;
        std::memcpy(&real, &ro.bits[0], sizeof(float));
        std::memcpy(&imag, &ro.bits[1], sizeof(float));
        VlComplex complex;
        complex.real = real;
        complex.imag = imag;
        return complex;
    }

    inline RawObject complex_to_ro(const VlComplex &complex)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &complex.real, sizeof(float));
        std::memcpy(&obj.bits[1], &complex.imag, sizeof(float));
        return obj;
    }

    RawValue int_equal(const RawValue &a, const RawValue &b);
    RawValue int_not_equal(const RawValue &a, const RawValue &b);
    RawValue int_greater(const RawValue &a, const RawValue &b);
    RawValue int_less(const RawValue &a, const RawValue &b);
    RawValue int_greater_equal(const RawValue &a, const RawValue &b);
    RawValue int_less_equal(const RawValue &a, const RawValue &b);
    RawValue int_add(const RawValue &a, const RawValue &b);
    RawValue int_sub(const RawValue &a, const RawValue &b);
    RawValue int_mul(const RawValue &a, const RawValue &b);
    RawValue int_div(const RawValue &a, const RawValue &b);
    RawValue int_mod(const RawValue &a, const RawValue &b);
    RawValue int_exp(const RawValue &a, const RawValue &b);
    RawValue int_neg(const RawValue &a);
    RawValue int_and(const RawValue &a, const RawValue &b);
    RawValue int_or(const RawValue &a, const RawValue &b);
    RawValue int_xor(const RawValue &a, const RawValue &b);
    RawValue int_not(const RawValue &a);
    RawValue int_left_shift(const RawValue &a, const RawValue &b);
    RawValue int_right_shift(const RawValue &a, const RawValue &b);
    RawValue boolean_and(const RawValue &a, const RawValue &b);
    RawValue boolean_or(const RawValue &a, const RawValue &b);
    RawValue boolean_not(const RawValue &a);

    RawValue complex_equal(const RawObject &a, const RawObject &b);
    RawValue complex_not_equal(const RawObject &a, const RawObject &b);
    RawObject complex_add(const RawObject &a, const RawObject &b);
    RawObject complex_sub(const RawObject &a, const RawObject &b);
    RawObject complex_mul(const RawObject &a, const RawObject &b);
    RawObject complex_div(const RawObject &a, const RawObject &b);
    RawObject complex_exp(const RawObject &a);
    RawObject complex_neg(const RawObject &a);
}

#endif // VL_TYPES_H
