.PHONY: install test lint format clean run

install:
	pip install -e "backend/[dev]"

test:
	python -m pytest backend/tests/ -v

lint:
	ruff check backend/

format:
	ruff format backend/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
