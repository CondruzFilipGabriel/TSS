from __future__ import annotations

"""
reset.py

Readuce workspace-ul AutoTesting la o stare curata, potrivita pentru o rulare
noua de la zero.

Pastreaza:
- codul framework-ului;
- to_test.py;
- Rules.md;
- testing_functional.md si testing_structural.md;
- fisierele stabile de configurare.

Reseteaza:
- test_functional.py;
- test_structural.py;
- test_propunere.py;
- Logs.jsonl.

Sterge:
- artefacte pytest/coverage/mutmut;
- directoare __pycache__;
- arhive/loguri de rulare anterioare din arh/ si logs/.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STANDARD_TEST_IMPORTS = "import pytest\nfrom to_test import *\n"

GENERATED_TEST_FILES = [
    "test_functional.py",
    "test_structural.py",
    "test_propunere.py",
]

FILES_TO_EMPTY = [
    "Logs.jsonl",
]

FILES_TO_DELETE = [
    ".coverage",
    "__validate_temp__.py",
    "__autotesting_pyproject_backup__.tmp",
]

DIRECTORIES_TO_DELETE = [
    "arh",
    "logs",
    "mutants",
    ".mutmut-cache",
    ".pytest_cache",
    "htmlcov",
]


def safe_delete_file(path: Path) -> None:
    """Sterge un fisier daca exista."""
    if path.exists() and path.is_file():
        path.unlink()


def safe_delete_directory(path: Path) -> None:
    """Sterge recursiv un director daca exista."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)


def remove_pycache_directories() -> None:
    """Sterge toate directoarele __pycache__ din proiect."""
    for pycache_dir in ROOT.rglob("__pycache__"):
        safe_delete_directory(pycache_dir)


def reset_test_files() -> None:
    """
    Reinitializeaza fisierele de teste generate.

    Fisierele test_functional.py si test_structural.py sunt populate ulterior
    de Ollama. Dupa reset trebuie sa existe, dar sa contina doar importurile
    minime. test_propunere.py este fisier temporar si este resetat la fel.

    Alte fisiere test_*.py ramase in root sunt reinitializate, ca sa nu
    contamineze o rulare noua.
    """
    test_files = {ROOT / file_name for file_name in GENERATED_TEST_FILES}
    test_files.update(ROOT.glob("test_*.py"))

    for test_file in sorted(test_files):
        test_file.write_text(STANDARD_TEST_IMPORTS, encoding="utf-8")


def empty_log_files() -> None:
    """Goleste fisierele de log persistente care trebuie pastrate ca nume."""
    for file_name in FILES_TO_EMPTY:
        (ROOT / file_name).write_text("", encoding="utf-8")


def delete_runtime_files() -> None:
    """Sterge fisiere temporare create de rulari anterioare."""
    for file_name in FILES_TO_DELETE:
        safe_delete_file(ROOT / file_name)


def delete_runtime_directories() -> None:
    """Sterge directoare temporare sau arhive create de rulari anterioare."""
    for directory_name in DIRECTORIES_TO_DELETE:
        safe_delete_directory(ROOT / directory_name)


def recreate_required_directories() -> None:
    """Recreeaza directoarele asteptate de aplicatie."""
    (ROOT / "arh").mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)


def print_reset_summary() -> None:
    """Afiseaza sumarul fisierelor importante dupa reset."""
    print("Workspace resetat la o stare curata.")
    for file_name in GENERATED_TEST_FILES:
        status = "OK" if (ROOT / file_name).exists() else "LIPSA"
        print(f"- {file_name}: {status}")


def main() -> None:
    """Executa resetarea completa a workspace-ului."""
    delete_runtime_files()
    delete_runtime_directories()
    remove_pycache_directories()
    recreate_required_directories()
    reset_test_files()
    empty_log_files()
    print_reset_summary()


if __name__ == "__main__":
    main()
