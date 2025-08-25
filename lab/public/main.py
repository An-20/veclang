import time

import js
import pyscript
from pyodide.ffi import to_js

import veclang.embedded as embedded


def compile_program(code: str):
    compile_start_time = time.perf_counter()
    try:
        header, disassembled, diagnostics, as_bytes = embedded.vl_compile(code)
    except Exception as e:
        header, disassembled, diagnostics, as_bytes = (
            "",
            "",
            f"Error compiling code: {e}",
            b"",
        )
    compile_end_time = time.perf_counter()

    if not diagnostics.strip():
        diagnostics = "<no diagnostics>"

    js.window.txtOutput.clear()
    js.window.txtOutput.appendLines(
        f"Compiled in {compile_end_time-compile_start_time:.4}s.\n"
        f"Compiler diagnostics:\n{diagnostics}\n\n"
    )

    js.window.headerOutput.clear()
    js.window.disOutput.clear()
    js.window.headerOutput.appendLines(header)
    js.window.disOutput.appendLines(disassembled)
    js_array = to_js(as_bytes)
    js.handleProgramBytes(js_array)


def compile_and_run_program(code: str, image_resolution: int):
    compile_program(code)

    run_start_time = time.perf_counter()
    js.window.runProgram(image_resolution)
    run_end_time = time.perf_counter()
    js.window.txtOutput.appendLines(f"Ran in {run_end_time-run_start_time:.4}s.\n")


def compile_program_repl(code: str):
    diagnostics, bytecode = embedded.vl_repl_compile(code)
    if diagnostics:
        js.window.replOutput.writeStderr(diagnostics)
    else:
        js.window.handleReplProgramBytes(bytecode)


js.window.compile_program = pyscript.ffi.create_proxy(compile_program)
js.window.compile_and_run_program = pyscript.ffi.create_proxy(compile_and_run_program)

js.window.compile_program_repl = pyscript.ffi.create_proxy(compile_program_repl)
