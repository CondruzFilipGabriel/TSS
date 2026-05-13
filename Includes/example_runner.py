from __future__ import annotations

"""
example_runner.py

Rol
---
Ofera un orchestrator mic pentru testarea framework-ului pe exemplele din
folderul examples/. Modulul poate copia un exemplu in to_test.py, poate reseta
workspace-ul si, optional, poate porni AutoTesting.py sau manual_testing.py.

Scopul lui este sa permita verificarea repetabila a celor trei functii de test
fara modificari manuale ale fisierului to_test.py.
"""

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"
TO_TEST_PATH = ROOT / "to_test.py"
BACKUP_PATH = ROOT / "to_test.backup_before_example_runner.py"
RUN_LOG_DIR = ROOT / "logs" / "example_runs"


@dataclass(frozen=True)
class ExampleRunOptions:
    """Optiunile efective pentru o rulare pe exemple."""

    selection: str
    run_autotesting: bool
    run_manual: bool
    manual_selection: str
    force_backup_overwrite: bool


def build_parser() -> argparse.ArgumentParser:
    """Construieste parserul CLI pentru run_examples.py."""
    parser = argparse.ArgumentParser(
        description=(
            "Copiaza un exemplu din examples/<id>/to_test.py in root si, optional, "
            "ruleaza AutoTesting.py sau manual_testing.py."
        )
    )
    parser.add_argument(
        "selection",
        nargs="?",
        default="list",
        help="Exemplul de rulat: 1, 2, 3, all sau list. Default: list.",
    )
    parser.add_argument(
        "--run-autotesting",
        action="store_true",
        help="Dupa pregatirea exemplului, ruleaza python3 AutoTesting.py.",
    )
    parser.add_argument(
        "--run-manual",
        action="store_true",
        help="Dupa pregatirea exemplului, ruleaza python3 manual_testing.py.",
    )
    parser.add_argument(
        "--manual-selection",
        default="all",
        help="Selectia transmisa catre manual_testing.py. Default: all.",
    )
    parser.add_argument(
        "--force-backup-overwrite",
        action="store_true",
        help="Permite suprascrierea backupului to_test.backup_before_example_runner.py.",
    )
    return parser


def get_available_examples() -> list[str]:
    """Returneaza exemplele disponibile care contin un fisier to_test.py."""
    if not EXAMPLES_DIR.exists():
        return []

    examples: list[str] = []
    for example_dir in sorted(EXAMPLES_DIR.iterdir()):
        if example_dir.is_dir() and (example_dir / "to_test.py").exists():
            examples.append(example_dir.name)
    return examples


def print_available_examples() -> None:
    """Afiseaza exemplele disponibile."""
    examples = get_available_examples()
    if not examples:
        print("Nu exista exemple valide in folderul examples/.")
        return

    print("Exemple disponibile:")
    for example_id in examples:
        print(f"  - {example_id}: examples/{example_id}/to_test.py")


def resolve_selection(selection: str) -> list[str]:
    """Transforma selectia CLI intr-o lista de exemple concrete."""
    available = get_available_examples()

    if selection == "list":
        return []
    if selection == "all":
        return available
    if selection in available:
        return [selection]

    raise ValueError(
        "Selectie invalida. Foloseste unul dintre: "
        + ", ".join(["list", "all", *available])
    )


def backup_existing_to_test(force_overwrite: bool) -> None:
    """Salveaza o copie a fisierului to_test.py curent, daca exista."""
    if not TO_TEST_PATH.exists():
        return

    if BACKUP_PATH.exists() and not force_overwrite:
        return

    shutil.copy2(TO_TEST_PATH, BACKUP_PATH)


def copy_example_to_root(example_id: str, force_backup_overwrite: bool) -> Path:
    """Copiaza examples/<id>/to_test.py in root/to_test.py."""
    source_path = EXAMPLES_DIR / example_id / "to_test.py"
    if not source_path.exists():
        raise FileNotFoundError(f"Nu exista exemplul: {source_path}")

    backup_existing_to_test(force_backup_overwrite)
    shutil.copy2(source_path, TO_TEST_PATH)
    return source_path


def run_command(command: list[str], log_file: Path | None = None) -> int:
    """Ruleaza o comanda si, optional, salveaza stdout/stderr intr-un fisier."""
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("w", encoding="utf-8") as handle:
            process = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                stdout=handle,
                stderr=subprocess.STDOUT,
                check=False,
            )
        return process.returncode

    process = subprocess.run(command, cwd=ROOT, check=False)
    return process.returncode


def reset_workspace() -> int:
    """Ruleaza reset.py dupa copierea exemplului."""
    return run_command([sys.executable, "reset.py"])


def run_example(example_id: str, options: ExampleRunOptions) -> int:
    """Pregateste si ruleaza, dupa caz, un exemplu."""
    print(f"\n=== Exemplul {example_id} ===")
    source_path = copy_example_to_root(
        example_id=example_id,
        force_backup_overwrite=options.force_backup_overwrite,
    )
    print(f"Copiat: {source_path} -> {TO_TEST_PATH}")

    reset_code = reset_workspace()
    if reset_code != 0:
        print(f"Resetarea workspace-ului a esuat pentru exemplul {example_id}.")
        return reset_code

    final_code = 0

    if options.run_autotesting:
        log_file = RUN_LOG_DIR / f"example_{example_id}_autotesting.log"
        print(f"Rulez AutoTesting.py. Log: {log_file}")
        final_code = run_command([sys.executable, "AutoTesting.py"], log_file)
        print(f"AutoTesting.py exit code: {final_code}")
        if final_code != 0:
            return final_code

    if options.run_manual:
        log_file = RUN_LOG_DIR / f"example_{example_id}_manual_testing.log"
        print(f"Rulez manual_testing.py {options.manual_selection}. Log: {log_file}")
        final_code = run_command(
            [sys.executable, "manual_testing.py", options.manual_selection],
            log_file,
        )
        print(f"manual_testing.py exit code: {final_code}")

    if not options.run_autotesting and not options.run_manual:
        print("Exemplul a fost doar pregatit. Ruleaza python3 AutoTesting.py cand doresti.")

    return final_code


def main() -> None:
    """Punct de intrare pentru run_examples.py."""
    parser = build_parser()
    args = parser.parse_args()

    if args.selection == "list":
        print_available_examples()
        return

    try:
        selected_examples = resolve_selection(args.selection)
    except ValueError as error:
        print(error)
        raise SystemExit(2) from error

    options = ExampleRunOptions(
        selection=args.selection,
        run_autotesting=args.run_autotesting,
        run_manual=args.run_manual,
        manual_selection=args.manual_selection,
        force_backup_overwrite=args.force_backup_overwrite,
    )

    exit_code = 0
    for example_id in selected_examples:
        current_code = run_example(example_id, options)
        if current_code != 0:
            exit_code = current_code
            break

    raise SystemExit(exit_code)
