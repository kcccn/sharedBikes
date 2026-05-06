#!/usr/bin/env bash
set -euo pipefail

echo "==> Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing dependencies..."
pip install -e ".[dev]"

echo "==> Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install 2>/dev/null || echo "(pre-commit config optional)"

echo "==> Done! Activate with: source .venv/bin/activate"
