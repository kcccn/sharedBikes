#!/usr/bin/env bash
set -euo pipefail

echo "🚲 CityBike-Sim setup"

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"

echo "✅ Setup complete. Run 'make run' to start the API server."
