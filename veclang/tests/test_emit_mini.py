from veclang.frontend.parser.parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast, format_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir, format_hir
from veclang.backend.bc_compiler.emitter import BytecodeEmitter
from veclang.backend.bc_compiler.disassembler import disassemble

parsed = parse(
    """
print(1 + 1);
"""
)
print_ast(parsed)
hir = lower(parsed)
print_hir(hir)
emitter = BytecodeEmitter()
bytecode = emitter.emit(hir)
disassemble(bytecode)
