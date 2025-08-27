from veclang.midend.vl_stdlib.vl_stdlib_types import (
    StdlibFnParam,
    StdlibFunction,
    StdlibNamespace,
)


VlCoreStdlib = StdlibNamespace(
    "core",
    "Core standard library for Veclang, automatically imported into the global namespace",
    [
        StdlibFunction(
            "print",
            "Prints an integer",
            [StdlibFnParam("x", "int")],
            "null",
            0x0000,
        ),
        StdlibFunction(
            "print",
            "Prints a real",
            [StdlibFnParam("x", "real")],
            "null",
            0x0001,
        ),
        StdlibFunction(
            "print",
            "Prints a complex",
            [StdlibFnParam("x", "complex")],
            "null",
            0x0002,
        ),
        StdlibFunction(
            "print",
            "Prints a str",
            [StdlibFnParam("x", "str")],
            "null",
            0x0003,
        ),
    ],
    [],
)
