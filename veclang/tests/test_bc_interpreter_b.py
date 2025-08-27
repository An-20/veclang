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


def test_basic_ops_complex_1():
    program_str = """
    fn main(a: complex, b: complex) -> complex {
        return a + b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [3 + 2j, 5 + 3j])
    assert a == 8 + 5j


def test_basic_ops_complex_2():
    program_str = """
    fn main(a: complex, b: complex) -> complex {
        return a - b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [3 + 2j, 5 + 3j])
    assert a == -2 - 1j


def test_basic_ops_complex_3():
    program_str = """
    fn main(a: complex, b: complex) -> complex {
        return a * b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [3 + 2j, 5 + 3j])
    assert a == 9 + 19j


def test_basic_ops_complex_4():
    program_str = """
    fn main(a: complex, b: complex) -> complex {
        return a / b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [4j, 2j])
    assert a == 2.0


def test_basic_ops_complex_5():
    program_str = """
    fn main() -> complex {
        using math::*;
        return E ** (PI * 1i);
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [])
    assert abs(a - (-1.0)) < 0.01


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


def test_for():
    program_str = """
    fn main(a: int) -> int {
        let prod: int = 1;
        for (n: int in 1:(a+1)) {
            prod = prod * n;
        }
        return prod;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    assert interpreter.interpret_fn(0, [3]) == 6
    assert interpreter.interpret_fn(0, [4]) == 24
    assert interpreter.interpret_fn(0, [5]) == 120


def test_while():
    program_str = """
    fn main(a: int) -> int {
        let prod: int = 1;
        let n: int = 1;
        while (n <= a) {
            prod *= n;
            n += 1;
        }
        return prod;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    assert interpreter.interpret_fn(0, [3]) == 6
    assert interpreter.interpret_fn(0, [4]) == 24
    assert interpreter.interpret_fn(0, [5]) == 120
