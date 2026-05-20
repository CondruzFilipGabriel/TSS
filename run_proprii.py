from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = ROOT_DIR / "examples"
PYTHON = "python3"
FILE_UNDER_TEST = "to_test.py"
FUNCTIONAL_TEST_FILE = "test_functional_propriu.py"
STRUCTURAL_TEST_FILE = "test_structural_propriu.py"

TEMP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    "mutants",
    ".mutmut-cache",
}
TEMP_FILE_PATTERNS = (
    ".coverage",
    ".coverage.*",
    "pyproject.toml.bak",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ruleaza pytest, coverage si mutmut pe testele proprii din examples/<numar>.",
    )
    parser.add_argument(
        "example",
        nargs="?",
        default="1",
        help="Numarul folderului din examples/. Default: 1.",
    )
    parser.add_argument(
        "selection",
        nargs="?",
        default="all",
        help="Selectie: all, functional, structural sau numele exact al fisierului de teste.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listeaza exemplele disponibile si se opreste.",
    )
    parser.add_argument(
        "--no-clean-after",
        action="store_true",
        help="Nu sterge artefactele temporare dupa rulare.",
    )
    return parser.parse_args()


def example_number(path: Path) -> int:
    try:
        return int(path.name)
    except ValueError:
        return 10**9


def list_examples() -> list[Path]:
    if not EXAMPLES_DIR.exists():
        return []
    return sorted(
        [path for path in EXAMPLES_DIR.iterdir() if path.is_dir()],
        key=lambda path: (example_number(path), path.name),
    )


def print_examples() -> None:
    examples = list_examples()
    if not examples:
        print("Nu exista foldere in examples/.")
        return

    print("Exemple disponibile:")
    for folder in examples:
        marker = "OK" if (folder / FILE_UNDER_TEST).exists() else "lipseste to_test.py"
        print(f"- {folder.name}: {marker}")


def select_example(selector: str) -> Path:
    folder = EXAMPLES_DIR / selector
    if folder.exists() and folder.is_dir():
        return folder
    raise FileNotFoundError(f"Nu exista folderul examples/{selector}.")


