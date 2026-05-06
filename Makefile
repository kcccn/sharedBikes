.PHONY: install format lint test run

install:
	cd backend && pip install -e ".[dev]"

format:
	ruff format backend/

lint:
	ruff check backend/
	mypy backend/ --ignore-missing-imports

test:
	cd backend && python -m pytest -v --tb=short

run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
