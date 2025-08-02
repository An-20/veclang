#include "vl_types_val.h"

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

}
