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
<generate_img>
fn mandelbrot(
    x: int,
    y: int,
    res_x: int,
    res_y: int
) -> vec3 {
    const THRESHOLD: real = 2.0;
    let c: complex = (x / res_x - 0.7) + (y / res_y - 0.5) * 1i;
    c = c * 3;
    let z: complex = 0;
    for (_: int in 0:25) {
        if (z.re * z.re + z.im * z.im > THRESHOLD) {
            let v: real = (25 - _) / 25 * 255;
            return [v, v, v];
        }
        z = z * z + c;
    }
    return [0, 0, 0];
}
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

VlSEDF.dump("outmandle.sedf", bytecode)
