.PHONY: install test lint format clean run

install:
	pip install -r backend/requirements.txt

test:
	python -m pytest backend/tests/ -v

lint:
	ruff check backend/

format:
	ruff format backend/

run:
	uvicorn backend.app.main:app --reload

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
