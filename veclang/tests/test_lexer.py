from veclang.frontend.parser.vl_lexer import lexer
from veclang.common import CompilerFlags


COMPILER_FLAGS: CompilerFlags = CompilerFlags(64)
VL_PROGRAM = """
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
    return real(0);
}
"""


lexer.line_no = 0
lexer_tokens = []
# Give the lexer some input
lexer.input(VL_PROGRAM)

# Tokenize
while True:
    tok = lexer.token()
    if not tok:
        break  # No more input
    lexer_tokens.append(tok)

print(lexer_tokens)
