import os
import shutil
import subprocess


REPO_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../")
BUILD_DIR = os.path.abspath(f"{REPO_DIR}/build.em/")

EMSDK_ENV = r"C:\sdks\emsdk\emsdk_env.bat"


def get_env():
    proc = subprocess.Popen(
        f'call "{EMSDK_ENV}" && set', stdout=subprocess.PIPE, shell=True, text=True
    )

    stdout, _ = proc.communicate()
    env = os.environ.copy()
    for line in stdout.splitlines():
        if "=" in line:
            key, val = line.split("=", 1)
            env[key] = val
    return env


def run_build():
    env = get_env()
    os.makedirs(BUILD_DIR, exist_ok=True)

    subprocess.run(
        ["emcmake", "cmake", ".."],
        env=env,
        check=True,
        shell=True,
        cwd=BUILD_DIR,
    )
    subprocess.run(
        ["cmake", "--build", "."],
        env=env,
        check=True,
        shell=True,
        cwd=BUILD_DIR,
    )

    files_to_copy = ["veclang.js", "veclang.wasm"]
    for filename in files_to_copy:
        shutil.copy2(f"{BUILD_DIR}/{filename}", f"{REPO_DIR}/lab/public/{filename}")


if __name__ == "__main__":
    run_build()
