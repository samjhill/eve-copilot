.PHONY: help install install-dev test lint format clean build docs

help:  ## Show this help message
	@echo "EVE Copilot - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt

test:  ## Run tests with coverage
	python run_tests.py

test-quick:  ## Run tests without coverage
	pytest tests/ -v

lint:  ## Run linting checks
	flake8 evetalk/ tests/ --max-line-length=100 --ignore=E203,W503
	mypy evetalk/ --ignore-missing-imports

format:  ## Format code with black and isort
	black evetalk/ tests/ --line-length=100
	isort evetalk/ tests/

format-check:  ## Check code formatting without making changes
	black evetalk/ tests/ --line-length=100 --check
	isort evetalk/ tests/ --check-only

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	python setup.py sdist bdist_wheel

docs:  ## Build documentation
	cd docs && make html

run:  ## Run the application
	python app.py

run-debug:  ## Run the application in debug mode
	python app.py --debug

check: format-check lint test  ## Run all quality checks

pre-commit:  ## Install pre-commit hooks
	pre-commit install

update-deps:  ## Update dependencies
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt
