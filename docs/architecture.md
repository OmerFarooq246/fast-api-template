# Architecture

## Application construction

`app.main.create_app()` is the composition root. It creates environment-specific database
resources, configures logging and middleware, registers exception handlers and routers,
and attaches resources to `app.state`. `app.main.app` preserves the standard Uvicorn import
path while tests can construct isolated application instances with explicit settings.

FastAPI lifespan owns process-level resources. When the application stops, the async
database engine is disposed cleanly.

## Dependency direction

```text
HTTP route -> service/use case -> repository -> SQLAlchemy -> PostgreSQL
     |               |
     |               +-> application/domain exceptions
     +-> schemas, dependencies, and HTTP responses
```

- **Routes** parse HTTP input, enforce endpoint dependencies, call a service, and shape the
  HTTP response. They do not contain persistence queries.
- **Services** implement use cases and coordinate repositories. They raise typed application
  errors instead of HTTP exceptions.
- **Repositories** contain persistence operations. They add, query, delete, and `flush()`
  entities but never commit or roll back.
- **Models** describe persistence state with SQLAlchemy 2 typed mappings.
- **Schemas** define public request and response contracts with Pydantic.

Dependencies must point inward. A repository must not import a route or service, and a
service must not depend on FastAPI request/response types.

## Transactions

The `get_db` dependency opens one transaction for the request. A successful request commits
after the route finishes; an exception rolls the transaction back. Repository `flush()`
calls send SQL to PostgreSQL, populate generated fields, and surface constraints while the
work is still reversible.

This permits one use case to make several repository changes atomically:

```python
async def perform_use_case(session: AsyncSession) -> Result:
    first = await first_repository.create(session, ...)
    await second_repository.update(session, ...)
    return Result(first.id)
```

Neither repository commits. For consumers outside HTTP (workers, CLI commands, and scheduled
jobs), the caller must establish an equivalent `async with session.begin()` boundary. Avoid
nested, competing transaction owners. If a future use case needs multiple independently
committed phases, give that use case an explicit unit-of-work boundary rather than adding
commits to generic repository methods.

## Errors

Expected application failures use the types in `app.core.exceptions`. The centralized
handler maps these to stable client-facing error codes and HTTP statuses. The catch-all
handler logs the traceback with request context and returns a sanitized `500` response.
Internal exception text must never be returned to clients.

Add a new application exception only when callers can make a meaningful distinction. Map it
centrally, and test both its status and stable response code.

## Configuration

`app.core.config.Settings` is the single source of runtime configuration. It validates the
database driver and deployment secrets before the application starts. Pass settings through
dependencies or constructors; avoid reading environment variables throughout application
code.

New settings should:

1. Have a precise type and safe local default when one exists.
2. Use Pydantic constraints for bounds and formats.
3. Be added to `env.example` and the configuration documentation.
4. Fail startup when an unsafe value would otherwise reach production.

## Database migrations

SQLAlchemy metadata describes the desired schema; Alembic migrations describe how deployed
schemas reach it. Import every model from `app/models/__init__.py` so Alembic autogeneration
can discover it.

After changing a model:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
uv run alembic upgrade head
uv run alembic check
```

Review generated migrations manually, especially enum, constraint, index, data migration,
and downgrade behavior. CI verifies an empty-database upgrade, downgrade to base, re-upgrade,
and model/schema drift against PostgreSQL.

## Testing strategy

- **Unit tests** isolate services, security helpers, schemas, dependencies, middleware, and
  repository behavior. They must not require network services.
- **Contract tests** inspect HTTP behavior and OpenAPI security/response declarations.
- **Integration tests** use PostgreSQL for constraints, transactions, locking, migrations,
  and dialect-specific behavior. SQLite is not a substitute for these checks.

Tests should live beside their risk: add unit and integration coverage in the same commit as
the behavior. Mark PostgreSQL tests with `@pytest.mark.integration`.

## Adding a domain module

For a new domain such as `projects`:

1. Add typed SQLAlchemy models under `app/models/` and export them from
   `app/models/__init__.py`.
2. Generate and review an Alembic migration.
3. Add narrowly scoped request/response schemas under `app/schemas/`.
4. Add repository queries under `app/repositories/` without transaction commits.
5. Add use cases under `app/services/`, raising typed application errors.
6. Add authorization dependencies when access rules are reused across endpoints.
7. Add a router under `app/api/routes/` and register it in `app/api/router.py`.
8. Add unit, HTTP contract, authorization, and PostgreSQL integration tests as appropriate.
9. Run `make check` and the relevant integration tests before opening a pull request.

Keep modules cohesive. Split a domain into subpackages when its files become difficult to
navigate; do not introduce cross-domain imports to bypass a service boundary.

## Observability extension points

The logging setup emits structured JSON without requiring a vendor SDK. Request context is
stored in a context variable so logs created deeper in the call stack receive the same
request ID. Add metrics and tracing as middleware or lifespan-managed providers, preserving
the same correlation identifier where supported.

Do not put secrets, passwords, complete tokens, authorization headers, or sensitive request
bodies in logs, metrics labels, or traces.
