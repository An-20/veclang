from veclang.midend.vl_stdlib.vl_stdlib_types import (
    StdlibFnParam,
    StdlibFunction,
    StdlibNamespace,
)


VlReplStdlib = StdlibNamespace(
    "repl",
    "Standard library for Veclang REPLs, automatically imported into the global namespace",
    [
        StdlibFunction(
            "repl_printi",
            "Prints an integer, in the format 'value: int'",
            [StdlibFnParam("x", "int")],
            "null",
            0x0010,
        ),
        StdlibFunction(
            "repl_printb",
            "Prints a bool, in the format 'value: bool'",
            [StdlibFnParam("x", "bool")],
            "null",
            0x0011,
        ),
        StdlibFunction(
            "repl_printr",
            "Prints a real, in the format 'value: real'",
            [StdlibFnParam("x", "real")],
            "null",
            0x0012,
        ),
        StdlibFunction(
            "repl_printc",
            "Prints a complex, in the format 'value: complex'",
            [StdlibFnParam("x", "complex")],
            "null",
            0x0013,
        ),
        StdlibFunction(
            "repl_printv2",
            "Prints a vec2, in the format 'value: vec2'",
            [StdlibFnParam("x", "vec2")],
            "null",
            0x0014,
        ),
        StdlibFunction(
            "repl_printv3",
            "Prints a vec3, in the format 'value: vec3'",
            [StdlibFnParam("x", "vec3")],
            "null",
            0x0015,
        ),
        StdlibFunction(
            "repl_printv4",
            "Prints a vec4, in the format 'value: vec4'",
            [StdlibFnParam("x", "vec4")],
            "null",
            0x0016,
        ),
        StdlibFunction(
            "repl_printm2",
            "Prints a mat2, in the format 'value: mat2'",
            [StdlibFnParam("x", "mat2")],
            "null",
            0x0017,
        ),
        StdlibFunction(
            "repl_printm3",
            "Prints a mat3, in the format 'value: mat3'",
            [StdlibFnParam("x", "mat3")],
            "null",
            0x0018,
        ),
        StdlibFunction(
            "repl_printm4",
            "Prints a mat4, in the format 'value: mat4'",
            [StdlibFnParam("x", "mat4")],
            "null",
            0x0019,
        ),
        StdlibFunction(
            "repl_prints",
            "Prints a str, in the format 'value: str'",
            [StdlibFnParam("x", "str")],
            "null",
            0x001F,
        ),
    ],
    [],
)