def has_test_function(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    content = path.read_text(encoding="utf-8", errors="replace")
    return re.search(r"^\s*def\s+test_[A-Za-z0-9_]+\s*\(", content, re.MULTILINE) is not None


def normalize_selection_to_file(selection: str) -> str:
    normalized = selection.strip()

    aliases = {
        "functional": FUNCTIONAL_TEST_FILE,
        "structural": STRUCTURAL_TEST_FILE,
        "functional_propriu": FUNCTIONAL_TEST_FILE,
        "structural_propriu": STRUCTURAL_TEST_FILE,
    }

    if normalized in aliases:
        return aliases[normalized]
    if normalized.endswith(".py"):
        return normalized
    if normalized.startswith("test_"):
        return f"{normalized}.py"
    return f"test_{normalized}.py"


def select_tests(folder: Path, selection: str) -> list[str]:
    if selection == "all":
        candidates = [FUNCTIONAL_TEST_FILE, STRUCTURAL_TEST_FILE]
        return [file_name for file_name in candidates if has_test_function(folder / file_name)]

    file_name = normalize_selection_to_file(selection)
    path = folder / file_name

    if not path.exists():
        raise FileNotFoundError(f"Fisierul de teste nu exista in {folder}: {file_name}")
    if not has_test_function(path):
        raise ValueError(f"Fisierul nu contine functii test_: {file_name}")

    return [file_name]


def safe_remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def clean_runtime(folder: Path) -> int:
    removed = 0

    temp_dirs = [
        path
        for path in folder.rglob("*")
        if path.is_dir() and path.name in TEMP_DIR_NAMES
    ]

    for path in sorted(temp_dirs, key=lambda item: len(item.parts), reverse=True):
        safe_remove_path(path)
        removed += 1

    for pattern in TEMP_FILE_PATTERNS:
        for path in folder.rglob(pattern):
            if path.is_file():
                safe_remove_path(path)
                removed += 1

    return removed


def run_command(folder: Path, command: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=folder,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )


def write_mutmut_config(folder: Path, test_files: list[str]) -> tuple[bool, str]:
    pyproject = folder / "pyproject.toml"
    previous_content = pyproject.read_text(encoding="utf-8") if pyproject.exists() else ""
    had_file = pyproject.exists()
    quoted = ", ".join(f'"{name}"' for name in test_files)

    pyproject.write_text(
        "[tool.mutmut]\n"
        f'paths_to_mutate = ["{FILE_UNDER_TEST}"]\n'
        f"pytest_add_cli_args_test_selection = [{quoted}]\n"
        'pytest_add_cli_args = ["-q"]\n'
        "debug = true\n",
        encoding="utf-8",
    )

    return had_file, previous_content


def restore_mutmut_config(folder: Path, had_file: bool, previous_content: str) -> None:
    pyproject = folder / "pyproject.toml"
    if had_file:
        pyproject.write_text(previous_content, encoding="utf-8")
    elif pyproject.exists():
        pyproject.unlink()


def parse_mutmut_score(run_output: str, results_output: str) -> tuple[int, int, int, float]:
    total = 0
    for line in reversed(run_output.splitlines()):
        match = re.search(r"(\d+)\s*/\s*(\d+)", line)
        if match and match.group(1) == match.group(2):
            total = int(match.group(2))
            break

    unresolved = 0
    unresolved_suffixes = (
        ": survived",
        ": timeout",
        ": suspicious",
        ": skipped",
        ": not checked",
    )

    for line in results_output.splitlines():
        lowered = line.strip().lower()
        if any(lowered.endswith(suffix) for suffix in unresolved_suffixes):
            unresolved += 1

    killed = max(total - unresolved, 0)
    score = round(killed * 100 / total, 2) if total else 0.0
    return total, killed, unresolved, score


def print_output(title: str, output: str, max_lines: int = 60) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    if not lines:
        print("(fara output)")
        return
    for line in lines[:max_lines]:
        print(line)
    if len(lines) > max_lines:
        print(f"... output trunchiat: inca {len(lines) - max_lines} linii")


def print_mutmut_summary(mutmut_run: subprocess.CompletedProcess[str], mutmut_results: subprocess.CompletedProcess[str]) -> None:
    print("\nMutmut")
    print("------")
    if mutmut_run.returncode == 0 and mutmut_results.returncode == 0:
        print("rulare finalizata")
        return

    print("rulare terminata cu erori; fragment de output:")
    print_output("Mutmut output", mutmut_run.stdout + "\n" + mutmut_results.stdout, max_lines=25)


def run_proprii(folder: Path, selection: str, clean_after: bool) -> None:
    if not (folder / FILE_UNDER_TEST).exists():
        raise FileNotFoundError(f"Lipseste {FILE_UNDER_TEST} in {folder}")

    test_files = select_tests(folder, selection)
    if not test_files:
        raise ValueError("Nu exista fisiere de teste proprii selectabile in exemplu.")

    print(f"Exemplu: {folder}")
    print(f"Teste proprii selectate: {', '.join(test_files)}")
    print("Testele sunt rulate direct din folderul exemplului, fara copiere in root.")

    clean_runtime(folder)

    pytest_result = run_command(folder, [PYTHON, "-m", "pytest", "-q", *test_files], timeout=180)
    print_output("Pytest", pytest_result.stdout)

    coverage_result = run_command(
        folder,
        [PYTHON, "-m", "coverage", "run", "--branch", "-m", "pytest", "-q", *test_files],
        timeout=180,
    )
    coverage_report = run_command(folder, [PYTHON, "-m", "coverage", "report", "-m", FILE_UNDER_TEST], timeout=180)
    print_output("Coverage", coverage_result.stdout + "\n" + coverage_report.stdout)

    had_pyproject, previous_content = write_mutmut_config(folder, test_files)
    try:
        mutmut_run = run_command(folder, ["mutmut", "run"], timeout=600)
        mutmut_results = run_command(folder, ["mutmut", "results"], timeout=180)
    finally:
        restore_mutmut_config(folder, had_pyproject, previous_content)

    total, killed, unresolved, score = parse_mutmut_score(mutmut_run.stdout, mutmut_results.stdout)
    print_mutmut_summary(mutmut_run, mutmut_results)

    print("\nRezumat")
    print("-------")
    print(f"Exemplu: {folder.name}")
    print(f"Selectie: {selection}")
    print(f"Teste: {', '.join(test_files)}")
    print(f"Pytest return code: {pytest_result.returncode}")
    print(f"Coverage return code: {coverage_result.returncode}")
    print(f"Mutmut return code: {mutmut_run.returncode}")
    print(f"Mutanti total: {total}")
    print(f"Mutanti omorati: {killed}")
    print(f"Mutanti nerezolvati: {unresolved}")
    print(f"Mutation score: {score}%")

    if clean_after:
        removed = clean_runtime(folder)
        print(f"Cleanup temporar: efectuat ({removed} elemente sterse)")
    else:
        print("Cleanup temporar: sarit la cerere")


def main() -> None:
    args = parse_args()

    if args.list:
        print_examples()
        return

    try:
        folder = select_example(args.example)
        run_proprii(folder, args.selection, clean_after=not args.no_clean_after)
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
