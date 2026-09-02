# AGENTS.md

## Purpose

This file provides repository-specific instructions for AI coding agents working in this project.

The repository is a production-oriented FastAPI template using async SQLAlchemy, PostgreSQL, Alembic, Pydantic settings, JWT authentication, structured logging, and layered application boundaries.

Agents should preserve the existing architecture, safety rules, and contribution workflow rather than introducing alternate patterns without a clear reason.

## Repository workflow

- Never push directly to `main`.
- Create a focused branch for each change and open a pull request.
- Keep changes scoped to one feature, fix, refactor, or documentation task where practical.
- Pull requests should pass CI and receive review before merge.
- Use squash merge.
- Branch names should follow `<type>/<short-kebab-description>`.
- Pull request titles should follow Conventional Commit style:

```text
<type>(<scope>): <summary>
```

Common types include `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`, and `perf`.

Read `CONTRIBUTING.md` before making workflow-sensitive changes.

## Text policy

Do not use em dashes anywhere in repository text.

This includes:

- Python code
- comments
- docstrings
- Markdown
- commit messages
- pull request titles
- pull request descriptions

Use a hyphen, comma, colon, parentheses, or rewrite the sentence.

The repository enforces this rule through pre-commit hooks and CI.

## Architecture

Follow the dependency direction documented in `docs/architecture.md`:

```text
HTTP route -> service/use case -> repository -> SQLAlchemy -> PostgreSQL
     |               |
     |               +-> application/domain exceptions
     +-> schemas, dependencies, and HTTP responses
```

### Routes

Routes should:

- parse and validate HTTP input
- apply reusable FastAPI dependencies
- call services
- shape HTTP responses

Routes should not contain persistence queries or business logic that belongs in services.

### Services

Services should:

- implement application use cases
- coordinate repositories
- enforce business rules
- raise typed application exceptions

Services should not depend on FastAPI request or response types.

### Repositories

Repositories should:

- contain persistence operations
- query, add, update, and delete entities
- call `flush()` when generated values or constraints must be surfaced

Repositories must not commit or roll back transactions.

Transaction ownership belongs to the caller or request boundary.

### Models and schemas

- SQLAlchemy models live under `app/models/`.
- Pydantic request and response schemas live under `app/schemas/`.
- Export new models from `app/models/__init__.py` so Alembic autogeneration can discover them.

## Application construction and lifecycle

`app.main.create_app()` is the application composition root.

Use it when tests or alternate environments need isolated application instances.

Process-level resources such as the database engine are owned by the FastAPI lifespan and attached to `app.state`.

Do not introduce new module-level database engines, sessions, or other process resources that bypass the application lifecycle.

## Database and transaction rules

The database layer uses async SQLAlchemy with PostgreSQL.

`app.db.database.Database.session()` owns a transaction through:

```python
async with session_factory() as session, session.begin():
    ...
```

The FastAPI `get_db` dependency uses this transaction boundary for HTTP requests.

This means:

- successful requests commit when the request-scoped transaction exits
- exceptions roll back the transaction
- repository methods should not call `commit()` or `rollback()`
- multi-repository service operations should remain atomic within the same session

For workers, CLI commands, scheduled jobs, or other non-HTTP consumers, create an equivalent explicit transaction boundary.

Avoid nested or competing transaction owners.

## Configuration

`app.core.config.Settings` is the single source of runtime configuration.

Do not read environment variables directly throughout application code when a setting belongs in `Settings`.

When adding configuration:

1. Add a precise type.
2. Add a safe local default only when appropriate.
3. Use Pydantic validation or constraints.
4. Add the variable to `env.example`.
5. Update relevant documentation.
6. Fail startup for unsafe production values.

Database URIs must use the `postgresql+asyncpg` driver.

Production and staging secrets must not use the development default.

## Test database safety

Integration tests must use a dedicated test database.

The repository currently separates normal application configuration from integration test configuration through `TEST_DATABASE_URI`.

Important rules:

- Never point integration tests at development, staging, or production databases.
- Integration test database names must contain `test`.
- Do not weaken or remove the safety check in `tests/integration/conftest.py`.
- Unit tests must not require an external database or network service.
- PostgreSQL-specific behavior should be tested with PostgreSQL, not SQLite.

The CI integration database is named `fast_api_template_test`.

## Testing strategy

Use the existing test categories:

