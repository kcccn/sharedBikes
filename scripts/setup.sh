#!/usr/bin/env bash
set -euo pipefail

echo "==> Creating Python virtual environment…"
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing backend with dev dependencies…"
cd backend
pip install -e ".[dev]"
cd ..

echo "==> Installing pre-commit hook (ruff)…"
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/sh
ruff check backend/ --fix
ruff format backend/
HOOK
chmod +x .git/hooks/pre-commit

echo "==> Done. Run 'source .venv/bin/activate' to start."
