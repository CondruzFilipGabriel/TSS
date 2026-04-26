from __future__ import annotations

"""
manual_testing.py

Manual utility for checking the current unit-test suite against to_test.py.

Usage:
    python3 manual_testing.py
    python3 manual_testing.py all
    python3 manual_testing.py functional
    python3 manual_testing.py structural
    python3 manual_testing.py functional --clean-after

Behavior:
1. Cleans runtime artifacts before testing.
2. Selects test files from the current folder.
3. Runs pytest.
4. Runs branch coverage for to_test.py.
5. Runs mutmut for to_test.py.
6. Optionally cleans runtime artifacts after testing with --clean-after.

Notes:
- `all` runs all final test_*.py files, excluding test_propunere.py.
- `functional` runs test_functional.py.
- `structural` runs test_structural.py.
- Any other category name runs test_<category>.py if it exists.
"""

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent

FILE_UNDER_TEST = "to_test.py"
TEST_FILE_PATTERN = "test_*.py"
PROPOSAL_TEST_FILE = "test_propunere.py"

PYTHON_COMMAND = "python3"

MUTMUT_CACHE = ".mutmut-cache"
MUTANTS_DIR = "mutants"
PYPROJECT_FILE = "pyproject.toml"
PYPROJECT_BACKUP_FILE = "__manual_testing_pyproject_backup__.tmp"

PYTEST_CACHE_DIR = ".pytest_cache"
COVERAGE_FILE = ".coverage"

TIMEOUT_SECONDS = 180
MUTMUT_TIMEOUT_SECONDS = 600


@dataclass(frozen=True)
class CommandResult:
    """
    Stores the result of an external command.
    """

    command: list[str]
    returncode: int
    output: str
    timed_out: bool = False


@dataclass(frozen=True)
class PytestResult:
    """
    Stores the pytest summary.
    """

    score: float
    passed: bool
    output: str


@dataclass(frozen=True)
class CoverageResult:
    """
    Stores the branch coverage summary.
    """

    score: float
    output: str


@dataclass(frozen=True)
class MutmutResult:
    """
    Stores the mutation testing summary.
    """

    score: float
    total_mutants: int
    killed_mutants: int
    unresolved_mutants: int
    output: str


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


def parse_pytest_score(output: str, returncode: int) -> float:
    """
    Computes a simple pytest score.

    100.0 means the suite is clean.
    If the suite is not clean, the score is estimated from pytest's final summary.
    """
    if "no tests ran" in output.lower():
        return 0.0

    if returncode == 0:
        return 100.0

    summary_line = ""

    for line in reversed(output.splitlines()):
        if any(
            word in line
            for word in ("passed", "failed", "error", "errors", "xpassed")
        ):
            summary_line = line.strip()
            break

    if not summary_line:
        return 0.0

    counts = {
        "passed": 0,
        "failed": 0,
        "error": 0,
        "errors": 0,
        "xpassed": 0,
    }

    for key in counts:
        match = re.search(rf"(\d+)\s+{key}\b", summary_line)
        if match:
            counts[key] = int(match.group(1))

    total = sum(counts.values())
    if total == 0:
        return 0.0

    return round(counts["passed"] * 100 / total, 2)


def run_pytest(test_files: list[str]) -> PytestResult:
    """
    Runs pytest on the selected test files.
    """
    command = [PYTHON_COMMAND, "-m", "pytest", "-q", *test_files]
    result = run_command(command, TIMEOUT_SECONDS)

    return PytestResult(
        score=parse_pytest_score(result.output, result.returncode),
        passed=result.returncode == 0,
        output=result.output,
    )


def parse_coverage_score(output: str) -> float:
    """
    Extracts the final coverage percentage from coverage report output.
    """
    total_line = ""

    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("TOTAL"):
            total_line = stripped
            break

    if not total_line:
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith(FILE_UNDER_TEST):
                total_line = stripped
                break

    if not total_line:
        return 0.0

    match = re.search(r"(\d+%)\s*$", total_line)
    if not match:
        return 0.0

    return float(match.group(1).replace("%", ""))


