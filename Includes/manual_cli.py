from __future__ import annotations
import argparse
from pathlib import Path

from Includes.manual_common import clean_runtime_artifacts, print_section
from Includes.manual_mutmut import run_mutmut
from Includes.manual_pytest_coverage import run_coverage, run_pytest
from Includes.manual_selection import ensure_required_files_exist, select_test_files


from Includes.manual_config import *
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
