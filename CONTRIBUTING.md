# Contributing

## Workflow

1. Do not push directly to `main`. Create a branch and open a pull request.
2. Every pull request must pass CI before merge.
3. Pull requests should be reviewed before merge.
4. Keep changes focused. Avoid combining unrelated features, fixes, and refactors in the same pull request.

Direct pushes to `main` should be blocked using GitHub branch protection or repository rulesets. A local `pre-push` hook may also be used as an additional safeguard.

## Branch names

Use the following format:

```text
<type>/<short-kebab-description>
```

Use lowercase kebab-case for the description.

Recommended types:

| Type       | Purpose                                               |
| ---------- | ----------------------------------------------------- |
| `feat`     | New functionality                                     |
| `fix`      | Bug fix                                               |
| `refactor` | Internal code restructuring without changing behavior |
| `test`     | Tests or testing infrastructure                       |
| `docs`     | Documentation changes                                 |
| `ci`       | CI/CD and GitHub Actions changes                      |
| `chore`    | Maintenance, tooling, or dependency work              |
| `perf`     | Performance improvements                              |

Examples:

```text
feat/user-registration
fix/refresh-token-rotation
refactor/database-session
test/auth-integration
docs/testing-guide
ci/postgres-integration-tests
chore/update-dependencies
```

Branch names should clearly describe the change and remain reasonably short.

## Pull request titles

Pull request titles must follow Conventional Commit style:

```text
<type>(<scope>): <summary>
```

The scope should identify the main part of the application affected by the change.

Common scopes may include:

```text
api
auth
config
db
users
security
logging
tests
ci
docs
```

Examples:

```text
feat(auth): add refresh token rotation
fix(db): rollback failed transaction correctly
refactor(config): separate application settings
test(auth): add refresh token integration tests
docs(tests): explain test database setup
ci(tests): add PostgreSQL integration test job
```

Use lowercase for the type and scope.

Keep the summary concise and describe what changed.

Because pull requests should be squash-merged, the pull request title should also be suitable as the final commit message on `main`.

## Merge strategy

Use **Squash and merge** for pull requests.

Do not create unnecessary merge commits.

Before merging, confirm that:

* CI passes.
* Required review feedback has been addressed.
* The pull request title follows the repository naming convention.
* The resulting squash commit title is suitable for `main`.

## Style

Do not use em dashes anywhere in the repository.

This applies to:

* Python code
* comments
* docstrings
* Markdown
* documentation
* commit messages
* pull request titles
* pull request descriptions

Use a hyphen, comma, colon, parentheses, or rewrite the sentence instead.

Where practical, this rule should be enforced automatically by linting or CI.

## Code review

Review findings should use priority notation:

| Priority | Meaning                                                                                | Merge policy                                                      |
| -------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `P0`     | Critical security issue, data loss risk, destructive behavior, or catastrophic failure | Must fix immediately. Do not merge.                               |
| `P1`     | Serious correctness, security, or reliability defect                                   | Must fix before merge.                                            |
| `P2`     | Real defect with limited impact, edge case, or important maintainability issue         | Should normally be fixed before merge unless explicitly deferred. |
| `P3`     | Minor improvement, cleanup, readability issue, or non-critical suggestion              | Non-blocking.                                                     |
| `P4`     | Optional polish or stylistic suggestion                                                | Non-blocking.                                                     |

Prefix actionable findings with their priority.

Examples:

```text
P1: Refresh token reuse does not revoke the remaining token family.

P2: This test can connect to a non-test database if the URI safety check is removed.

P3: This helper duplicates validation already performed by the settings model.
```

Each actionable finding should explain:

1. What the problem is.
2. Why it matters.
3. A practical or safe way to fix it.

The overall review priority is the highest unresolved finding.

A pull request with unresolved `P0` or `P1` findings must not be merged.

`P2` findings should normally be resolved before merge unless the reviewer explicitly marks them as safe to defer.

`P3` and `P4` findings are non-blocking unless the reviewer explains otherwise.

## Local checks

Before opening or updating a pull request, run the repository checks:

```bash
make lint
make typecheck
make test
```

For the full local validation:

```bash
make check
```

When changing database behavior, also run the relevant PostgreSQL integration tests using the dedicated test database.

Never point integration tests at a development, staging, or production database.