def run_coverage(test_files: list[str]) -> CoverageResult:
    """
    Runs coverage with branch measurement for to_test.py.
    """
    run_command([PYTHON_COMMAND, "-m", "coverage", "erase"], TIMEOUT_SECONDS)

    coverage_run = run_command(
        [
            PYTHON_COMMAND,
            "-m",
            "coverage",
            "run",
            "--branch",
            "-m",
            "pytest",
            "-q",
            *test_files,
        ],
        TIMEOUT_SECONDS,
    )

    if coverage_run.returncode != 0:
        return CoverageResult(
            score=0.0,
            output=coverage_run.output,
        )

    coverage_report = run_command(
        [
            PYTHON_COMMAND,
            "-m",
            "coverage",
            "report",
            "-m",
            f"--include={FILE_UNDER_TEST}",
        ],
        TIMEOUT_SECONDS,
    )

    if coverage_report.returncode != 0 or "No data to report" in coverage_report.output:
        return CoverageResult(
            score=0.0,
            output=coverage_report.output,
        )

    return CoverageResult(
        score=parse_coverage_score(coverage_report.output),
        output=coverage_report.output,
    )


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


def print_short_output(title: str, output: str, max_lines: int = 40) -> None:
    """
    Prints a limited command output excerpt.
    """
    print()
    print(f"{title}:")
    print("-" * len(title))

    lines = [line.rstrip() for line in output.splitlines() if line.strip()]

    if not lines:
        print("(no output)")
        return

    for line in lines[:max_lines]:
        print(line)

    if len(lines) > max_lines:
        print(f"... output truncated, {len(lines) - max_lines} more lines not shown")


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run pytest, branch coverage, and mutmut for to_test.py.",
    )

    parser.add_argument(
        "selection",
        nargs="?",
        default="all",
        help=(
            "Test selection: all, functional, structural, or any category name "
            "mapped to test_<category>.py. Default: all."
        ),
    )

    parser.add_argument(
        "--clean-after",
        "--clean-afeter",
        action="store_true",
        dest="clean_after",
        help="Clean runtime artifacts after the manual testing run.",
    )

    return parser.parse_args()


def main() -> None:
    """
    Runs pytest, coverage, and mutmut for the selected test suite.
    """
    args = parse_args()

    print_section("Manual testing for to_test.py")
    print(f"Current folder: {CURRENT_DIR}")
    print(f"Selection: {args.selection}")

    print()
    print("Cleaning runtime artifacts before testing...")
    clean_runtime_artifacts()

    try:
        test_files = select_test_files(args.selection)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)

    print(f"File under test: {FILE_UNDER_TEST}")
    print(f"Selected test files: {', '.join(test_files)}")

    if not ensure_required_files_exist(test_files):
        raise SystemExit(1)

    print_section("Pytest")
    pytest_result = run_pytest(test_files)
    print(f"Pytest score: {pytest_result.score}%")
    print(f"Pytest clean: {'yes' if pytest_result.passed else 'no'}")
    print_short_output("Pytest output", pytest_result.output)

    print_section("Coverage")
    coverage_result = run_coverage(test_files)
    print(f"Branch coverage score for {FILE_UNDER_TEST}: {coverage_result.score}%")
    print_short_output("Coverage output", coverage_result.output)

    print_section("Mutmut")
    mutmut_result = run_mutmut(test_files)
    print(f"Mutation score: {mutmut_result.score}%")
    print(f"Total mutants: {mutmut_result.total_mutants}")
    print(f"Killed mutants: {mutmut_result.killed_mutants}")
    print(f"Unresolved mutants: {mutmut_result.unresolved_mutants}")
    print_short_output("Mutmut output", mutmut_result.output)

    print_section("Summary")
    print(f"Selection: {args.selection}")
    print(f"Test files: {', '.join(test_files)}")
    print(f"Pytest:   {pytest_result.score}%")
    print(f"Coverage: {coverage_result.score}%")
    print(f"Mutmut:   {mutmut_result.score}%")

    if args.clean_after:
        print()
        print("Cleaning runtime artifacts after testing...")
        clean_runtime_artifacts()


if __name__ == "__main__":
    main()
