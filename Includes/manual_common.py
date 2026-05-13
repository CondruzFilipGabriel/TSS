from __future__ import annotations
import re
import shutil
import subprocess
from pathlib import Path
from Includes.manual_models import CommandResult


from Includes.manual_config import *
def print_section(title: str) -> None:
    """
    Prints a visible terminal section title.
    """
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

def run_command(command: list[str], timeout: int) -> CommandResult:
    """
    Runs an external command and captures stdout and stderr.
    """
    try:
        result = subprocess.run(
            command,
            cwd=CURRENT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = (result.stdout or "") + (result.stderr or "")

        return CommandResult(
            command=command,
            returncode=result.returncode,
            output=output,
            timed_out=False,
        )

    except subprocess.TimeoutExpired as error:
        output = (error.stdout or "") + (error.stderr or "")

        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")

        return CommandResult(
            command=command,
            returncode=124,
            output=output + f"\nTimeout after {timeout} seconds.",
            timed_out=True,
        )

def safe_remove_path(path: Path) -> None:
    """
    Removes a file or directory if it exists.
    """
    try:
        if not path.exists():
            return

        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    except OSError as error:
        print(f"WARNING: could not remove {path}: {type(error).__name__}: {error}")

def remove_all_pycache_directories() -> None:
    """
    Removes all __pycache__ directories from the current project folder.
    """
    for pycache_dir in CURRENT_DIR.rglob("__pycache__"):
        safe_remove_path(pycache_dir)

def clean_runtime_artifacts() -> None:
    """
    Removes runtime artifacts that can affect pytest, coverage, or mutmut.

    This cleanup intentionally does not delete or rewrite test files.
    It also does not reset test_propunere.py, because this script is manual
    and should avoid changing user-written test content.
    """
    safe_remove_path(CURRENT_DIR / MUTMUT_CACHE)
    safe_remove_path(CURRENT_DIR / MUTANTS_DIR)
    safe_remove_path(CURRENT_DIR / PYPROJECT_BACKUP_FILE)
    safe_remove_path(CURRENT_DIR / PYTEST_CACHE_DIR)
    safe_remove_path(CURRENT_DIR / COVERAGE_FILE)
    remove_all_pycache_directories()
