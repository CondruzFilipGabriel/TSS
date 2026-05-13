from __future__ import annotations
import re
from pathlib import Path
from Includes.manual_common import run_command
from Includes.manual_models import PytestResult, CoverageResult


from Includes.manual_config import *
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
