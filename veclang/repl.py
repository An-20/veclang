from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast import ASTPositionInfo
from veclang.midend.hir.vl_lowerer import Lowerer
import veclang.midend.hir.vl_hir as vl_hir
import veclang.midend.vl_core as vl_core
from veclang.backend.bc_compiler.vl_emitter import BytecodeEmitter
from veclang.backend.bc_compiler.vl_emitter_utils import two_bytes_to_int
from veclang.backend.bc_common.py.vl_sedf import VlProgram

from veclang.common import CompilerFlags


class ReplCompiler:

    def __init__(self, compiler_flags: CompilerFlags):
        self.compiler_flags: CompilerFlags = compiler_flags

        self.lowerer: Lowerer = Lowerer(compiler_flags)
        self.emitter: BytecodeEmitter = BytecodeEmitter(compiler_flags)

        self.fn_instructions: list[bytes] = []
        self.first_lowerer_run = True

    @staticmethod
    def format_diagnostics(diagnostics) -> str:
        return "\n".join(str(x) for x in diagnostics)

    def compile(self, input_str: str) -> VlProgram | str:
        is_expr = False
        parsed, diagnostics = parse(input_str, self.compiler_flags)
        if diagnostics:
            # user could have inputted an expression
            parsed, new_diagnostics = parse(input_str + ";", self.compiler_flags)
            if new_diagnostics:
                return f"Error(s) when parsing:\n{self.format_diagnostics(diagnostics)}"
            is_expr = True

        if self.first_lowerer_run:
            hir, diagnostics = self.lowerer.lower(parsed, additional_imports=["repl"])
        else:
            hir, diagnostics = self.lowerer.lower(parsed, import_core=False)
        self.first_lowerer_run = False
        if not hir:
            return f"Error(s) when lowering:\n{self.format_diagnostics(diagnostics)}"

        if is_expr:
            # wrap statement in the repl_printx function call
            if len(hir.stmts) != 1:
                raise ValueError("IE")
            elif not isinstance(hir.stmts[0], vl_hir.ExprStmtNode):
                raise ValueError("IE")
            # noinspection PyUnresolvedReferences
            expr: vl_hir.ExprNode = hir.stmts[0].expr
            if expr.vl_type.to_vl_type_str() != "null":
                repl_print_fn_id = {
                    "int": 0x0010,
                    "bool": 0x0011,
                    "real": 0x0012,
                    "complex": 0x0013,
                    "vec2": 0x0014,
                    "vec3": 0x0015,
                    "vec4": 0x0016,
                    # "mat2": 0x0000,  # TODO!
                    # "mat3": 0x0000,
                    # "mat4": 0x0000,
                }[expr.vl_type.to_vl_type_str()]
                api = ASTPositionInfo(1, 1)
                hir.stmts[0] = vl_hir.ExprStmtNode(
                    vl_hir.BuiltinFunctionCallExprNode(
                        repl_print_fn_id, [expr], vl_core.vl_types_val.VlNull, None, api
                    ),
                    api,
                )

        self.emitter.instructions.clear()
        self.emitter.instructions = self.fn_instructions
        bytecode, diagnostics = self.emitter.emit(hir, force_start_with_jmp=True)
        fn_instructions_len = two_bytes_to_int(bytecode["instructions"][2:4])
        instructions = [
            bytecode["instructions"][i : i + 4]
            for i in range(0, len(bytecode["instructions"]), 4)
        ]
        self.fn_instructions = instructions[:fn_instructions_len]
        if diagnostics:
            return f"Error(s) when emitting:\n{self.format_diagnostics(diagnostics)}"

        return bytecode
