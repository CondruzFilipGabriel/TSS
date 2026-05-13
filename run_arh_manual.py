from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = ROOT_DIR / "arh"
PYTHON = "python3"
FILE_UNDER_TEST = "to_test.py"
PROPOSAL_FILE = "test_propunere.py"


def archive_number(path: Path) -> int:
    try:
        return int(path.name.split(" ", 1)[0])
    except (ValueError, IndexError):
        return -1


def list_archives() -> list[Path]:
    if not ARCHIVE_DIR.exists():
        return []
    folders = [p for p in ARCHIVE_DIR.iterdir() if p.is_dir()]
    return sorted(folders, key=lambda p: (archive_number(p), p.name))


def find_archive(selector: str) -> Path:
    archives = list_archives()
    if not archives:
        raise FileNotFoundError("Nu exista foldere in arh/.")

    if selector == "latest":
        return archives[-1]

    if selector.isdigit():
        for folder in archives:
            if archive_number(folder) == int(selector):
                return folder
        raise FileNotFoundError(f"Nu exista arhiva cu numarul {selector}.")

    candidate = ARCHIVE_DIR / selector
    if candidate.exists() and candidate.is_dir():
        return candidate

    raise FileNotFoundError(f"Nu am gasit arhiva: {selector}")


def has_test_function(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    content = path.read_text(encoding="utf-8", errors="replace")
    return re.search(r"^\s*def\s+test_[A-Za-z0-9_]+\s*\(", content, re.M) is not None


def select_tests(folder: Path, selection: str) -> list[str]:
    if selection == "all":
        files = []
        for path in sorted(folder.glob("test_*.py")):
            if path.name == PROPOSAL_FILE:
                continue
            if has_test_function(path):
                files.append(path.name)
        return files

    if selection.endswith(".py"):
        file_name = selection
    elif selection.startswith("test_"):
        file_name = selection + ".py"
    else:
        file_name = f"test_{selection}.py"

    path = folder / file_name
    if not path.exists():
        raise FileNotFoundError(f"Fisierul de teste nu exista in arhiva: {file_name}")
    if not has_test_function(path):
        raise ValueError(f"Fisierul nu contine functii test_: {file_name}")
    return [file_name]


def clean_runtime(folder: Path) -> None:
    """Sterge artefactele temporare create prin pytest, coverage si mutmut.

    Folderul arhivei ramane intact. Sunt sterse doar fisiere/foldere
    generate automat in timpul rularilor manuale.
    """
    root_artifacts = ["mutants", ".mutmut-cache", ".pytest_cache", "htmlcov"]
    root_files = [".coverage"]

    for name in root_artifacts:
        path = folder / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    for name in root_files:
        path = folder / name
        if path.exists():
            path.unlink()

    # __pycache__ poate aparea in radacina arhivei sau in subfoldere
    # create temporar de instrumentele de testare.
    for cache_dir in folder.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir)

    # Coverage poate crea fisiere .coverage.* in anumite contexte.
    for coverage_file in folder.glob(".coverage.*"):
        if coverage_file.is_file():
            coverage_file.unlink()


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
        "debug = false\n",
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
    for line in results_output.splitlines():
        lowered = line.strip().lower()
        if lowered.endswith((": survived", ": timeout", ": suspicious", ": skipped", ": not checked")):
            unresolved += 1

    killed = max(total - unresolved, 0)
    score = round(killed * 100 / total, 2) if total else 0.0
    return total, killed, unresolved, score


def print_output(title: str, output: str, max_lines: int = 60) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    for line in lines[:max_lines]:
        print(line)
    if len(lines) > max_lines:
        print(f"... output trunchiat: inca {len(lines) - max_lines} linii")


def run_manual(folder: Path, selection: str, clean_after: bool) -> None:
    if not (folder / FILE_UNDER_TEST).exists():
        raise FileNotFoundError(f"Lipseste {FILE_UNDER_TEST} in {folder}")

    test_files = select_tests(folder, selection)
    if not test_files:
        raise ValueError("Nu exista fisiere de teste selectabile in arhiva.")

    print(f"Arhiva: {folder}")
    print(f"Teste selectate: {', '.join(test_files)}")

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
    mutmut_run = None
    mutmut_results = None
    try:
        mutmut_run = run_command(folder, ["mutmut", "run"], timeout=600)
        mutmut_results = run_command(folder, ["mutmut", "results"], timeout=180)
    except FileNotFoundError:
        print("\nMutmut")
        print("------")
        print("executabilul mutmut nu a fost gasit")
        total, killed, unresolved, score = 0, 0, 0, 0.0
    finally:
        restore_mutmut_config(folder, had_pyproject, previous_content)

    if mutmut_run is not None and mutmut_results is not None:
        total, killed, unresolved, score = parse_mutmut_score(mutmut_run.stdout, mutmut_results.stdout)
        if mutmut_run.returncode != 0:
            print_output("Mutmut", mutmut_run.stdout + "\n" + mutmut_results.stdout, max_lines=25)
        else:
            print("\nMutmut")
            print("------")
            print("rulare finalizata")

    print("\nRezumat")
    print("-------")
    print(f"Pytest return code: {pytest_result.returncode}")
    print(f"Coverage return code: {coverage_result.returncode}")
    print(f"Mutanti total: {total}")
    print(f"Mutanti omorati: {killed}")
    print(f"Mutanti nerezolvati: {unresolved}")
    print(f"Mutation score: {score}%")

    if clean_after:
        clean_runtime(folder)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ruleaza manual pytest, coverage si mutmut pe o arhiva din arh/.")
    parser.add_argument("archive", nargs="?", default="latest", help="latest, numar arhiva sau nume folder din arh/.")
    parser.add_argument("selection", nargs="?", default="all", help="all, functional, structural sau nume fisier test_*.py.")
    parser.add_argument("--list", action="store_true", help="Afiseaza arhivele disponibile si iese.")
    parser.add_argument(
        "--no-clean-after",
        action="store_true",
        help="Pastreaza artefactele temporare dupa testare, pentru depanare.",
    )
    args = parser.parse_args()

    if args.list:
        archives = list_archives()
        if not archives:
            print("Nu exista arhive in arh/.")
            return
        for folder in archives:
            print(f"{archive_number(folder)}: {folder.name}")
        return

    folder = find_archive(args.archive)
    run_manual(folder, args.selection, clean_after=not args.no_clean_after)


if __name__ == "__main__":
    main()
