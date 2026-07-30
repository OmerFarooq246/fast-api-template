# FastAPI Template

## Setup

This project uses [uv](https://docs.astral.sh/uv/) to create reproducible
development environments from `pyproject.toml` and `uv.lock`.

```bash
uv sync
cp env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Install the managed Git hooks and run the local quality suite:

```bash
uv run pre-commit install --install-hooks
make check
```

Before generating a migration, import each new model from
`app/models/__init__.py` so Alembic can discover its metadata.
