#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CLEAN_AFTER=1
ARGS=()

for arg in "$@"; do
    if [[ "$arg" == "--no-clean-after" ]]; then
        CLEAN_AFTER=0
        ARGS+=("$arg")
    else
        ARGS+=("$arg")
    fi
done

cleanup_temp() {
    python3 cleanup_temp.py --root "$ROOT_DIR" --quiet || true
}

cleanup_temp

if [[ "$CLEAN_AFTER" -eq 1 ]]; then
    trap 'cleanup_temp; echo "[cleanup] Fisiere temporare sterse din root si din toate subfolderele. Arhiva si logurile au fost pastrate."' EXIT
fi

echo "[1/2] Verific fisierele Python..."
python3 -m compileall -q AutoTesting.py manual_testing.py reset.py run_examples.py run_arh_manual.py run_proprii.py config.py cleanup_temp.py Includes examples

echo "[2/2] Rulez testele proprii pentru exemplul '${ARGS[0]:-1}', selectie '${ARGS[1]:-all}'..."
python3 run_proprii.py "${ARGS[@]}"

if [[ "$CLEAN_AFTER" -eq 0 ]]; then
    echo "[cleanup] Dezactivat pentru aceasta rulare (--no-clean-after)."
fi
