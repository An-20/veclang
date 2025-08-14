import timeit

from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir
from veclang.backend.bc_compiler.vl_emitter import emit
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_interpreter.bc_interpreter import interpret_fn, Interpreter
from veclang.common import CompilerFlags


COMPILER_FLAGS: CompilerFlags = CompilerFlags(64)


def compile_vl(program_str: str):
    parsed, diagnostics = parse(program_str, COMPILER_FLAGS)
    if diagnostics:
        raise ValueError(f"Error when parsing: {diagnostics}")
    print_ast(parsed)

    hir, diagnostics = lower(parsed, COMPILER_FLAGS)
    if diagnostics:
        raise ValueError(f"Error when lowering: {diagnostics}")
    print_hir(hir)

    bytecode, diagnostics = emit(hir, COMPILER_FLAGS)
    if diagnostics:
        raise ValueError(f"Error when emitting: {diagnostics}")
    print(disassemble_vl_program(bytecode))
    return bytecode


PROGRAM_STR = """
fn sum(n: int) -> int {
    let s: int = 0;
    for (_: int in 0:100000) {
        s = 0;
        for (x: int in 0:n) {
            s += x;
        }
    }
    return s;
}
"""
COMPILED = compile_vl(PROGRAM_STR)
INTERPRETER = Interpreter(COMPILED)


def sum_veclang(n: int):
    return INTERPRETER.interpret_fn(0, [n]).return_value


def sum_python(n: int):
    s = 0
    for x in range(n):
        s += x
    return s


print(sum_veclang(100000))
print(sum_python(100000))


print("Veclang: ", timeit.timeit("sum_veclang(100000)", globals=globals(), number=1))
print("Python: ", timeit.timeit("sum_python(100000)", globals=globals(), number=100))
