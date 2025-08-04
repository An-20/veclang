from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir
from veclang.backend.bc_compiler.vl_emitter import BytecodeEmitter
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_common.py.vl_sedf import VlSEDF

parsed = parse(
    """
    print(42);
"""
)
print_ast(parsed)
hir, diagnostics = lower(parsed)
print_hir(hir)
emitter = BytecodeEmitter()
bytecode = emitter.emit(hir)
print(disassemble_vl_program(bytecode))
VlSEDF.dump("out2.sedf", bytecode)
