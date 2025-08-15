import timeit

from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl


PROGRAM_STR = """
fn sum(n: int) -> int {
    let s: int = 0;
    for (x: int in 0:n) {
        s += x;
    }
    return s;
}
"""
compiled = compile_vl(PROGRAM_STR)
interpreter = Interpreter(compiled)


def sum_veclang(n: int):
    return interpreter.interpret_fn(0, [n])


def sum_python(n: int):
    s = 0
    for x in range(n):
        s += x
    return s


print(sum_veclang(100000))
print(sum_python(100000))
print("Veclang: ", timeit.timeit("sum_veclang(1000000)", globals=globals(), number=10))
print("Python: ", timeit.timeit("sum_python(1000000)", globals=globals(), number=10))
