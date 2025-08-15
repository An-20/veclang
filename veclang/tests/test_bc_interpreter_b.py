from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl


def test_basic_ffi_int():
    program_str = """
    fn main(a: int, b: int) -> int {
        return a + b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [1, 2])
    print(a)


def test_basic_ffi_real():
    program_str = """
    fn main(a: real, b: real) -> real {
        return a + b;
    }
    """
    compiled = compile_vl(program_str)
    interpreter = Interpreter(compiled)
    a = interpreter.interpret_fn(0, [1.0, 2.0])
    print(a)
