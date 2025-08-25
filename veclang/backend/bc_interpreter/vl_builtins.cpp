#include "vl_builtins.h"

#include <cmath>
#include <iostream>
#include <cstdint>

namespace vl_builtins
{
    void bi_0x0000(BuiltinsDelegate &delegate)
    {
        // builtin for printing an int
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << vl_types::rv_to_int(value) << "\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0001(BuiltinsDelegate &delegate)
    {
        // builtin for printing a real
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << vl_types::rv_to_double(value) << "\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0002(BuiltinsDelegate &delegate)
    {
        // builtin for printing a complex
        vl_types::RawObject object = delegate.get_obj_argument();
        vl_types::VlComplex complex = vl_types::ro_to_complex(object);
        std::cout << complex.real << " + " << complex.imag << "i\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0010(BuiltinsDelegate &delegate)
    {
        // repl::repl_printi
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << vl_types::rv_to_int(value) << ": int\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0011(BuiltinsDelegate &delegate)
    {
        // repl::repl_printb
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << (vl_types::rv_to_bool(value) ? "true" : "false") << ": bool\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0012(BuiltinsDelegate &delegate)
    {
        // repl::repl_printr
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << vl_types::rv_to_double(value) << ": real\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0013(BuiltinsDelegate &delegate)
    {
        // repl::repl_printc
        vl_types::RawObject object = delegate.get_obj_argument();
        vl_types::VlComplex complex = vl_types::ro_to_complex(object);
        std::cout << complex.real << "+" << complex.imag << "i: complex\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0014(BuiltinsDelegate &delegate)
    {
        // repl::repl_printv2
        vl_types::RawObject object = delegate.get_obj_argument();
        vl_types::VlVec2 vec2 = vl_types::ro_to_vec2(object);
        std::cout << "[" << vec2.x << "," << vec2.y << "]: vec2\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0015(BuiltinsDelegate &delegate)
    {
        // repl::repl_printv3
        vl_types::RawObject object = delegate.get_obj_argument();
        vl_types::VlVec3 vec3 = vl_types::ro_to_vec3(object);
        std::cout << "[" << vec3.x << "," << vec3.y << "," << vec3.z << "]: vec3\n";
        delegate.return_val(vl_types::null_value);
    }

    void bi_0x0016(BuiltinsDelegate &delegate)
    {
        // repl::repl_printv4
        vl_types::RawObject object = delegate.get_obj_argument();
        vl_types::VlVec4 vec4 = vl_types::ro_to_vec4(object);
        std::cout << "[" << vec4.x << "," << vec4.y << "," << vec4.z << "," << vec4.w << "]: vec4\n";
        delegate.return_val(vl_types::null_value);
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

    void bi_0x00f8(BuiltinsDelegate &delegate)
    {
        // builtin for sin
        double x = vl_types::rv_to_double(delegate.get_val_argument());
        delegate.return_val(vl_types::double_to_rv(std::sin(x)));
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
        case 0x0002:
            bi_0x0002(delegate);
            break;
        case 0x0010:
            bi_0x0010(delegate);
            break;
        case 0x0011:
            bi_0x0011(delegate);
            break;
        case 0x0012:
            bi_0x0012(delegate);
            break;
        case 0x0013:
            bi_0x0013(delegate);
            break;
        case 0x0014:
            bi_0x0014(delegate);
            break;
        case 0x0015:
            bi_0x0015(delegate);
            break;
        case 0x0016:
            bi_0x0016(delegate);
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
        case 0x00f8:
            bi_0x00f8(delegate);
            break;
        default:
            std::cerr << "Unknown builtin ID: " << static_cast<int>(builtin_id) << "\n";
            break;
        }
    }
}
