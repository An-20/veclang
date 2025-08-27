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

from veclang.backend.bc_common.py.vl_sedf import VlFunction, VlProgram, VlSEDF


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

        expected_num_args = len(
            self.program["header"]["functions"][fn_idx]["arg_types"]
        )
        if len(args) != expected_num_args:
            raise ValueError(f"Expected {expected_num_args} arguments, not {len(args)}")

        new_args = []
        for idx, (arg, arg_type) in enumerate(
            zip(args, self.program["header"]["functions"][fn_idx]["arg_types"])
        ):
            if arg_type == 0 and not isinstance(arg, int):
                raise ValueError(f"Expected argument {idx} to be int")

            elif arg_type == 1 and not isinstance(arg, bool):
                raise ValueError(f"Expected argument {idx} to be bool")

            elif arg_type == 2 and isinstance(arg, int):
                new_args.append(float(arg))

            elif arg_type == 2 and not isinstance(arg, float):
                raise ValueError(f"Expected argument {idx} to be float")

            elif arg_type == 3 and isinstance(arg, (int, float)):
                new_args.append(complex(arg))

            elif arg_type == 3 and not isinstance(arg, complex):
                raise ValueError(f"Expected argument {idx} to be complex")

            new_args.append(arg)

        out = self.interpreter.interpret_fn(
            fn_idx, new_args, self.program["header"]["functions"][fn_idx]["return_type"]
        )
        return out

    def interpret_program(self):
        self.interpreter.interpret_program()

    def interpret_program_continue(self):
        self.interpreter.interpret_program_continue()
