# Authentication

Two credentials, reaching different things.

## Sessions

What the OxiTick apps use.

```
POST /api/v1/auth/login
{ "identifier": "you", "password": "…", "device_id": "…", "device_name": "…" }
```

Returns an access token (a JWT, hours) and a refresh token (a month). Send the
access token as `Authorization: Bearer <jwt>` and exchange the refresh token at
`/api/v1/auth/refresh` when it expires.

A signed token is not by itself permission to act. Every authenticated request
also checks:

- **the account** — a banned account is refused immediately rather than when its
  token happens to expire (`403 account_banned`);
- **the session** — a device disconnected from another one is refused
  (`401 device_revoked`), as is a session that predates a security change on the
  account such as enabling two-factor (`401 session_superseded`).

Both are `code` values in the error body. Branch on the code, not the message.

## App tokens

What an AI assistant or a script uses. Created in the app, not over the API — see
[app tokens](app-tokens.md).

```
Authorization: Bearer oxt_EXAMPLE000000000000000000000000000000000
```

Accepted **only** on `/api/v1/personal/*`. Deliberately weaker than a session in
every direction: narrower reach, an explicit scope, no refresh, and revocation
that takes effect on the next request.

## Error codes

| Code | Status | Meaning |
|---|---|---|
| `token_invalid` | 401 | Missing, malformed, expired or revoked credential. Sign in again, or make a new token. |
| `account_banned` | 403 | The account is suspended. Retrying will not help. |
| `account_not_found` | 403 | The credential names an account that no longer exists. |
| `device_revoked` | 401 | This device was disconnected from another one. Signing in again re-attaches it. |
| `session_superseded` | 401 | The session predates a security change on the account. |
| `scope_insufficient` | 403 | The app token is valid but was created without enough scope. Make a new token. |
| `rate_limited` | 429 | This token has spent its budget. See `Retry-After`. |
| `app_api_disabled` | 503 | An administrator has switched app tokens off for the whole server. Nothing is wrong with the token. |

## Two-factor

When an account has TOTP enabled, login requires a code, and so do the actions
that would otherwise let someone bypass it — changing the password, disabling
two-factor, and creating an app token.

Enabling two-factor signs out every other session on the account, so a session
opened before it cannot outlive it.

## CORS

The server sends `Access-Control-Allow-Origin: *` and allows `GET`, `POST`,
`PUT`, `PATCH`, `DELETE` and `OPTIONS`. There are no cookies anywhere in the API
— every credential is a bearer token in a header — so there is no CSRF surface
and no `Allow-Credentials`.
