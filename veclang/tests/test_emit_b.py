from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir
from veclang.backend.bc_compiler.vl_emitter import BytecodeEmitter
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_common.py.vl_sedf import VlSEDF


parsed = parse(
    """
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
)
print_ast(parsed)
hir, diagnostics = lower(parsed)
print_hir(hir)
emitter = BytecodeEmitter()
bytecode = emitter.emit(hir)
print(disassemble_vl_program(bytecode))
VlSEDF.dump("outmandle.sedf", bytecode)
