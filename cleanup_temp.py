#!/usr/bin/env python3
"""
Sterge artefactele temporare create de pytest, coverage si mutmut.

Curata recursiv root-ul proiectului si toate subfolderele lui, fara sa stearga
arhivele, logurile, testele generate sau fisierele sursa.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


# Directoare temporare care pot fi sterse oriunde apar in proiect.
TEMP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    "mutants",
    ".mutmut-cache",
}

# Fisiere temporare care pot fi sterse oriunde apar in proiect.
TEMP_FILE_NAMES = {
    ".coverage",
    "__validate_temp__.py",
    "__autotesting_pyproject_backup__.tmp",
}

# Prefixe de fisiere temporare.
TEMP_FILE_PREFIXES = (
    ".coverage.",
)

# Foldere care nu trebuie traversate. Nu sunt artefacte de testare.
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
}


def is_temp_file(path: Path) -> bool:
    """Returneaza True daca fisierul este un artefact temporar cunoscut."""
    name = path.name
    return name in TEMP_FILE_NAMES or any(name.startswith(prefix) for prefix in TEMP_FILE_PREFIXES)


def collect_temp_paths(root: Path) -> list[Path]:
    """Colecteaza artefactele temporare din root si din toate subfolderele."""
    found: list[Path] = []

    for path in root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue

        if path.is_dir() and path.name in TEMP_DIR_NAMES:
            found.append(path)
            continue

        if path.is_file() and is_temp_file(path):
            found.append(path)

    # Stergem intai caile mai adanci, ca sa evitam stergerea unui copil dupa parinte.
    found.sort(key=lambda item: len(item.parts), reverse=True)
    return found


def remove_paths(paths: list[Path], dry_run: bool = False) -> int:
    """Sterge caile primite si returneaza cate elemente au fost sterse."""
    removed = 0

    for path in paths:
        if not path.exists():
            continue

        if dry_run:
            removed += 1
            print(path)
            continue

        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

        removed += 1

    return removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Curata artefactele temporare din root si din toate subfolderele proiectului."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root-ul proiectului care trebuie curatat. Implicit: directorul curent.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afiseaza ce ar fi sters, fara sa stearga efectiv.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Nu afiseaza mesajul final daca nu este dry-run.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = collect_temp_paths(root)
    removed = remove_paths(paths, dry_run=args.dry_run)

    if not args.quiet and not args.dry_run:
        print(f"Cleanup temporar: efectuat ({removed} elemente sterse)")


if __name__ == "__main__":
    main()
