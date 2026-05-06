# Minimal Makefile for development workflow

.PHONY: install lint test run clean

install:
	pip install -e ".[dev]"

lint:
	ruff check backend/
	ruff format --check backend/

format:
	ruff format backend/

test:
	python -m pytest backend/tests/ -v

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
