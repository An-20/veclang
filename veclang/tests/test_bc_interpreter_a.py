from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl


def test_return_int():
    program_str = """
        fn main() -> int {
            return -1;
        }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert a == -1


def test_return_real():
    program_str = """
        fn main() -> real {
            return 42.0;
        }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert a == 42.0


def test_return_bool():
    program_str = """
        fn main() -> bool {
            return true;
        }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert a is True


def test_return_complex():
    program_str = """
        fn main() -> complex {
            return 3 + 2i;
        }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert a == (3 + 2j)


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
