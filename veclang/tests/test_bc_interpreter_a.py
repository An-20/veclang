from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl


def test_basic():
    PROGRAM_STR = """
        using core::*;
        // using math::{sin, PI};
        using math;
        
        fn main() -> real {
            // printr(42.0 + 3.0);
            // return 42;
            return math::sin(math::PI/4);
        }
    """
    compiled = compile_vl(PROGRAM_STR)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    print(a)
