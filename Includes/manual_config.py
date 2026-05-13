from __future__ import annotations
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parents[1]

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
