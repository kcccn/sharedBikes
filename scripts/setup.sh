#!/usr/bin/env bash
set -euo pipefail

echo "🚲 Setting up CityBike-Sim development environment..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt 2>/dev/null || true

echo "✅ Setup complete. Activate with: source .venv/bin/activate"
