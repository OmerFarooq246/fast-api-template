.PHONY: check check-text coverage format lint test typecheck

UV ?= uv

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

lint:
	$(UV) run ruff format --check .
	$(UV) run ruff check .

check-text:
	$(UV) run python scripts/check_no_em_dash.py

typecheck:
	$(UV) run mypy app tests

test:
	$(UV) run pytest

coverage:
	$(UV) run pytest --cov=app --cov-report=term-missing --cov-report=xml

check: check-text lint typecheck test
