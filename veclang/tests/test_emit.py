from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast, format_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir, format_hir
from veclang.backend.bc_compiler.vl_emitter import BytecodeEmitter
from veclang.backend.bc_compiler.vl_disassembler import disassemble


parsed = parse(
    """
<generate_img>
fn main(x: int, y: int, res_x: int, res_y: int) -> vec3 { return [255, 255, 255]; }

<generate_img>
fn mandlebrot(
    x: int,
    y: int,
    res_x: int,
    res_y: int
) -> vec3 {
    const ITERATIONS: int = 50;
    const THRESHOLD: real = 100;
    let c: complex = x / res_x + (y / res_y) * 1i;
    let z: complex = 0;
    for (_: int in 0:ITERATIONS) {
        if (z.re * z.re + z.im * z.im > THRESHOLD) {
            return [0, 0, 0];
        }
        z = z * z + c;
    }
    return [255, 255, 255];
}
"""
)
print_ast(parsed)
hir = lower(parsed)
print_hir(hir)
emitter = BytecodeEmitter()
bytecode = emitter.emit(hir)
disassemble(bytecode)
