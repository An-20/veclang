#include <cstdint>
#include <cstring>
#include <cmath>

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

    VlComplex ro_to_complex(const RawObject &ro)
    {
        VlComplex complex;
        std::memcpy(&complex, ro.bits, sizeof(VlComplex));
        return complex;
    }

    bool complex_equal(const RawObject &a, const RawObject &b)
    {
        return a.bits[0] == b.bits[0] && a.bits[1] == b.bits[1];
    }

    bool complex_not_equal(const RawObject &a, const RawObject &b)
    {
        return !complex_equal(a, b);
    }

    VlComplex complex_add(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        result.real = x.real + y.real;
        result.imag = x.imag + y.imag;
        return result;
    }

    VlComplex complex_sub(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        result.real = x.real - y.real;
        result.imag = x.imag - y.imag;
        return result;
    }

    VlComplex complex_mul(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        result.real = x.real * y.real - x.imag * y.imag;
        result.imag = x.real * y.imag + x.imag * y.real;
        return result;
    }

    VlComplex complex_div(const RawObject &a, const RawObject &b)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex y = ro_to_complex(b);
        VlComplex result;
        float denom = y.real * y.real + y.imag * y.imag;
        if (denom == 0.0f)
            throw std::runtime_error("Division by zero in complex division");
        result.real = (x.real * y.real + x.imag * y.imag) / denom;
        result.imag = (x.imag * y.real - x.real * y.imag) / denom;
        return result;
    }

    VlComplex complex_exp(const RawObject &a)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex result;
        float exp_real = std::exp(x.real);
        result.real = exp_real * std::cos(x.imag);
        result.imag = exp_real * std::sin(x.imag);
        return result;
    }

    VlComplex complex_neg(const RawObject &a)
    {
        VlComplex x = ro_to_complex(a);
        VlComplex result;
        result.real = -x.real;
        result.imag = -x.imag;
        return result;
    }
}
