import math

from veclang.midend.vl_core import VlReal
from veclang.midend.vl_stdlib.vl_stdlib_types import (
    StdlibFnParam,
    StdlibFunction,
    StdlibConstexpr,
    StdlibNamespace,
)


VlMathStdlib = StdlibNamespace(
    "math",
    "Standard math library functions for Veclang, often a thin wrapper over corresponding cmath functions.",
    [
        StdlibFunction(
            "abs",
            "Returns the absolute value of a real",
            [StdlibFnParam("x", "real")],
            "real",
            0x00F0,
        ),
        StdlibFunction(
            "absi",
            "Returns the absolute value of an int",
            [StdlibFnParam("x", "int")],
            "int",
            0x00F1,
        ),
        StdlibFunction(
            "intdiv",
            "Returns the quotient of numer divided by denom",
            [StdlibFnParam("numer", "int"), StdlibFnParam("denom", "int")],
            "int",
            0x00F2,
        ),
        StdlibFunction(
            "intrem",
            "Returns the remainder of numer divided by denom",
            [StdlibFnParam("numer", "int"), StdlibFnParam("denom", "int")],
            "int",
            0x00F3,
        ),
        StdlibFunction(
            "min",
            "Returns the minimum of two reals",
            [StdlibFnParam("a", "real"), StdlibFnParam("b", "real")],
            "real",
            0x00F4,
        ),
        StdlibFunction(
            "mini",
            "Returns the minimum of two ints",
            [StdlibFnParam("a", "int"), StdlibFnParam("b", "int")],
            "int",
            0x00F5,
        ),
        StdlibFunction(
            "max",
            "Returns the maximum of two reals",
            [StdlibFnParam("a", "real"), StdlibFnParam("b", "real")],
            "real",
            0x00F6,
        ),
        StdlibFunction(
            "maxi",
            "Returns the maximum of two ints",
            [StdlibFnParam("a", "int"), StdlibFnParam("b", "int")],
            "int",
            0x00F7,
        ),
        StdlibFunction(
            "sin",
            "Returns the sine of an angle, in radians",
            [StdlibFnParam("x", "real")],
            "real",
            0x00F8,
        ),
    ],
    [
        StdlibConstexpr(
            "E",
            "Euler's number, equal to 2.71828...",
            VlReal(math.e),
        ),
        StdlibConstexpr(
            "PI",
            "Pi, equal to 3.14159...",
            VlReal(math.pi),
        ),
    ],
)
