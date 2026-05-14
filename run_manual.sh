#!/usr/bin/env bash
set -euo pipefail

archive="${1:-latest}"
selection="all"

if [[ $# -ge 1 ]]; then
  shift
fi

if [[ $# -ge 1 && "$1" != --* ]]; then
  selection="$1"
  shift
fi

echo "[1/2] Verific fisierele Python..."
python3 -m compileall -q AutoTesting.py manual_testing.py reset.py run_examples.py run_arh_manual.py config.py Includes

echo "[2/2] Rulez manual arhiva '$archive', selectie '$selection'..."
python3 run_arh_manual.py "$archive" "$selection" "$@"
