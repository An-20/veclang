"""Utilities for tests, i.e. sample data"""
import os
import glob
import random
import shutil
import string
import tempfile


def get_test_file_path() -> str:
    """Returns a test file path"""
    base_aureus_tests_temp_path = os.path.join(tempfile.gettempdir(), "AUREUS_TESTS")

    if len(glob.glob(f"{base_aureus_tests_temp_path}\\*")) > 100:
        shutil.rmtree(base_aureus_tests_temp_path)

    if not os.path.exists(base_aureus_tests_temp_path):
        os.makedirs(base_aureus_tests_temp_path, exist_ok=True)

    sequence = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    filename = f"{sequence}.TESTFILE"
    full_path = os.path.join(base_aureus_tests_temp_path, filename)
    if os.path.exists(full_path):
        os.remove(full_path)
    return full_path


def get_test_folder_path() -> str:
    """Returns a test folder path"""
    base_aureus_tests_temp_path = os.path.join(tempfile.gettempdir(), "AUREUS_TESTS")

    if len(glob.glob(f"{base_aureus_tests_temp_path}\\*")) > 100:
        shutil.rmtree(base_aureus_tests_temp_path)

    if not os.path.exists(base_aureus_tests_temp_path):
        os.makedirs(base_aureus_tests_temp_path, exist_ok=True)

    sequence = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    full_path = os.path.join(base_aureus_tests_temp_path, sequence)
    if os.path.exists(full_path):
        os.remove(full_path)
    return full_path
