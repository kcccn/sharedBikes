.PHONY: install test lint format run clean

install:
	pip install -r backend/requirements.txt

test:
	python -m pytest backend/tests/ -v

lint:
	ruff check backend/
	ruff format --check backend/

format:
	ruff format backend/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov
