from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl


def test_basic():
    program_str = """
        fn main() -> real {
            return 42.0;
        }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert a == 42.0


def test_imports_1():
    program_str = """
        fn main() -> real {
            using math::{sin, PI};
            return sin(PI/4);
        }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert abs(a - 0.707) < 0.01


def test_imports_2():
    program_str = """
        using math;
        fn main() -> real {
            return math::sin(math::PI/4);
        }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert abs(a - 0.707) < 0.01
