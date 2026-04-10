#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <space_url> [repo_dir]"
  exit 1
fi

SPACE_URL="$1"
REPO_DIR="${2:-.}"

cd "$REPO_DIR"

echo "[1/7] Building Docker image..."
if command -v docker >/dev/null 2>&1; then
  docker build -t cybersoc-openenv:validate .
else
  echo "[WARN] Docker CLI not found. Skipping docker build in this dry run."
fi

echo "[2/7] Checking Space health endpoint..."
curl -fsS "${SPACE_URL%/}/health" >/dev/null

echo "[3/7] Checking Space reset endpoint..."
curl -fsS "${SPACE_URL%/}/reset" >/dev/null

echo "[4/7] Checking Space state endpoint..."
curl -fsS "${SPACE_URL%/}/state" >/dev/null

echo "[5/7] Running local environment evaluator..."
python scripts/evaluate_env.py

echo "[6/7] Running local inference baseline..."
python inference.py

echo "[7/7] Basic metadata checks..."
test -f openenv.yaml
test -f scripts/benchmark.py

echo "Validation completed successfully."
