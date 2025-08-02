#ifndef VL_BUILTINS_H
#define VL_BUILTINS_H

#include <cstdint>

#include "vl_types.h"
#include "vl_interpreter.h"

namespace vl_builtins
{
    class BuiltinsDelegate
    {
    public:
        BuiltinsDelegate(vl_interpreter::Interpreter &ref)
            : ref_(ref)
        {
            returned_ = false;
        }

        vl_types::RawValue get_val_argument()
        {
            if (ref_.value_stack.empty())
            {
                throw std::runtime_error("Value stack underflow");
            }
            vl_types::RawValue value = ref_.value_stack.top();
            ref_.value_stack.pop();
            return value;
        }

        vl_types::RawObject get_obj_argument()
        {
            if (ref_.object_stack.empty())
            {
                throw std::runtime_error("Object stack underflow");
            }
            vl_types::RawObject object = ref_.object_stack.top();
            ref_.object_stack.pop();
            return object;
        }

        void return_val(const vl_types::RawValue &value)
        {
            if (returned_)
            {
                throw std::runtime_error("Return value already set");
            }
            ref_.value_stack.push(value);
            returned_ = true;
        }

        void return_obj(const vl_types::RawObject &object)
        {
            if (returned_)
            {
                throw std::runtime_error("Return value already set");
            }
            ref_.object_stack.push(object);
            returned_ = true;
        }

        void assert_returned() const
        {
            if (!returned_)
            {
                throw std::runtime_error("No return value set");
            }
        }

    private:
        vl_interpreter::Interpreter &ref_;
        bool returned_ = false;
    };

    void call_builtin(BuiltinsDelegate delegate, uint8_t builtin_id);
}

#endif // VL_BUILTINS_H
