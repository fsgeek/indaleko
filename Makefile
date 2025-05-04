.PHONY: setup test lint format
## Setup development and test environment
setup:
	# Use uv via setup_env to install and lock dependencies
	python3 utils/setup_env.py --reset-lock-file

test:
## Run the full test suite
test:
	# Use uv to run pytest in the venv
	# Use uv to run pytest in the venv
	uv run pytest

## Run all configured pre-commit hooks
lint:
	# Use uv to run pre-commit in the venv
	# Use uv to run pre-commit in the venv
	uv run pre-commit run --all-files

## Format code with Black
format:
	# Use uv to run black in the venv
	# Use uv to run black in the venv
	uv run black .

## Type-check with mypy
mypy:
	# Use uv to run mypy in the venv
	# Use uv to run mypy in the venv
	uv run mypy .

## Coverage report
coverage:
	# Use uv to run coverage in the venv
	# Use uv to run coverage in the venv
	uv run coverage run -m pytest
	uv run coverage report