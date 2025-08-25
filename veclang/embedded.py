import json

from veclang.frontend.parser.vl_parser import parse
from veclang.midend.hir import lower
from veclang.backend.bc_compiler.vl_emitter import emit
from veclang.backend.bc_compiler.vl_disassembler import (
    disassemble_vl_program,
    default_format,
)
from veclang.backend.bc_common.py.vl_sedf import VlSEDF

import veclang.repl as repl
from veclang.common import CompilerFlags


def vl_compile(input_str: str) -> tuple[str, str, str, bytes]:
    """
    Compiles a program, returning a tuple of:
    - str of dumped header JSON data
    - str of disassembled constants and instructions
    - str of diagnostics HR-formatted
    - bytes of raw VlSEDF data
    """
    diagnostics_combined = []
    compiler_flags: CompilerFlags = CompilerFlags(64)

    parsed, diagnostics = parse(input_str, compiler_flags)
    if diagnostics:
        return "", "", "\n\n".join(str(x) for x in diagnostics), b""

    hir, diagnostics = lower(parsed, compiler_flags)
    if not hir:
        return "", "", "\n\n".join(str(x) for x in diagnostics), b""
    elif diagnostics:
        diagnostics_combined.extend(diagnostics)

    vl_program, diagnostics = emit(hir, compiler_flags)
    if diagnostics:
        return "", "", "\n\n".join(str(x) for x in diagnostics), b""

    as_bytes = VlSEDF.dumpb(vl_program)
    header_dumped = json.dumps(vl_program["header"], indent=2)
    diagnostics_combined = sorted(diagnostics_combined, key=lambda x: x.line_no)
    diagnostics_formatted = "\n\n".join(str(x) for x in diagnostics_combined)
    try:
        disassembled = disassemble_vl_program(vl_program)
        return header_dumped, disassembled, diagnostics_formatted, as_bytes
    except Exception as e:
        return (
            header_dumped,
            (
                f"Exception when disassembling: {e}\nRaw data:"
                f"\n{default_format(vl_program['constants'] + vl_program['instructions'])}"
            ),
            diagnostics_formatted,
            as_bytes,
        )


repl_compiler = repl.ReplCompiler(CompilerFlags(64))


def vl_repl_compile(input_str: str) -> tuple[str, bytes]:
    """
    Compiles a program for REPL, returning a tuple of:
    - str of diagnostics HR-formatted (if diagnostics are returned, then compilation has FAILED)
    - bytes of raw VlSEDF data
    """
    out = repl_compiler.compile(input_str)
    if isinstance(out, str):
        return out, b""
    return "", VlSEDF.dumpb(out)
