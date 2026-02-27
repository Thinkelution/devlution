.PHONY: install dev test lint typecheck clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check .

lint-fix:
	ruff check . --fix

typecheck:
	mypy devlution/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build:
	python -m build

all: lint typecheck test
