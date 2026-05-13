from __future__ import annotations
import re
import shutil
from pathlib import Path
from Includes.manual_common import clean_runtime_artifacts, run_command, safe_remove_path
from Includes.manual_models import MutmutResult


from Includes.manual_config import *
def build_mutmut_pyproject_text(test_files: list[str]) -> str:
    """
    Builds a temporary pyproject.toml section for mutmut.
    """
    quoted_test_files = ", ".join(f'"{file_name}"' for file_name in test_files)

    return (
        "[tool.mutmut]\n"
        f'paths_to_mutate = ["{FILE_UNDER_TEST}"]\n'
        f"pytest_add_cli_args_test_selection = [{quoted_test_files}]\n"
        'pytest_add_cli_args = ["-q"]\n'
        "debug = true\n"
    )

def prepare_mutmut_environment(test_files: list[str]) -> bool:
    """
    Backs up pyproject.toml if present, clears mutmut artifacts, and writes
    a temporary mutmut configuration.

    Returns True if an original pyproject.toml existed.
    """
    pyproject_path = CURRENT_DIR / PYPROJECT_FILE
    backup_path = CURRENT_DIR / PYPROJECT_BACKUP_FILE

    had_pyproject = pyproject_path.exists()

    if had_pyproject:
        shutil.copy2(pyproject_path, backup_path)

    safe_remove_path(CURRENT_DIR / MUTMUT_CACHE)
    safe_remove_path(CURRENT_DIR / MUTANTS_DIR)

    pyproject_path.write_text(
        build_mutmut_pyproject_text(test_files),
        encoding="utf-8",
    )

    return had_pyproject

def restore_mutmut_environment(had_pyproject: bool) -> None:
    """
    Restores the previous pyproject.toml state after mutmut.
    """
    pyproject_path = CURRENT_DIR / PYPROJECT_FILE
    backup_path = CURRENT_DIR / PYPROJECT_BACKUP_FILE

    if had_pyproject and backup_path.exists():
        shutil.move(str(backup_path), str(pyproject_path))
        return

    if backup_path.exists():
        backup_path.unlink()

    if not had_pyproject and pyproject_path.exists():
        pyproject_path.unlink()

def parse_total_mutants_from_run_output(run_output: str) -> int:
    """
    Extracts the total number of mutants from mutmut run output.
    """
    lines = [line.strip() for line in run_output.splitlines() if line.strip()]

    for line in reversed(lines):
        match = re.search(r"(\d+)\s*/\s*(\d+)", line)
        if match:
            left = int(match.group(1))
            right = int(match.group(2))
            if right > 0 and left == right:
                return right

    return 0

def parse_unresolved_mutants_from_results(results_output: str) -> int:
    """
    Counts unresolved mutants from mutmut results output.

    Unresolved states are treated as not killed.
    """
    unresolved = 0

    unresolved_suffixes = (
        ": survived",
        ": timeout",
        ": suspicious",
        ": skipped",
        ": not checked",
    )

    for raw_line in results_output.splitlines():
        line = raw_line.strip().lower()

        if any(line.endswith(suffix) for suffix in unresolved_suffixes):
            unresolved += 1

    return unresolved

def run_mutmut(test_files: list[str]) -> MutmutResult:
    """
    Runs mutmut and computes a mutation score.
    """
    if shutil.which("mutmut") is None:
        return MutmutResult(
            score=0.0,
            total_mutants=0,
            killed_mutants=0,
            unresolved_mutants=0,
            output="mutmut executable was not found.",
        )

    had_pyproject = False

    try:
        had_pyproject = prepare_mutmut_environment(test_files)

        run_result = run_command(["mutmut", "run"], MUTMUT_TIMEOUT_SECONDS)
        run_output = run_result.output

        if run_result.returncode != 0:
            return MutmutResult(
                score=0.0,
                total_mutants=0,
                killed_mutants=0,
                unresolved_mutants=0,
                output=run_output,
            )

        results_result = run_command(["mutmut", "results"], TIMEOUT_SECONDS)
        results_output = results_result.output

        total_mutants = parse_total_mutants_from_run_output(run_output)
        unresolved_mutants = parse_unresolved_mutants_from_results(results_output)

        combined_output = run_output + "\n" + results_output

        if total_mutants <= 0:
            return MutmutResult(
                score=0.0,
                total_mutants=0,
                killed_mutants=0,
                unresolved_mutants=0,
                output=combined_output,
            )

        if unresolved_mutants > total_mutants:
            return MutmutResult(
                score=0.0,
                total_mutants=total_mutants,
                killed_mutants=0,
                unresolved_mutants=unresolved_mutants,
                output=combined_output,
            )

        killed_mutants = total_mutants - unresolved_mutants
        score = round(killed_mutants * 100 / total_mutants, 2)

        return MutmutResult(
            score=score,
            total_mutants=total_mutants,
            killed_mutants=killed_mutants,
            unresolved_mutants=unresolved_mutants,
            output=combined_output,
        )

    finally:
        restore_mutmut_environment(had_pyproject)
