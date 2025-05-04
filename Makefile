.PHONY: setup test lint format
## Setup development and test environment
setup:
	python3 -m pip install --upgrade pip
	# Install development and test dependencies
	pip install ".[dev,test]"

## Run the full test suite
test:
	python3 -m pytest

## Run all configured pre-commit hooks
lint:
	pre-commit run --all-files

## Format code with Black
format:
	black .