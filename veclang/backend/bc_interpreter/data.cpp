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
    int i;
    float f;
    bool b;
};
