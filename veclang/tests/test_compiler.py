from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir
from veclang.backend.bc_compiler.vl_emitter import BytecodeEmitter
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_interpreter.bc_interpreter import interpret_fn


def compile_vl(program_str: str):
    parsed = parse(program_str)
    hir, diagnostics = lower(parsed)
    emitter = BytecodeEmitter()
    bytecode = emitter.emit(hir)
    return bytecode


PROGRAM_STR = """
fn main(a: int, b: int) -> int {
    return a + b;
}
"""
print(interpret_fn(compile_vl(PROGRAM_STR), [1, 2]).return_value)
