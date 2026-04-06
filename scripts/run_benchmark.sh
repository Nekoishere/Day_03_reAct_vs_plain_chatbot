#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for benchmark_football.py
# Usage examples:
#   ./scripts/run_benchmark.sh
#   ./scripts/run_benchmark.sh --mode react --tool-mode web --question "Ai vo dich World Cup 2018?"
#   ./scripts/run_benchmark.sh --provider google --model gemini-1.5-flash

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

if [[ "${1:-}" == "--help-script" ]]; then
  cat <<'EOF'
run_benchmark.sh - Friendly wrapper for src.benchmark_football

Common usage:
  ./scripts/run_benchmark.sh
  ./scripts/run_benchmark.sh --mode baseline
  ./scripts/run_benchmark.sh --mode react --tool-mode web
  ./scripts/run_benchmark.sh --mode both --tool-mode hybrid --run-tag exp01
  ./scripts/run_benchmark.sh --mode react --question "Ai vo dich World Cup 2018?"
  ./scripts/run_benchmark.sh --mode react --ui-input

Pass-through:
  All arguments are forwarded to:
    python -m src.benchmark_football
EOF
  exit 0
fi

exec "$PYTHON_BIN" -m src.benchmark_football "$@"
