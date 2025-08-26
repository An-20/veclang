import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))

import argparse
from termcolor import colored
from veclang.frontend.parser.vl_parser import parse
from veclang.frontend.parser.vl_ast_io import format_ast
from veclang.midend.hir import lower
from veclang.midend.hir.vl_hlr_io import format_hir
from veclang.backend.bc_compiler.vl_emitter import emit
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program
from veclang.backend.bc_common.py.vl_sedf import VlSEDF
from veclang.backend.bc_interpreter.bc_interpreter import Interpreter

from veclang.repl import ReplCompiler

from veclang.common import CompilerFlags, LANGUAGE_VERSION_STR, COMPILER_VERSION_STR


def dump_output(label, content, color, file_path=None):
    """Dump text either to stdout or to a file."""
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(content))
        print(colored(f"{label} written to {file_path}", color, attrs=["bold"]))
    else:
        print(colored(label, color, attrs=["bold"]))
        print(content)


def main():
    parser = argparse.ArgumentParser(
        prog="veclang", description="Veclang bytecode compiler and interpreter"
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Veclang {LANGUAGE_VERSION_STR}, compiler {COMPILER_VERSION_STR}",
        help="Show version information",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # compile command
    compile_cmd = subparsers.add_parser(
        "compile", help="Compile a Veclang source file to bytecode"
    )
    compile_cmd.add_argument("input", help="Source file (.vl)")
    compile_cmd.add_argument(
        "-o", "--output", help="Output bytecode file", default="out.vl_sedf"
    )
    compile_cmd.add_argument("--debug", action="store_true", help="Enable debug output")
    compile_cmd.add_argument(
        "--dump-ast", nargs="?", const=True, help="Dump AST (optionally to file)"
    )
    compile_cmd.add_argument(
        "--dump-hir", nargs="?", const=True, help="Dump HIR (optionally to file)"
    )
    compile_cmd.add_argument(
        "--dump-dis",
        nargs="?",
        const=True,
        help="Dump disassembled bytecode (optionally to file)",
    )
    compile_cmd.add_argument(
        "--runtime-precision",
        type=int,
        choices=[32, 64],
        default=64,
        help="Target runtime precision (32 or 64 bits, default 64)",
    )

    # repl command
    repl_cmd = subparsers.add_parser("repl", help="Start interactive Veclang REPL")

    args = parser.parse_args()

    if args.command == "compile":
        if args.runtime_precision not in {32, 64}:
            raise ValueError("IE: args.runtime_precision not in {32, 64}")
        compiler_flags: CompilerFlags = CompilerFlags(args.runtime_precision)

        with open(args.input) as f:
            source = f.read()

        ast, diagnostics = parse(source, compiler_flags)
        if diagnostics:
            print(colored(f"Error(s) when parsing AST:", "red", attrs=["bold"]))
            print("\n\n".join([str(x) for x in diagnostics]))
            print(
                colored(
                    f"The above errors were fatal. Compilation terminated.",
                    "red",
                    attrs=["bold"],
                )
            )
            return

        if args.dump_ast or args.debug:
            ast_formatted = format_ast(ast)
            dump_output(
                "AST:",
                ast_formatted,
                "yellow",
                None if args.dump_ast is True else args.dump_ast,
            )

        hir, diagnostics = lower(ast, compiler_flags)
        if diagnostics:
            has_errors = any([x.code.startswith("E") for x in diagnostics])
            if has_errors:
                print(colored(f"Error(s) when lowering to HIR:", "red", attrs=["bold"]))
                print(
                    "\n\n".join([str(x) for x in diagnostics if x.code.startswith("E")])
                )
                print(
                    colored(
                        f"The above errors were fatal. Compilation terminated.",
                        "red",
                        attrs=["bold"],
                    )
                )
            has_warnings = any([not x.code.startswith("E") for x in diagnostics])
            if has_warnings:
                print(
                    colored(f"Warning(s) when lowering to HIR:", "red", attrs=["bold"])
                )
                print(
                    "\n\n".join(
                        [str(x) for x in diagnostics if not x.code.startswith("E")]
                    )
                )
            if has_errors:
                return

        if args.dump_hir or args.debug:
            hir_formatted = format_hir(hir)
            dump_output(
                "HIR:",
                hir_formatted,
                "cyan",
                None if args.dump_hir is True else args.dump_hir,
            )

        vl_program, diagnostics = emit(hir, compiler_flags)
        if diagnostics:
            print(colored(f"Error(s) when emitting bytecode:", "red", attrs=["bold"]))
            print("\n\n".join([str(x) for x in diagnostics]))
            print(
                colored(
                    f"The above errors were fatal. Compilation terminated.",
                    "red",
                    attrs=["bold"],
                )
            )
            return

        if args.dump_dis or args.debug:
            disassembled = disassemble_vl_program(vl_program)
            dump_output(
                "Disassembly:",
                disassembled,
                "magenta",
                None if args.dump_dis is True else args.dump_dis,
            )

        if args.debug:
            print(
                colored(
                    f"Compiled bytecode constants length: {len(vl_program['constants'])} bytes",
                    "green",
                )
            )
            print(
                colored(
                    f"Compiled bytecode instructions length: {len(vl_program['instructions'])} bytes",
                    "green",
                )
            )

        with open(args.output, "wb") as f:
            f.write(VlSEDF.dumpb(vl_program))

        print(
            colored(f"Compilation successful: {args.output}", "green", attrs=["bold"])
        )

    elif args.command == "repl":
        print(
            f"Veclang {LANGUAGE_VERSION_STR} (compiler {COMPILER_VERSION_STR}, interpreter bc_interpreter)"
        )
        print(colored("Veclang REPL - 'exit' to quit", "magenta", attrs=["bold"]))

        repl_compiler = ReplCompiler(CompilerFlags(64))
        interpreter: Interpreter | None = None

        while True:
            try:
                line = input(">>> ")
                if line.strip() == "exit":
                    break
                if not line.strip():
                    continue

                compiled = repl_compiler.compile(line)
                if isinstance(compiled, str):
                    out_lines = compiled.splitlines()
                    for idx, line in enumerate(out_lines):
                        if line.startswith("Error") and idx:
                            print(colored("Error", "red") + line[5:])
                        elif line.startswith("Warning") and idx:
                            print(colored("Warning", "yellow") + line[7:])
                        else:
                            print(line)

                else:
                    if interpreter:
                        interpreter.update_program(compiled)
                    else:
                        interpreter = Interpreter(compiled)

                    interpreter.interpret_program_continue()

            except KeyboardInterrupt:
                print(colored("\nInterrupted by KeyboardInterrupt", "red"))
                break
            except Exception as e:
                print(colored(f"Error: {e}", "red", attrs=["bold"]))


if __name__ == "__main__":
    main()
