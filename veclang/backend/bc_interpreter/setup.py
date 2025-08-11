from setuptools import setup, Extension
import pybind11
import sys

ext_modules = [
    Extension(
        "_bc_interpreter_core",
        [
            "bc_interpreter_bindings.cpp",
            "vl_builtins.cpp",
            "vl_interpreter.cpp",
            "vl_program.cpp",
            "vl_types_obj.cpp",
            "vl_types_val.cpp",
            "../bc_common/cpp/vl_sedf.cpp",
        ],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=(
            ["/std:c++17"] if sys.platform == "win32" else ["-std=c++17"]
        ),
    ),
]

setup(
    name="_bc_interpreter_core",
    ext_modules=ext_modules,
)
