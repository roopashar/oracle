.PHONY: help install install-dev test test-unit test-integration lint format clean docs

help:
	@echo "Oracle Test Library - Makefile Commands"
	@echo ""
	@echo "install          - Install the package"
	@echo "install-dev      - Install with development dependencies"
	@echo "test             - Run all tests"
	@echo "test-unit        - Run unit tests only"
	@echo "test-integration - Run integration tests (requires DB)"
	@echo "lint             - Run code linting"
	@echo "format           - Format code with black"
	@echo "clean            - Clean build artifacts"
	@echo "docs             - Generate documentation"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,viz,all]"

test:
	pytest test_oracle_lib.py -v --cov=oracle_test_lib --cov-report=html

test-unit:
	pytest test_oracle_lib.py -v -m "not integration"

test-integration:
	pytest test_oracle_lib.py -v -m integration

lint:
	flake8 oracle_test_lib.py --max-line-length=100
	mypy oracle_test_lib.py --ignore-missing-imports

format:
	black oracle_test_lib.py examples.py oracle_test_cli.py test_oracle_lib.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

docs:
	@echo "Generating documentation..."
	@echo "Documentation is in README.md"
