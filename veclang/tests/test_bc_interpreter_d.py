from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl


PROGRAM_STR = """
fn main() -> int {
    for (x: int in 0:-10:-2) {
        printi(x);
    }
    return 0;
}
main();
"""
compiled = compile_vl(PROGRAM_STR)
interpreter = Interpreter(compiled)
interpreter.interpret_program()