- unit tests for services, schemas, security, middleware, dependencies, and isolated repository behavior
- contract tests for HTTP and OpenAPI behavior
- integration tests for PostgreSQL constraints, transactions, locking, migrations, and dialect-specific behavior

Mark PostgreSQL integration tests with:

```python
@pytest.mark.integration
```

When changing database behavior, add relevant PostgreSQL integration coverage.

When fixing a bug, prefer adding a regression test that fails before the fix and passes after it.

## Database migrations

Use Alembic for schema changes.

After modifying SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
uv run alembic upgrade head
uv run alembic check
```

Review generated migrations manually.

Pay special attention to:

- constraints
- indexes
- enum changes
- data migrations
- downgrade behavior

Do not modify deployed schema behavior only through model changes without adding the corresponding migration.

## Errors and API behavior

Expected application failures should use typed exceptions from `app.core.exceptions`.

Map application exceptions centrally through the existing exception handling layer.

Do not leak internal exception messages, secrets, stack traces, SQL errors, or implementation details to clients.

When adding a new public API error, keep the response code stable and cover it with tests.

## Security

Preserve the security expectations documented in `docs/security.md`.

Do not:

- log passwords
- log complete access or refresh tokens
- log authorization headers
- expose secret values in errors
- weaken JWT validation without explicit justification
- bypass authorization dependencies for convenience

Security-sensitive changes should include focused tests.

## Observability

The project already includes request IDs, structured logging, and health/readiness behavior.

Preserve correlation IDs across middleware and deeper application logs.

New observability code should avoid introducing vendor-specific coupling into core application logic unless explicitly required.

Never place secrets or sensitive request bodies into logs, traces, or metric labels.

## Health checks

Keep liveness and readiness semantics distinct.

- Liveness should indicate whether the process is running.
- Readiness may verify dependencies such as PostgreSQL.

Readiness checks should remain bounded by the configured timeout and should not create unmanaged database resources.

## Adding a new domain module

For a new domain such as `projects`, normally follow this order:

1. Add SQLAlchemy models in `app/models/`.
2. Export models from `app/models/__init__.py`.
3. Generate and review an Alembic migration.
4. Add request and response schemas in `app/schemas/`.
5. Add repository operations in `app/repositories/`.
6. Add service use cases in `app/services/`.
7. Add reusable authorization dependencies where appropriate.
8. Add routes under `app/api/routes/`.
9. Register the router in `app/api/router.py`.
10. Add unit, contract, authorization, and integration tests as required.

Keep domain boundaries cohesive. Do not create cross-layer imports that bypass the service layer.

## Local commands

The project uses `uv`.

Install dependencies:

```bash
uv sync --locked
```

Run formatting:

```bash
make format
```

Run lint checks:

```bash
make lint
```

Run type checking:

```bash
make typecheck
```

Run tests:

```bash
make test
```

Run the text policy check:

```bash
make check-text
```

Run the complete local validation:

```bash
make check
```

Before opening or updating a pull request, prefer running `make check`.

## CI expectations

CI currently validates:

- formatting and linting
- no-em-dash text policy
- strict mypy type checks
- non-integration tests with coverage
- PostgreSQL integration tests
- Alembic upgrade, drift check, downgrade, and re-upgrade
- dependency audit

Do not modify code merely to make one CI job pass if the change violates the architecture or test isolation guarantees.

## Coding guidance

Prefer existing patterns over introducing new abstractions.

Keep functions and classes focused.

Use explicit types and preserve strict mypy compatibility.

Prefer dependency injection over hidden globals.

Avoid premature framework additions.

Do not replace async SQLAlchemy patterns with synchronous database access.

Do not add SQLite as a substitute for PostgreSQL integration behavior.

Do not add repository-level transaction commits.

Do not bypass `create_app()` for test setup when isolated settings are needed.

## Before finishing a task

Check the changed code against this list:

- architecture boundaries are preserved
- transaction ownership remains correct
- integration tests cannot touch non-test databases
- configuration is centralized
- migrations accompany schema changes
- security behavior is not weakened
- tests cover changed behavior
- no em dashes were introduced
- `make check` passes where practical
- relevant PostgreSQL integration tests pass for database changes
- documentation is updated when public behavior or configuration changes

If a task conflicts with these instructions, call out the conflict rather than silently weakening repository safeguards.
