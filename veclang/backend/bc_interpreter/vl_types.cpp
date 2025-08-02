#include "vl_types.h"

#include <cstdint>
#include <cstring>
#include <cmath>
#include <stdexcept>

namespace vl_types
{
    RawValue int_add(const RawValue &a, const RawValue &b)
    {
        int32_t x = rv_to_int(a);
        int32_t y = rv_to_int(b);
        return int_to_rv(x + y);
    }

    RawValue complex_equal(const RawObject &a, const RawObject &b)
    {
        bool result = (a.bits[0] == b.bits[0] && a.bits[1] == b.bits[1]);
        return bool_to_rv(result);
    }

    RawValue complex_not_equal(const RawObject &a, const RawObject &b)
    {
        bool result = !(a.bits[0] == b.bits[0] && a.bits[1] == b.bits[1]);
        return bool_to_rv(result);
    }

    RawObject complex_add(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        result.real = x.real + y.real;
        result.imag = x.imag + y.imag;
        return complex_to_ro(result);
    }

    RawObject complex_sub(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        result.real = x.real - y.real;
        result.imag = x.imag - y.imag;
        return complex_to_ro(result);
    }

    RawObject complex_mul(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        result.real = x.real * y.real - x.imag * y.imag;
        result.imag = x.real * y.imag + x.imag * y.real;
        return complex_to_ro(result);
    }

    RawObject complex_div(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        float denom = y.real * y.real + y.imag * y.imag;
        if (denom == 0.0f)
            throw std::runtime_error("Division by zero in complex division");
        result.real = (x.real * y.real + x.imag * y.imag) / denom;
        result.imag = (x.imag * y.real - x.real * y.imag) / denom;
        return complex_to_ro(result);
    }

    RawObject complex_exp(const RawObject &a)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex result;
        float exp_real = std::exp(x.real);
        result.real = exp_real * std::cos(x.imag);
        result.imag = exp_real * std::sin(x.imag);
        return complex_to_ro(result);
    }

    RawObject complex_neg(const RawObject &a)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex result;
        result.real = -x.real;
        result.imag = -x.imag;
        return complex_to_ro(result);
    }
}
