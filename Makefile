.PHONY: help install dev-install lint format type-check test test-cov clean migrate run docs

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make lint           - Run code linting (flake8)"
	@echo "  make format         - Format code with black"
	@echo "  make type-check     - Run type checking (mypy)"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make test-quick     - Run quick tests (no coverage)"
	@echo "  make clean          - Clean up temporary files"
	@echo "  make run            - Run development server"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-new    - Create new migration"
	@echo "  make db-drop        - Drop database (development only)"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev,ai]"

lint:
	flake8 src tests

format:
	black src tests
	isort src tests

type-check:
	mypy src

test:
	pytest -v --cov=src --cov-report=html --cov-fail-under=85

test-cov:
	pytest -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated at htmlcov/index.html"

test-quick:
	pytest -x

check-all:
	@echo "Running format check..."
	black --check src tests
	@echo "Running lint check..."
	flake8 src tests
	@echo "Running type check..."
	mypy src
	@echo "Running tests..."
	pytest --cov=src --cov-fail-under=85
	@echo "All checks passed!"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete
	find . -type f -name "*.pyc" -delete

run:
	python -m uvicorn src.main:app --reload

migrate:
	alembic upgrade head

migrate-new:
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

db-drop:
	@echo "WARNING: This will drop the entire database!"
	@read -p "Are you sure? (y/n) " confirm; \
	if [ "$$confirm" = "y" ]; then \
		alembic downgrade base; \
		echo "Database dropped"; \
	fi

docs:
	@echo "Building documentation..."
	mkdocs serve
