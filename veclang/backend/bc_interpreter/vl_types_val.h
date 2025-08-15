#ifndef VL_TYPES_VAL_H
#define VL_TYPES_VAL_H

#include <cstdint>
#include <cstring>
#include <cmath>
#include <stdexcept>

namespace vl_types
{
    struct RawValue
    {
        uint64_t bits;
        RawValue() : bits(0) {}
    };

    inline RawValue null()
    {
        RawValue value;
        value.bits = 0;
        return value;
    }

    inline RawValue int_to_rv(int64_t value)
    {
        RawValue rv;
        rv.bits = static_cast<uint64_t>(value);
        return rv;
    }

    inline RawValue bool_to_rv(bool value)
    {
        RawValue rv;
        rv.bits = value ? 1 : 0;
        return rv;
    }

    inline RawValue double_to_rv(double value)
    {
        RawValue rv;
        std::memcpy(&rv.bits, &value, sizeof(double));
        return rv;
    }

    inline int64_t rv_to_int(const RawValue &rv)
    {
        return static_cast<int64_t>(rv.bits);
    }

    inline bool rv_to_bool(const RawValue &rv)
    {
        return rv.bits != 0;
    }

    inline double rv_to_double(const RawValue &rv)
    {
        double value;
        std::memcpy(&value, &rv.bits, sizeof(double));
        return value;
    }

    RawValue int_equal(const RawValue &a, const RawValue &b);
    RawValue int_not_equal(const RawValue &a, const RawValue &b);
    RawValue int_greater(const RawValue &a, const RawValue &b);
    RawValue int_greater_or_equal(const RawValue &a, const RawValue &b);
    RawValue int_less(const RawValue &a, const RawValue &b);
    RawValue int_less_or_equal(const RawValue &a, const RawValue &b);
    RawValue int_add(const RawValue &a, const RawValue &b);
    RawValue int_sub(const RawValue &a, const RawValue &b);
    RawValue int_mul(const RawValue &a, const RawValue &b);
    RawValue int_div(const RawValue &a, const RawValue &b);
    RawValue int_mod(const RawValue &a, const RawValue &b);
    RawValue int_pow(const RawValue &a, const RawValue &b);
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

    RawValue real_equal(const RawValue &a, const RawValue &b);
    RawValue real_not_equal(const RawValue &a, const RawValue &b);
    RawValue real_greater(const RawValue &a, const RawValue &b);
    RawValue real_greater_or_equal(const RawValue &a, const RawValue &b);
    RawValue real_less(const RawValue &a, const RawValue &b);
    RawValue real_less_or_equal(const RawValue &a, const RawValue &b);
    RawValue real_add(const RawValue &a, const RawValue &b);
    RawValue real_sub(const RawValue &a, const RawValue &b);
    RawValue real_mul(const RawValue &a, const RawValue &b);
    RawValue real_div(const RawValue &a, const RawValue &b);
    RawValue real_mod(const RawValue &a, const RawValue &b);
    RawValue real_pow(const RawValue &a, const RawValue &b);
    RawValue real_neg(const RawValue &a);

}

#endif // VL_TYPES_VAL_H
