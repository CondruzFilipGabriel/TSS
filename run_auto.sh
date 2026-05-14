#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

EXEMPLU="${1:-1}"

cleanup_temp() {
    python3 cleanup_temp.py --root "$ROOT_DIR" --quiet || true
}

cleanup_temp
trap 'cleanup_temp; echo "[cleanup] Fisiere temporare sterse din root si din toate subfolderele. Arhiva si logurile au fost pastrate."' EXIT

echo "[1/3] Verific fisierele Python..."
python3 -m compileall -q AutoTesting.py manual_testing.py reset.py run_examples.py run_arh_manual.py config.py cleanup_temp.py Includes

echo "[2/3] Pregatesc exemplul ${EXEMPLU}..."
python3 run_examples.py "$EXEMPLU"

echo "[3/3] Pornesc AutoTesting..."
python3 AutoTesting.py
