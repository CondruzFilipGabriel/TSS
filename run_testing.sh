#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

MODEL="qwen2.5-coder:7b"

if ! curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
    echo "Ollama nu ruleaza. Pornesc serverul..."
    nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
    sleep 3
fi

if ! curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
    echo "Eroare: Ollama nu a pornit corect."
    read -rp "Apasa Enter pentru inchidere..."
    exit 1
fi

aider "$@"
EXIT_CODE=$?

echo
echo "Aider s-a inchis. Oprire model Ollama..."
ollama stop "$MODEL" 2>/dev/null || true

echo "Totul a fost inchis."
read -rp "Apasa Enter pentru inchidere..."
exit "$EXIT_CODE"