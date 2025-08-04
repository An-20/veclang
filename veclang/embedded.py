import json

from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import print_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import print_hir
from veclang.backend.bc_compiler.vl_emitter import BytecodeEmitter
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_common.py.vl_sedf import VlSEDF


def default_format(data: bytes) -> str:
    """Default formatter taken from CEDF"""
    lines = []
    width = 16
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:08X}  {hex_part:<48}  {ascii_part}")
    return "\n".join(lines)


def disassemble(input_str: str) -> tuple[str, str, str, bytes]:
    parsed = parse(input_str)
    hir, diagnostics = lower(parsed)
    diagnostics_formatted = "\n".join([str(x) for x in diagnostics])
    if hir is None:
        return "", "", diagnostics_formatted, b""

    emitter = BytecodeEmitter()
    vl_program = emitter.emit(hir)
    as_bytes = VlSEDF.dumpb(vl_program)

    header_dumped = json.dumps(vl_program["header"], indent=2)
    try:
        out_str = f"Constants:\n{default_format(vl_program['constants'])}\n\n"
        out_str += f"Instructions:\n{disassemble_vl_program(vl_program)}"
        return header_dumped, out_str, diagnostics_formatted, as_bytes
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
