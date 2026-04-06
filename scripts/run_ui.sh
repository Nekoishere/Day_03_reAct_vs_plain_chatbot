#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  echo "[ERROR] Missing .env file."
  echo "Run: cp .env.example .env"
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  echo "[WARN] .venv not found. Using system Python."
  PYTHON_BIN="python"
else
  PYTHON_BIN=".venv/bin/python"
fi

echo "Starting UI at http://127.0.0.1:7860"
exec "$PYTHON_BIN" -m src.ui.app
