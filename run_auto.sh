#!/usr/bin/env bash
set -euo pipefail

# Ruleaza fluxul automat complet pe un exemplu din folderul examples/.
# Utilizare:
#   ./run_auto.sh        # foloseste exemplul 1
#   ./run_auto.sh 2      # foloseste exemplul 2
#   ./run_auto.sh 3      # foloseste exemplul 3

EXAMPLE_NUMBER="${1:-1}"

echo "[1/3] Verific fisierele Python..."
python3 -m compileall -q AutoTesting.py manual_testing.py reset.py run_examples.py run_arh_manual.py config.py Includes

echo "[2/3] Pregatesc exemplul ${EXAMPLE_NUMBER}..."
python3 run_examples.py "${EXAMPLE_NUMBER}"

echo "[3/3] Pornesc AutoTesting..."
python3 AutoTesting.py
