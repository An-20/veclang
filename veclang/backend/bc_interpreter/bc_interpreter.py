import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import typing
import dataclasses

# noinspection PyUnresolvedReferences
try:
    import _bc_interpreter_core

    _HAVE_BC_INTERPRETER_CORE = True
except ImportError:
    _HAVE_BC_INTERPRETER_CORE = False

from veclang.backend.bc_common.py.vl_sedf import VlProgram, VlSEDF


@dataclasses.dataclass
class ProgramOutput:
    stdout: str
    return_value: typing.Any


class Interpreter:

    def __init__(self, program: VlProgram):
        if not _HAVE_BC_INTERPRETER_CORE:
            raise ValueError("Could not import _bc_interpreter_core extension!")

        program_as_bytes = VlSEDF.dumpb(program)
        self.program: VlProgram = program
        self.interpreter = _bc_interpreter_core.Interpreter(program_as_bytes)

    def update_program(self, program: VlProgram):
        program_as_bytes = VlSEDF.dumpb(program)
        self.program: VlProgram = program
        self.interpreter.update_program(program_as_bytes)

    def interpret_fn(self, fn_idx: int, args: list[typing.Any]):
        if fn_idx not in range(len(self.program["header"]["functions"])):
            raise ValueError("too high fn_idx!")
        out = self.interpreter.interpret_fn(
            fn_idx, args, self.program["header"]["functions"][fn_idx]["return_type"]
        )
        return out

    def interpret_program(self):
        self.interpreter.interpret_program()

    def interpret_program_continue(self):
        self.interpreter.interpret_program_continue()
