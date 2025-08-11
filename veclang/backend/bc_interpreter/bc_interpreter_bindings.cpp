#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <iostream>
#include <cstdint>
#include <vector>
#include <utility>
#include <streambuf>

#include "vl_types_val.h"
#include "vl_types_obj.h"
#include "vl_interpreter.h"
#include "../bc_common/cpp/vl_sedf.h"

namespace py = pybind11;

py::list interpret_fn(py::bytes program_bytes, py::list arguments, py::int_ return_type_code)
{
    std::cout << "hjere!" << std::endl;
    std::string program_bytes_str = program_bytes.cast<std::string>();
    std::cout << "hjere2!" << std::endl;

    vl_sedf::VlProgram program = vl_sedf::loadb(std::vector<uint8_t>(program_bytes_str.begin(), program_bytes_str.end()));
    std::cout << "hjere3!" << std::endl;

    std::vector<vl_types::RawValue> value_params;
    std::vector<vl_types::RawObject> object_params;

    for (size_t i = 0; i < arguments.size(); ++i)
    {
        py::handle obj = arguments[i];
        std::cout << "hjere4!" << std::endl;

        if (py::isinstance<py::bool_>(obj))
        {
            bool val = obj.cast<bool>();
            std::cout << "arg " << i << " was bool with value "
                      << std::boolalpha << val << "\n";
            value_params.push_back(vl_types::bool_to_rv(val));
        }
        else if (py::isinstance<py::int_>(obj))
        {
            long val = obj.cast<long>();
            std::cout << "arg " << i << " was int with value " << val << "\n";
            value_params.push_back(vl_types::int_to_rv(val));
        }
        else if (py::isinstance<py::float_>(obj))
        {
            double val = obj.cast<double>();
            std::cout << "arg " << i << " was float with value " << val << "\n";
            value_params.push_back(vl_types::float_to_rv(val));
        }
        else if (PyComplex_Check(obj.ptr()))
        {
            std::complex<double> val = obj.cast<std::complex<double>>();
            std::cout << "arg " << i << " was complex with value ("
                      << val.real() << " + " << val.imag() << "i)\n";
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
    std::cout << "hjere5!" << std::endl;

    bool returns_val = return_type_code.cast<uint8_t>() <= 2;

    std::stringstream buffer;
    std::streambuf *old = std::cout.rdbuf(buffer.rdbuf());

    vl_interpreter::Interpreter interpreter;
    auto [rv, ro] = interpreter.interpret_fn(program, value_params, object_params, returns_val);

    py::list ret;
    std::string text = buffer.str();
    ret.append(text);

    switch (return_type_code.cast<uint8_t>())
    {
    case 0:
        ret.append(vl_types::rv_to_int(rv));
        break;
    }
    return ret;
}

PYBIND11_MODULE(_bc_interpreter_core, m)
{
    m.doc() = "Example module for passing arbitrary args to C++ and returning mixed objects";
    m.def("interpret_fn", &interpret_fn, "Process arbitrary Python arguments");
}
