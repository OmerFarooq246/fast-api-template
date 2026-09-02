# FastAPI Template

A production-oriented, asynchronous FastAPI template with PostgreSQL, SQLAlchemy 2,
Alembic, typed settings, JWT authentication, rotating refresh tokens, and a complete
local/CI quality workflow.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL

## Quick start

```bash
uv sync --locked
cp env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

The API documentation is available at `http://localhost:8000/docs`.

Install the managed Git hooks and run all local checks:

```bash
uv run pre-commit install --install-hooks
make check
```

## Common commands

| Command | Purpose |
| --- | --- |
| `make format` | Apply Ruff lint fixes and formatting |
| `make lint` | Check formatting and lint rules without modifying files |
| `make typecheck` | Run strict mypy checks |
| `make test` | Run the complete pytest suite |
| `make check` | Run text-policy, formatting, linting, type, and test checks |
| `make coverage` | Run tests and generate terminal/XML coverage reports |
| `uv run alembic upgrade head` | Apply all database migrations |
| `uv run alembic check` | Detect model changes missing from migrations |

Integration tests read `TEST_DATABASE_URI` from the process environment first (including
values set with `export` or by CI) and fall back to `.env`. The URI must identify a
dedicated PostgreSQL database whose name contains `test`. Export it when applying
migrations so Alembic can temporarily use the same database through `DATABASE_URI`:

```bash
source .venv/bin/activate
export TEST_DATABASE_URI=postgresql+asyncpg://postgres:postgres@localhost/fast_api_template_test
DATABASE_URI="$TEST_DATABASE_URI" alembic upgrade head
pytest -m integration
```

Create and synchronize `.venv` with `uv sync --locked` first if it does not already exist.
PostgreSQL must be running, and the test database must already exist before applying its
migrations. Never point `TEST_DATABASE_URI` at a development, staging, or production
database.

## Configuration

Settings are read from environment variables and an optional `.env` file. See
[`env.example`](env.example) for the complete list.

### Environment modes

`ENVIRONMENT` accepts `local`, `test`, `staging`, or `production`. It selects the
configuration validation mode; it does not load a separate configuration profile or
automatically change settings such as `DEBUG`, `DATABASE_URI`, `CORS_ORIGINS`, or
`LOG_FORMAT`.

| Value | Behavior |
| --- | --- |
| `local` | Default mode for local development. The development secret is accepted. |
| `test` | Intended for automated tests. It has the same secret validation as `local`; selecting it does not automatically use `TEST_DATABASE_URI`. Unit tests inject their own settings, while PostgreSQL integration tests read `TEST_DATABASE_URI` from the process environment or `.env`. |
| `staging` | Startup fails if `SECRET_KEY` is still the development default or contains fewer than 32 characters. |
| `production` | Enforces the same strong-secret requirement as `staging`. Production-safe database credentials, CORS origins, logging, and JWT identifiers must still be configured explicitly. |

In every mode, `DATABASE_URI` must use the `postgresql+asyncpg` driver and include a
database name. Other settings retain their declared defaults unless overridden through the
environment or `.env` file.

Important production requirements:

- Set `ENVIRONMENT=production`.
- Supply a unique `SECRET_KEY` containing at least 32 characters.
- Use a `postgresql+asyncpg://` database URL.
- Restrict `CORS_ORIGINS` to trusted frontends.
- Set `LOG_FORMAT=json` for structured log ingestion.
- Choose stable, application-specific `JWT_ISSUER` and `JWT_AUDIENCE` values.

Staging and production startup fails if the development secret is retained.

## Health and operations

- `GET /health/live` confirms that the process can serve requests. It has no external
  dependency checks.
- `GET /health/ready` verifies PostgreSQL connectivity within
  `READINESS_TIMEOUT_SECONDS`. It returns `503` when the application should be removed
  from service.
- Every HTTP response includes `X-Request-ID`. A valid upstream identifier is preserved;
  otherwise the application generates one.
- Request completion logs include the request ID, method, path, status, and duration.

Run migrations as a separate deployment step before rolling out application instances.
Do not run competing migration commands independently in every web worker.

## Project documentation

- [`docs/architecture.md`](docs/architecture.md) explains application layers,
  transaction ownership, testing, migrations, and how to add a domain module.
- [`docs/security.md`](docs/security.md) documents password storage, JWT claims,
  refresh-token rotation, authorization, and operational security assumptions.

## CI

GitHub Actions runs independent jobs for formatting, linting, strict typing, unit tests
with coverage, PostgreSQL integration tests, the complete Alembic upgrade/downgrade chain,
schema-drift detection, and dependency auditing. Local hooks provide fast feedback; CI is
the authoritative repository-wide check.

## License

See [`LICENSE`](LICENSE).
