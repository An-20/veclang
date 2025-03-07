import subprocess


subprocess.run(
    [
        "lib/flatc.exe",
        "--python",
        "-o",
        "veclang/backend/bc_common/py/",
        "veclang/backend/bc_common/bytecode.fbs",
    ]
)


subprocess.run(
    [
        "lib/flatc.exe",
        "--cpp",
        "-o",
        "veclang/backend/bc_common/cpp/",
        "veclang/backend/bc_common/bytecode.fbs",
    ]
)
