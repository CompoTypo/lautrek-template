.PHONY: help dev test lint format clean

help:
	@echo "Commands: dev, test, lint, format, clean"

dev:
	cd server && uv run uvicorn src.api.main:app --reload --port 8080

test:
	cd server && uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format . && uv run ruff check --fix .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
