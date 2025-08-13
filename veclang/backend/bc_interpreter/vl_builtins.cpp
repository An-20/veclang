#include "vl_builtins.h"

#include <iostream>
#include <cstdint>

namespace vl_builtins
{
    void bi_0x0000(BuiltinsDelegate &delegate)
    {
        // builtin for printing an int
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << vl_types::rv_to_int(value) << "\n";
        delegate.return_val(value);
    }

    void bi_0x0001(BuiltinsDelegate &delegate)
    {
        // builtin for printing a real
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << vl_types::rv_to_double(value) << "\n";
        delegate.return_val(value);
    }

    void bi_0x1000(BuiltinsDelegate &delegate)
    {
        // builtin for casting an int to a real
        vl_types::RawValue value = delegate.get_val_argument();
        int64_t value_int = vl_types::rv_to_int(value);
        double value_double = (double)value_int;
        delegate.return_val(vl_types::double_to_rv(value_double));
    }

    void bi_0x1001(BuiltinsDelegate &delegate)
    {
        // builtin for casting an int to a complex
        vl_types::RawValue value = delegate.get_val_argument();
        int64_t value_int = vl_types::rv_to_int(value);
        vl_types::VlComplex complex;
        complex.real = (double)value_int;
        complex.imag = 0.0f;
        delegate.return_obj(vl_types::complex_to_ro(complex));
    }

    void bi_0x1100(BuiltinsDelegate &delegate)
    {
        // builtin for casting a real to a complex
        vl_types::RawValue value = delegate.get_val_argument();
        double value_double = vl_types::rv_to_double(value);
        vl_types::VlComplex complex;
        complex.real = value_double;
        complex.imag = 0.0f;
        delegate.return_obj(vl_types::complex_to_ro(complex));
    }

    void bi_0x1200(BuiltinsDelegate &delegate)
    {
        // builtin for getting the real component of a complex
        vl_types::RawObject object = delegate.get_obj_argument();
        vl_types::VlComplex complex = vl_types::ro_to_complex(object);
        double real_component = complex.real;
        delegate.return_val(vl_types::double_to_rv(real_component));
    }

    void bi_0x1201(BuiltinsDelegate &delegate)
    {
        // builtin for getting the imaginary component of a complex
        vl_types::RawObject object = delegate.get_obj_argument();
        vl_types::VlComplex complex = vl_types::ro_to_complex(object);
        double imag_component = complex.imag;
        delegate.return_val(vl_types::double_to_rv(imag_component));
    }

    void bi_0x1300(BuiltinsDelegate &delegate)
    {
        // builtin for constructing a vec2 from 2 reals
        double y = vl_types::rv_to_double(delegate.get_val_argument());
        double x = vl_types::rv_to_double(delegate.get_val_argument());
        vl_types::VlVec2 vec;
        vec.x = x;
        vec.y = y;
        delegate.return_obj(vl_types::vec2_to_ro(vec));
    }

    void bi_0x1301(BuiltinsDelegate &delegate)
    {
        // builtin for constructing a vec3 from 3 reals
        double z = vl_types::rv_to_double(delegate.get_val_argument());
        double y = vl_types::rv_to_double(delegate.get_val_argument());
        double x = vl_types::rv_to_double(delegate.get_val_argument());
        vl_types::VlVec3 vec;
        vec.x = x;
        vec.y = y;
        vec.z = z;
        delegate.return_obj(vl_types::vec3_to_ro(vec));
    }

    void bi_0x1302(BuiltinsDelegate &delegate)
    {
        // builtin for constructing a vec4 from 4 reals
        double z = vl_types::rv_to_double(delegate.get_val_argument());
        double y = vl_types::rv_to_double(delegate.get_val_argument());
        double x = vl_types::rv_to_double(delegate.get_val_argument());
        double w = vl_types::rv_to_double(delegate.get_val_argument());
        vl_types::VlVec4 vec;
        vec.w = w;
        vec.x = x;
        vec.y = y;
        vec.z = z;
        delegate.return_obj(vl_types::vec4_to_ro(vec));
    }

    void call_builtin(BuiltinsDelegate delegate, uint16_t builtin_id)
    {
        // std::cout << "Calling builtin with ID: " << static_cast<int>(builtin_id) << "\n";
        switch (builtin_id)
        {
        case 0x0000:
            bi_0x0000(delegate);
            break;
        case 0x0001:
            bi_0x0001(delegate);
            break;
        case 0x1000:
            bi_0x1000(delegate);
            break;
        case 0x1001:
            bi_0x1001(delegate);
            break;
        case 0x1100:
            bi_0x1100(delegate);
            break;
        case 0x1200:
            bi_0x1200(delegate);
            break;
        case 0x1201:
            bi_0x1201(delegate);
            break;
        case 0x1300:
            bi_0x1300(delegate);
            break;
        case 0x1301:
            bi_0x1301(delegate);
            break;
        case 0x1302:
            bi_0x1302(delegate);
            break;
        default:
            std::cerr << "Unknown builtin ID: " << static_cast<int>(builtin_id) << "\n";
            break;
        }
    }
}
