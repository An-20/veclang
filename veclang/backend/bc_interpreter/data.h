#include <cstdint>


struct VlMat2 {
    float data[4];
};

struct VlMat3 {
    float data[9];
};

struct VlMat4 {
    float data[16];
};

struct VlVec2 {
    float x, y;
};

struct VlVec3 {
    float x, y, z;
};

struct VlVec4 {
    float x, y, z, w;
};

struct VlComplex {
    float real, imag;
};

union VlValue {
    int32_t i;
    float f;
    bool b;
};

VlValue add(const VlValue& a, const VlValue& b) {
    VlValue result;
    result.f = a.f + b.f;
    return result;
}

VlValue subtract(const VlValue& a, const VlValue& b) {
    VlValue result;
    result.f = a.f - b.f;
    return result;
}

VlValue multiply(const VlValue& a, const VlValue& b) {
    VlValue result;
    result.f = a.f * b.f;
    return result;
}

#define DEFINE_OPERATION(name, op) \
VlValue name(const VlValue& a, const VlValue& b) { \
    VlValue result; \
    result.f = a.f op b.f; \
    return result; \
}

DEFINE_OPERATION(add, +)
DEFINE_OPERATION(subtract, -)
DEFINE_OPERATION(multiply, *)
DEFINE_OPERATION(divide, /)