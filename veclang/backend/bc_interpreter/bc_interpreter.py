import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import typing
import dataclasses

import _bc_interpreter_core
from veclang.backend.bc_common.py.vl_sedf import VlProgram, VlSEDF


@dataclasses.dataclass
class ProgramOutput:
    stdout: str
    return_value: typing.Any


def interpret_fn(
    program: VlProgram, fn_idx: int, args: list[typing.Any]
) -> ProgramOutput:
    program_as_bytes = VlSEDF.dumpb(program)
    out = _bc_interpreter_core.interpret_fn(program_as_bytes, fn_idx, args, 0)
    assert len(out) == 2
    return ProgramOutput(out[0], out[1])


class Interpreter:

    def __init__(self, program: VlProgram):
        program_as_bytes = VlSEDF.dumpb(program)
        self.interpreter = _bc_interpreter_core.Interpreter(program_as_bytes)

    def interpret_fn(self, fn_idx: int, args: list[typing.Any]):
        out = self.interpreter.interpret_fn(fn_idx, args, 0)
        return out
