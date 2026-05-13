#!/usr/bin/env bash
set -euo pipefail

# Ruleaza manual pytest, coverage si mutmut pe un folder din arh/.
# Utilizare:
#   ./run_manual.sh 1              # ruleaza toate testele din arhiva 1
#   ./run_manual.sh 2 functional   # ruleaza doar test_functional.py din arhiva 2
#   ./run_manual.sh 3 structural   # ruleaza doar test_structural.py din arhiva 3
#   ./run_manual.sh latest all     # ruleaza ultima arhiva
#
# Dupa rulare, artefactele temporare din arhiva testata sunt sterse automat
# (__pycache__, .pytest_cache, .coverage, htmlcov, mutants, .mutmut-cache).
# Folderul arhivei si fisierele de test raman pastrate.
#
# Interpretare:
#   1 = prima / cea mai veche arhiva, daca folderele arh/ sunt numerotate cronologic.
#   2 = a doua arhiva etc.

ARCHIVE_SELECTOR="${1:-}"
SELECTION="${2:-all}"
EXTRA_ARG="${3:-}"

if [[ -z "${ARCHIVE_SELECTOR}" ]]; then
    echo "Utilizare: ./run_manual.sh <numar_arhiva|latest> [all|functional|structural|test_file.py] [--no-clean-after]"
    echo "Exemple:"
    echo "  ./run_manual.sh 1"
    echo "  ./run_manual.sh 2 functional"
    echo "  ./run_manual.sh latest all"
    exit 1
fi

echo "[1/2] Verific fisierele Python..."
python3 -m compileall -q AutoTesting.py manual_testing.py reset.py run_examples.py run_arh_manual.py config.py Includes

echo "[2/2] Rulez manual arhiva '${ARCHIVE_SELECTOR}', selectie '${SELECTION}'..."
if [[ -n "${EXTRA_ARG}" ]]; then
    python3 run_arh_manual.py "${ARCHIVE_SELECTOR}" "${SELECTION}" "${EXTRA_ARG}"
else
    python3 run_arh_manual.py "${ARCHIVE_SELECTOR}" "${SELECTION}"
fi
