# Security model

## Passwords

New passwords are hashed with Argon2id through `pwdlib`. Existing bcrypt hashes remain
verifiable and are upgraded to the recommended Argon2id representation after a successful
login. Plaintext passwords must only exist in validated request data and must never be sent
to repositories, persisted, or logged.

Password changes require the current password and revoke all refresh sessions for the user.
Password policy, breached-password screening, recovery, and multi-factor authentication are
application-specific features and are not implemented by this template.

## Access tokens

Access tokens are short-lived signed JWTs. Decoding validates:

- `sub`: stable user identifier.
- `iss`: expected token issuer.
- `aud`: this API as the intended audience.
- `iat`: token issuance time.
- `exp`: token expiration time.
- `jti`: unique token identifier.
- `token_type`: explicitly `access`.

Protected requests load the current user from PostgreSQL. Deleted and inactive accounts are
therefore rejected even when a token signature remains valid, and authorization uses the
current database role rather than a stale role claim.

Access tokens are not stored in the database. Logout and password changes do not revoke an
already issued access token immediately; it expires according to
`ACCESS_TOKEN_EXPIRE_MINUTES`. Keep this lifetime short. Applications requiring immediate
access-token revocation need an additional revocation/version check.

## Refresh tokens

Refresh JWTs have `token_type=refresh`, their own lifetime, and cannot authenticate protected
API routes. PostgreSQL stores only a SHA-256 digest of each refresh `jti`, never the raw
token.

Every refresh operation:

1. Validates the JWT and its required claims.
2. Locks the matching refresh session.
3. Revokes the used session.
4. Issues a new access/refresh pair in the same token family.

Reusing a revoked refresh token revokes its entire family. Logout revokes one refresh
session; logout-all and password changes revoke all refresh sessions for the account.

Clients must protect refresh tokens as credentials. A production browser application should
consider Secure, HttpOnly, SameSite cookies plus an appropriate CSRF defense instead of
JavaScript-accessible storage. The template accepts the token in a JSON request body so it
does not leak through query strings.

## Authorization

Reusable FastAPI dependencies enforce administrator and super-administrator roles. Public
schemas are separate from administrative update schemas, preventing ordinary input from
changing passwords, roles, or account state unexpectedly.

Role checks are only a starting point. New resource endpoints must define ownership and
tenant boundaries explicitly and test both allowed and denied cases. Never rely on a client
to hide an operation it is not authorized to call.

## Secrets and deployment

- Generate `SECRET_KEY` with a cryptographically secure random generator and inject it from a
  secret manager.
- Do not commit `.env`, tokens, database credentials, or production configuration.
- Terminate TLS at a trusted proxy/load balancer and configure forwarded headers only for
  trusted proxies.
- Restrict database credentials and network access by environment.
- Restrict CORS origins; CORS is not an authentication or CSRF control.
- Run dependency auditing and apply security updates through reviewed lockfile changes.
- Provision the initial super-admin through an audited operational process; public
  registration always creates a regular user.

## Error and log exposure

Expected failures return stable application error codes. Unexpected failures return a
generic message while the traceback is recorded server-side with a request ID. Do not add
raw exception messages or sensitive payloads to API responses.

Structured logging intentionally uses a small allowlist of request fields. Review any new
logging fields for secrets and personal data before adding them.
