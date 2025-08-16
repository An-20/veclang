from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.common import CompilerFlags


COMPILER_FLAGS: CompilerFlags = CompilerFlags(64)
PROGRAM_STR = """
using math;
using math::*;

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

fn main(
    <key: "value">
    asdas: mat4
) -> int {
    a::b::c();
    return real(0);
}
"""
parsed, diagnostics = parse(PROGRAM_STR, COMPILER_FLAGS)
if diagnostics:
    raise ValueError(f"Error when parsing: {diagnostics}")
print_ast(parsed)
