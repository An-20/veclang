#include "vl_types_val.h"

#include <cstdint>
#include <cstring>
#include <cmath>
#include <stdexcept>

namespace vl_types
{
    RawValue int_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_int(a) == rv_to_int(b));
    }

    RawValue int_not_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_int(a) != rv_to_int(b));
    }

    RawValue int_greater(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_int(a) > rv_to_int(b));
    }

    RawValue int_greater_or_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_int(a) >= rv_to_int(b));
    }

    RawValue int_less(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_int(a) < rv_to_int(b));
    }

    RawValue int_less_or_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_int(a) <= rv_to_int(b));
    }

    RawValue int_add(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x + y);
    }

    RawValue int_sub(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x - y);
    }

    RawValue int_mul(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x * y);
    }

    RawValue int_div(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        if (y == 0)
        {
            throw std::runtime_error("Division by zero");
        }
        double result = static_cast<double>(x) / static_cast<double>(y);
        return double_to_rv(result);
    }

    RawValue int_mod(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        if (y == 0)
        {
            throw std::runtime_error("Division by zero");
        }
        return int_to_rv(x % y);
    }

    RawValue int_pow(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return double_to_rv(std::pow(x, y));
    }

    RawValue int_neg(const RawValue &a)
    {
        int64_t x = rv_to_int(a);
        return int_to_rv(-x);
    }

    RawValue int_and(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x & y);
    }

    RawValue int_or(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x | y);
    }

    RawValue int_xor(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x ^ y);
    }

    RawValue int_not(const RawValue &a)
    {
        int64_t x = rv_to_int(a);
        return int_to_rv(~x);
    }

    RawValue int_left_shift(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x << y);
    }

    RawValue int_right_shift(const RawValue &a, const RawValue &b)
    {
        int64_t x = rv_to_int(a);
        int64_t y = rv_to_int(b);
        return int_to_rv(x >> y);
    }

    RawValue boolean_and(const RawValue &a, const RawValue &b)
    {
        bool x = rv_to_bool(a);
        bool y = rv_to_bool(b);
        return bool_to_rv(x && y);
    }

    RawValue boolean_or(const RawValue &a, const RawValue &b)
    {
        bool x = rv_to_bool(a);
        bool y = rv_to_bool(b);
        return bool_to_rv(x || y);
    }

    RawValue boolean_not(const RawValue &a)
    {
        bool x = rv_to_bool(a);
        return bool_to_rv(!x);
    }

    RawValue real_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_double(a) == rv_to_double(b));
    }

    RawValue real_not_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_double(a) != rv_to_double(b));
    }

    RawValue real_greater(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_double(a) > rv_to_double(b));
    }

    RawValue real_greater_or_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_double(a) >= rv_to_double(b));
    }

    RawValue real_less(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_double(a) < rv_to_double(b));
    }

    RawValue real_less_or_equal(const RawValue &a, const RawValue &b)
    {
        return bool_to_rv(rv_to_double(a) <= rv_to_double(b));
    }

    RawValue real_add(const RawValue &a, const RawValue &b)
    {
        double x = rv_to_double(a);
        double y = rv_to_double(b);
        return double_to_rv(x + y);
    }

    RawValue real_sub(const RawValue &a, const RawValue &b)
    {
        double x = rv_to_double(a);
        double y = rv_to_double(b);
        return double_to_rv(x - y);
    }

    RawValue real_mul(const RawValue &a, const RawValue &b)
    {
        double x = rv_to_double(a);
        double y = rv_to_double(b);
        return double_to_rv(x * y);
    }

    RawValue real_div(const RawValue &a, const RawValue &b)
    {
        double x = rv_to_double(a);
        double y = rv_to_double(b);
        if (y == 0.0f)
        {
            throw std::runtime_error("Division by zero");
        }
        return double_to_rv(x / y);
    }

    RawValue real_mod(const RawValue &a, const RawValue &b)
    {
        double x = rv_to_double(a);
        double y = rv_to_double(b);
        if (y == 0.0f)
        {
            throw std::runtime_error("Division by zero");
        }
        return double_to_rv(std::fmod(x, y));
    }

    RawValue real_pow(const RawValue &a, const RawValue &b)
    {
        double x = rv_to_double(a);
        double y = rv_to_double(b);
        return double_to_rv(std::pow(x, y));
    }

    RawValue real_neg(const RawValue &a)
    {
        double x = rv_to_double(a);
        return double_to_rv(-x);
    }

}
