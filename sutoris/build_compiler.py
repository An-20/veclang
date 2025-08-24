import os
import zipfile


BASE_REPO_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../")


def zip_only_py_files(
    source_folder: str, zip_filename: str, exclude_dirs=None, exclude_filenames=None
):
    """
    Recursively compresses all .py files from source_folder into a zip file,
    excluding files in specified subdirectories or with specified filenames.

    Args:
        source_folder: The root directory to walk.
        zip_filename: The output .zip file path.
        exclude_dirs: A list of directory names (not paths) to exclude (e.g. ['__pycache__', 'venv']).
        exclude_filenames: A list of filenames (not paths) to exclude (e.g. ['setup.py', 'config.py']).
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_filenames is None:
        exclude_filenames = []

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(".py") and file not in exclude_filenames:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, start=source_folder)
                    zipf.write(full_path, arcname=rel_path)

    print(
        f"Created {zip_filename} with .py files from {source_folder}, "
        f"excluding dirs {exclude_dirs} and files {exclude_filenames}"
    )


zip_only_py_files(
    f"{BASE_REPO_DIR}/",
    f"{BASE_REPO_DIR}/lab/public/veclang.zip",
    exclude_dirs=["sutoris", "lab"],
    exclude_filenames=["main.py"],
)
