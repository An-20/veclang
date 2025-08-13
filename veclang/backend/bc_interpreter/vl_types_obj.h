#ifndef VL_TYPES_OBJ_H
#define VL_TYPES_OBJ_H

#include <cstdint>
#include <cstring>
#include <complex>
#include "vl_types_val.h"

namespace vl_types
{
    struct VlComplex
    {
        double real, imag;
    };

    struct VlVec2
    {
        double x, y;
    };

    struct VlVec3
    {
        double x, y, z;
    };

    struct VlVec4
    {
        double x, y, z, w;
    };

    struct VlMat2
    {
        double data[4];
    };

    struct VlMat3
    {
        double data[9];
    };

    struct VlMat4
    {
        double data[16];
    };

    struct RawObject
    {
        uint64_t bits[16];
    };

    inline RawObject complex_to_ro(const VlComplex &complex)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &complex.real, sizeof(double));
        std::memcpy(&obj.bits[1], &complex.imag, sizeof(double));
        return obj;
    }

    inline RawObject vec2_to_ro(const VlVec2 &vec)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &vec.x, sizeof(double));
        std::memcpy(&obj.bits[1], &vec.y, sizeof(double));
        return obj;
    }

    inline RawObject vec3_to_ro(const VlVec3 &vec)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &vec.x, sizeof(double));
        std::memcpy(&obj.bits[1], &vec.y, sizeof(double));
        std::memcpy(&obj.bits[2], &vec.z, sizeof(double));
        return obj;
    }

    inline RawObject vec4_to_ro(const VlVec4 &vec)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &vec.x, sizeof(double));
        std::memcpy(&obj.bits[1], &vec.y, sizeof(double));
        std::memcpy(&obj.bits[2], &vec.z, sizeof(double));
        std::memcpy(&obj.bits[3], &vec.w, sizeof(double));
        return obj;
    }

    inline RawObject mat2_to_ro(const VlMat2 &mat)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &mat.data[0], sizeof(double) * 4);
        return obj;
    }

    inline RawObject mat3_to_ro(const VlMat3 &mat)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &mat.data[0], sizeof(double) * 9);
        return obj;
    }

    inline RawObject mat4_to_ro(const VlMat4 &mat)
    {
        RawObject obj;
        std::memcpy(&obj.bits[0], &mat.data[0], sizeof(double) * 16);
        return obj;
    }

    inline VlComplex ro_to_complex(const RawObject &ro)
    {
        double real, imag;
        std::memcpy(&real, &ro.bits[0], sizeof(double));
        std::memcpy(&imag, &ro.bits[1], sizeof(double));
        VlComplex complex;
        complex.real = real;
        complex.imag = imag;
        return complex;
    }

    inline VlVec2 ro_to_vec2(const RawObject &ro)
    {
        VlVec2 vec;
        std::memcpy(&vec.x, &ro.bits[0], sizeof(double));
        std::memcpy(&vec.y, &ro.bits[1], sizeof(double));
        return vec;
    }

    inline VlVec3 ro_to_vec3(const RawObject &ro)
    {
        VlVec3 vec;
        std::memcpy(&vec.x, &ro.bits[0], sizeof(double));
        std::memcpy(&vec.y, &ro.bits[1], sizeof(double));
        std::memcpy(&vec.z, &ro.bits[2], sizeof(double));
        return vec;
    }

    inline VlVec4 ro_to_vec4(const RawObject &ro)
    {
        VlVec4 vec;
        std::memcpy(&vec.x, &ro.bits[0], sizeof(double));
        std::memcpy(&vec.y, &ro.bits[1], sizeof(double));
        std::memcpy(&vec.z, &ro.bits[2], sizeof(double));
        std::memcpy(&vec.w, &ro.bits[3], sizeof(double));
        return vec;
    }

    inline VlMat2 ro_to_mat2(const RawObject &ro)
    {
        VlMat2 mat;
        std::memcpy(&mat.data[0], &ro.bits[0], sizeof(double) * 4);
        return mat;
    }

    inline VlMat3 ro_to_mat3(const RawObject &ro)
    {
        VlMat3 mat;
        std::memcpy(&mat.data[0], &ro.bits[0], sizeof(double) * 9);
        return mat;
    }

    inline VlMat4 ro_to_mat4(const RawObject &ro)
    {
        VlMat4 mat;
        std::memcpy(&mat.data[0], &ro.bits[0], sizeof(double) * 16);
        return mat;
    }

    RawValue complex_equal(const RawObject &a, const RawObject &b);
    RawValue complex_not_equal(const RawObject &a, const RawObject &b);
    RawObject complex_add(const RawObject &a, const RawObject &b);
    RawObject complex_sub(const RawObject &a, const RawObject &b);
    RawObject complex_mul(const RawObject &a, const RawObject &b);
    RawObject complex_div(const RawObject &a, const RawObject &b);
    RawObject complex_pow(const RawObject &a, const RawObject &b);
    RawObject complex_neg(const RawObject &a);

    RawObject vector_add(const RawObject &a, const RawObject &b);
    RawObject vector_sub(const RawObject &a, const RawObject &b);
    RawObject vector_mul(const RawObject &a, const RawObject &b);
    RawObject vector_div(const RawObject &a, const RawObject &b);
    RawObject vector_neg(const RawObject &a);
    RawObject vector_scl(const RawObject &a, const RawValue &b);
    RawValue vector_dot(const RawObject &a, const RawObject &b);
    RawObject vector_cross(const RawObject &a, const RawObject &b);
    RawObject matrix_add(const RawObject &a, const RawObject &b);
    RawObject matrix_sub(const RawObject &a, const RawObject &b);
    RawObject matrix_mul(const RawObject &a, const RawObject &b);
    RawObject matrix_neg(const RawObject &a);
    RawObject matrix_scl(const RawObject &a, const RawValue &b);

}

#endif // VL_TYPES_OBJ_H
