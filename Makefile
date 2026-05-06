.PHONY: install test lint format clean

install:
	pip install -e ".[dev]"

test:
	python -m pytest

test-verbose:
	python -m pytest -v --tb=long

lint:
	ruff check .

lint-fix:
	ruff check --fix .

format:
	ruff format .

check: lint test

clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/
	rm -rf .coverage
	rm -rf htmlcov/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
