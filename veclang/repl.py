from veclang.frontend.parser.vl_parser import parse
from veclang.midend.hir.vl_lowerer import Lowerer
from veclang.backend.bc_compiler.vl_emitter import BytecodeEmitter
from veclang.backend.bc_compiler.vl_emitter_utils import (
    int_to_2_bytes,
    two_bytes_to_int,
)
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_interpreter.bc_interpreter import Interpreter
import veclang.backend.bc_common.py as bc

from veclang.common import CompilerFlags


class ReplCompiler:

    def __init__(self, compiler_flags: CompilerFlags):
        self.compiler_flags: CompilerFlags = compiler_flags

        self.lowerer: Lowerer = Lowerer(compiler_flags)
        self.emitter: BytecodeEmitter = BytecodeEmitter(compiler_flags)
        self.interpreter: Interpreter | None = None

        self.fn_instructions: list[bytes] = []
        self.first_run = True

    def run(self, input_str: str) -> str:
        parsed, diagnostics = parse(input_str, self.compiler_flags)
        if diagnostics:
            return f"Error when parsing:\n{diagnostics}"

        hir, diagnostics = self.lowerer.lower(parsed, import_core=self.first_run)
        if not hir:
            return f"Error when lowering:\n{diagnostics}"

        self.emitter.instructions.clear()
        self.emitter.instructions = self.fn_instructions
        bytecode, diagnostics = self.emitter.emit(hir, force_start_with_jmp=True)
        if diagnostics:
            return f"Error when emitting:\n{diagnostics}"

        if False:
            print(disassemble_vl_program(bytecode))

        if self.interpreter:
            self.interpreter.update_program(bytecode)
        else:
            self.interpreter = Interpreter(bytecode)

        self.interpreter.interpret_program_continue()
        self.first_run = False


repl = ReplCompiler(CompilerFlags(64))
while True:
    input_str = input(">>> ")
    repl_out = repl.run(input_str)
    if repl_out:
        print(repl_out)
