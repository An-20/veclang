import json

from veclang.frontend.parser.vl_parser import parse
from veclang.midend.hir import lower
from veclang.backend.bc_compiler.vl_emitter import emit
from veclang.backend.bc_compiler.vl_disassembler import (
    disassemble_vl_program,
    default_format,
)
from veclang.backend.bc_common.py.vl_sedf import VlSEDF


def vl_compile(input_str: str) -> tuple[str, str, str, bytes]:
    """
    Compiles a program, returning a tuple of:
    - str of dumped header JSON data
    - str of disassembled constants and instructions
    - str of diagnostics HR-formatted
    - bytes of raw VlSEDF data
    """
    diagnostics_combined = []

    parsed, diagnostics = parse(input_str)
    if diagnostics:
        return "", "", "\n\n".join(str(x) for x in diagnostics), b""

    hir, diagnostics = lower(parsed)
    if not hir:
        return "", "", "\n\n".join(str(x) for x in diagnostics), b""
    elif diagnostics:
        diagnostics_combined.extend(diagnostics)

    vl_program, diagnostics = emit(hir)
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
