.PHONY: check format lint test typecheck

UV ?= uv

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

lint:
	$(UV) run ruff format --check .
	$(UV) run ruff check .

typecheck:
	$(UV) run mypy app

test:
	$(UV) run pytest

check: lint typecheck
