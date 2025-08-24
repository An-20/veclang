from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir
from veclang.backend.bc_compiler.vl_emitter import emit
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_common.py.vl_sedf import VlSEDF
from veclang.common import CompilerFlags


COMPILER_FLAGS: CompilerFlags = CompilerFlags(64)
PROGRAM_STR = """
fn sum(n: int) -> int {
    let s: int = 0;
    for (x: int in 0:n) {
        s += x;
    }
    return s;
}
printi(sum(100000));
"""
parsed, diagnostics = parse(PROGRAM_STR, COMPILER_FLAGS)
if diagnostics:
    raise ValueError(f"Error when parsing: {diagnostics}")
print_ast(parsed)

hir, diagnostics = lower(parsed, COMPILER_FLAGS)
if not hir:
    raise ValueError(f"Error when lowering: {diagnostics}")
elif diagnostics:
    print("Diagnostics emitted during lowering:")
    for d in diagnostics:
        print(d)
print_hir(hir)

bytecode, diagnostics = emit(hir, COMPILER_FLAGS)
if diagnostics:
    raise ValueError(f"Error when emitting: {diagnostics}")
print(disassemble_vl_program(bytecode))

VlSEDF.dump("out.sedf", bytecode)
