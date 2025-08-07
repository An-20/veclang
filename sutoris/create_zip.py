import os
import zipfile


BASE_REPO_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../")


def zip_only_py_files(source_folder: str, zip_filename: str, exclude_dirs=None):
    """
    Recursively compresses all .py files from source_folder into a zip file,
    excluding files in specified subdirectories.

    Args:
        source_folder: The root directory to walk.
        zip_filename: The output .zip file path.
        exclude_dirs: A list of directory names (not paths) to exclude (e.g. ['__pycache__', 'venv']).
    """
    if exclude_dirs is None:
        exclude_dirs = []

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(".py"):  # and not file.startswith("test_"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, start=source_folder)
                    zipf.write(full_path, arcname=rel_path)

    print(
        f"Created {zip_filename} with .py files from {source_folder}, excluding {exclude_dirs}"
    )


zip_only_py_files(
    f"{BASE_REPO_DIR}/", f"{BASE_REPO_DIR}/veclang.zip", exclude_dirs=["sutoris"]
)
