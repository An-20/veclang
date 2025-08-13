from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir
from veclang.backend.bc_compiler.vl_emitter import emit
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_interpreter.bc_interpreter import interpret_fn
from veclang.common import CompilerFlags


COMPILER_FLAGS: CompilerFlags = CompilerFlags(64)
parsed, diagnostics = parse(
    """
    fn main() -> int {
        printr(42.0 + 3.0);
        return 42;
    }
""",
    COMPILER_FLAGS,
)
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

a = interpret_fn(bytecode, [])
