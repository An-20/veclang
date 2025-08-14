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
fn main() -> int {
    for (x: int in 0:-10:-2) {
        print(x);
    }
    return 0;
}
"""
COMPILED = compile_vl(PROGRAM_STR)
INTERPRETER = Interpreter(COMPILED)
INTERPRETER.interpret_fn(0, [])
