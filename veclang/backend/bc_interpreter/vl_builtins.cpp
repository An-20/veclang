#include "vl_builtins.h"

#include <iostream>
#include <cstdint>

namespace vl_builtins
{
    void bi_0x0000(BuiltinsDelegate &delegate)
    {
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << "Value argument: " << vl_types::rv_to_int(value) << "\n";
        delegate.return_val(value);
    }

    void bi_0x0001(BuiltinsDelegate &delegate)
    {
        vl_types::RawValue value = delegate.get_val_argument();
        std::cout << "Value argument: " << vl_types::rv_to_float(value) << "\n";
        delegate.return_val(value);
    }

    void call_builtin(BuiltinsDelegate delegate, uint8_t builtin_id)
    {
        std::cout << "Calling builtin with ID: " << static_cast<int>(builtin_id) << "\n";
        switch (builtin_id)
        {
        case 0x0000:
            bi_0x0000(delegate);
            break;
        case 0x0001:
            bi_0x0001(delegate);
            break;
        default:
            std::cerr << "Unknown builtin ID: " << static_cast<int>(builtin_id) << "\n";
            break;
        }
    }
}
