from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
from veclang.tests.test_bc_interpreter_common import compile_vl

PROGRAM_STR = """
prints("Hello, world!");
"""
compiled = compile_vl(PROGRAM_STR)
interpreter = Interpreter(compiled)
interpreter.interpret_program()
