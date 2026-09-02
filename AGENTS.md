# AGENTS.md

This file contains instructions for AI coding agents working in this repository.

Do not duplicate repository documentation here. Read and follow the existing source-of-truth documents before making changes.

## Required reading

Before modifying the repository, read:

- `CONTRIBUTING.md` for branching, pull requests, review expectations, naming conventions, local checks, and repository text policy.
- `docs/architecture.md` for application structure, dependency boundaries, transaction ownership, database patterns, migrations, testing strategy, and module organization.
- `docs/security.md` for authentication, authorization, secrets, logging, token handling, and other security requirements.
- `README.md` for setup, development commands, configuration, and general project usage.

If instructions conflict, prefer the more specific repository documentation over assumptions or generic framework conventions.

## Working principles

- Inspect the existing implementation before proposing changes.
- Follow existing patterns unless there is a concrete reason to change them.
- Keep changes focused and avoid unrelated refactors.
- Do not introduce new dependencies or architectural abstractions unnecessarily.
- Preserve strict typing and existing linting conventions.
- Add or update tests when behavior changes.
- Add Alembic migrations when database schema changes.
- Update documentation when configuration or public behavior changes.

## Database safety

Database-related work requires extra care.

- Never run tests against a development, staging, or production database.
- Preserve the dedicated integration-test database safeguards.
- Do not weaken checks around `TEST_DATABASE_URI`.
- Do not introduce repository-level `commit()` or `rollback()` calls unless the documented transaction architecture is intentionally being changed.

Refer to `docs/architecture.md` and the integration-test fixtures for the current database and transaction model.

## Validation

Before considering a code change complete, run the relevant repository checks documented in `CONTRIBUTING.md`.

Prefer the full validation command when practical:

```bash
make check
```

For database changes, also run the relevant PostgreSQL integration and migration checks.

## Scope of AGENTS.md

Keep this file limited to agent-specific operating guidance.

When repository architecture, security policy, contribution rules, setup instructions, or testing conventions change, update their respective source documents rather than copying those details into this file.
