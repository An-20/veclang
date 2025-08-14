#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <iostream>
#include <cstdint>
#include <vector>
#include <utility>
#include <streambuf>
#include <chrono>
#include <algorithm>

#include "vl_types_val.h"
#include "vl_types_obj.h"
#include "vl_interpreter.h"
#include "../bc_common/cpp/vl_sedf.h"

namespace py = pybind11;

class InterpreterWrapper
{
public:
    InterpreterWrapper(py::bytes program_bytes)
    {
        std::string program_bytes_str = program_bytes.cast<std::string>();
        vl_sedf::VlProgram program = vl_sedf::loadb(
            std::vector<uint8_t>(program_bytes_str.begin(), program_bytes_str.end()));
        interpreter = vl_interpreter::Interpreter(program);
    }

    void interpret_program()
    {
        interpreter.interpret_program();
    }

    py::object interpret_fn(py::int_ fn_idx, py::list arguments, py::int_ return_type_code)
    {
        using std::chrono::duration;
        using std::chrono::duration_cast;
        using std::chrono::high_resolution_clock;
        using std::chrono::milliseconds;

        std::vector<vl_types::RawValue> value_params;
        std::vector<vl_types::RawObject> object_params;

        for (size_t i = 0; i < arguments.size(); ++i)
        {
            py::handle obj = arguments[i];

            if (py::isinstance<py::bool_>(obj))
            {
                bool val = obj.cast<bool>();
                value_params.push_back(vl_types::bool_to_rv(val));
            }
            else if (py::isinstance<py::int_>(obj))
            {
                long val = obj.cast<int64_t>();
                value_params.push_back(vl_types::int_to_rv(val));
            }
            else if (py::isinstance<py::float_>(obj))
            {
                double val = obj.cast<double>();
                value_params.push_back(vl_types::double_to_rv(val));
            }
            else if (PyComplex_Check(obj.ptr()))
            {
                std::complex<double> val = obj.cast<std::complex<double>>();
                vl_types::VlComplex vl_val;
                vl_val.real = val.real();
                vl_val.imag = val.imag();
                object_params.push_back(vl_types::complex_to_ro(vl_val));
            }
            else
            {
                std::cout << "arg " << i << " was unknown type\n";
            }
        }
        bool returns_val = return_type_code.cast<uint8_t>() <= 2;

        // auto t1 = high_resolution_clock::now();

        auto [rv, ro] = interpreter.interpret_fn(fn_idx.cast<int>(), value_params, object_params, returns_val);
        // auto t2 = high_resolution_clock::now();

        // /* Getting number of milliseconds as an integer. */
        // auto ms_int = duration_cast<milliseconds>(t2 - t1);

        // /* Getting number of milliseconds as a double. */
        // duration<double, std::milli> ms_double = t2 - t1;

        // std::cout << ms_double.count() << "ms for actual fn call\n";

        switch (return_type_code.cast<uint8_t>())
        {
        case 0:
            return py::int_(vl_types::rv_to_int(rv));
        }
    }

private:
    vl_interpreter::Interpreter interpreter;
};

PYBIND11_MODULE(_bc_interpreter_core, m)
{
    m.doc() = "Example module for passing arbitrary args to C++ and returning mixed objects";

    py::class_<InterpreterWrapper>(m, "Interpreter")
        .def(py::init<py::bytes>())
        .def("interpret_fn", &InterpreterWrapper::interpret_fn)
        .def("interpret_program", &InterpreterWrapper::interpret_program);
}
