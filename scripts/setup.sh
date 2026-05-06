#!/usr/bin/env bash
set -euo pipefail

echo "=== CityBike-Sim Setup ==="

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Install pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    pre-commit install
fi

echo "=== Setup complete ==="
echo "Run 'source .venv/bin/activate' to activate, then 'make run' to start."
