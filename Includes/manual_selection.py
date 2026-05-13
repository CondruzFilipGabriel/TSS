from __future__ import annotations
from pathlib import Path
import re


from Includes.manual_config import *
def file_contains_test_function(path: Path) -> bool:
    """
    Returns True if a Python file contains at least one pytest-style test function.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return False

    return re.search(
        r"^\s*def\s+test_[A-Za-z0-9_]+\s*\(",
        content,
        re.MULTILINE,
    ) is not None

def get_all_final_test_files() -> list[str]:
    """
    Finds all final test_*.py files that contain tests.

    test_propunere.py is excluded because it is a temporary proposal file.
    """
    test_files: list[str] = []

    for path in sorted(CURRENT_DIR.glob(TEST_FILE_PATTERN)):
        if path.name == PROPOSAL_TEST_FILE:
            continue

        if path.is_file() and file_contains_test_function(path):
            test_files.append(path.name)

    return test_files

def get_category_test_file(category: str) -> list[str]:
    """
    Returns the selected test file for a category.

    Examples:
    - functional  -> test_functional.py
    - structural  -> test_structural.py
    - custom      -> test_custom.py
    """
    normalized_category = category.strip()

    if normalized_category.endswith(".py"):
        file_name = normalized_category
    elif normalized_category.startswith("test_"):
        file_name = f"{normalized_category}.py"
    else:
        file_name = f"test_{normalized_category}.py"

    path = CURRENT_DIR / file_name

    if not path.exists():
        raise FileNotFoundError(f"Selected test file does not exist: {file_name}")

    if not file_contains_test_function(path):
        raise ValueError(f"Selected test file contains no test functions: {file_name}")

    return [file_name]

def select_test_files(selection: str) -> list[str]:
    """
    Selects test files based on the command-line argument.
    """
    if selection == "all":
        return get_all_final_test_files()

    return get_category_test_file(selection)

def ensure_required_files_exist(test_files: list[str]) -> bool:
    """
    Validates the minimum files needed for manual testing.
    """
    file_under_test_path = CURRENT_DIR / FILE_UNDER_TEST

    if not file_under_test_path.exists():
        print(f"ERROR: {FILE_UNDER_TEST} was not found in {CURRENT_DIR}.")
        return False

    if not test_files:
        print("ERROR: no runnable test files were selected.")
        return False

    return True
