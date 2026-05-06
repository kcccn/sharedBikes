.PHONY: install test lint format clean run

install:
	pip install -e ".[dev]"

test:
	python -m pytest

test-verbose:
	python -m pytest -v --tb=short

lint:
	ruff check backend/

format:
	ruff format backend/

check: lint test

run:
	uvicorn app.main:app --reload

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
