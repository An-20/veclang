from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl


def test_basic_ops_int_1():
    program_str = """
    fn main(a: int, b: int) -> int {
        return a + b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [1, 2])
    assert a == 3


def test_basic_ops_int_2():
    program_str = """
    fn main(a: int, b: int) -> int {
        return a << b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [1, 4])
    assert a == 16


def test_basic_ops_real_1():
    program_str = """
    fn main(a: real, b: real) -> real {
        return a + b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [1.0, 2.0])
    assert a == 3.0


def test_basic_ops_real_2():
    program_str = """
    fn main(a: real, b: real) -> real {
        return a - b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [15.0, 2.0])
    assert a == 13.0


def test_basic_ops_real_3():
    program_str = """
    fn main(a: real, b: real) -> real {
        return a ** b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [2.0, 4.0])
    assert a == 16.0


def test_selection():
    program_str = """
    fn main(a: real, b: real) -> real {
        if (a < b) {
            return 1.0;
        }
        return 0.0;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    assert interpreter.interpret_fn(0, [15.0, 2.0]) == 0.0
    assert interpreter.interpret_fn(0, [2.0, 3.0]) == 1.0
