# OxiTick Server — API & self-hosting

Self-hosted sync server for **[OxiTick](https://oxitick.com)**, a private,
offline-first app for personal and collaborative to-do lists and notes. The app
works fully offline; point it at this server to sync across devices and share
lists with the people you choose. Your data stays on infrastructure you control:
no third-party cloud, no tracking, no ads.

This repository is the **public documentation** for that server: the HTTP API,
and how to run it. The server itself is distributed as a container image.

- **API reference (Swagger):** <https://oxisoft.github.io/oxitick/> — GitHub Pages, served from the repository root
- **Image:** <https://hub.docker.com/r/oxisoft/oxitick>
- **Website:** <https://oxitick.com>
- **MCP server for AI assistants:** <https://github.com/oxisoft/oxitick-mcp>

> ⚠️ **Never store passwords in OxiTick.** A to-do and notes manager is private,
> but it is not a vault. Passwords, recovery codes and other secrets belong in
> something built for them, with encryption at rest and a secret-specific
> security model. For a personal, cloud-free password manager we recommend
> **[IntelliWallet](https://intelliwallet.io)**.

---

## Install

`linux/amd64` and `linux/arm64` — Raspberry Pi 4/5, Apple Silicon hosts, ARM
VPS.

```
docker run -d --name oxitick -p 15773:15773 -v ./data:/app/data oxisoft/oxitick:latest
```

No configuration required: auth secrets are generated on first start and kept in
the data volume. With compose:

```yaml
# docker-compose.yml
services:
  oxitick:
    image: oxisoft/oxitick:latest
    ports:
      - "15773:15773"
    volumes:
      - ./data:/app/data
    environment:
      # Recommended: create the admin account before the first request is served
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=change-me-min-8-chars
    restart: unless-stopped
```

> **Bind-mounting a host directory?** The server runs as UID 1000, and Docker
> creates a missing bind-mount source owned by root — after which the container
> fails to start with `permission denied` on `/app/data/jwt_secret`. Create it
> first:
>
> ```
> mkdir -p data && sudo chown -R 1000:1000 data
> ```
>
> A named volume avoids this entirely.

Then open `http://your-host:15773/admin`, sign in, and create user accounts under
**Users**. In the app: Settings → Accounts → add the server URL and those
credentials. Account creation is admin-only; there is no public registration
endpoint.

Full deployment guidance — TLS, reverse proxies, backups, upgrades — is in the
[Docker Hub description](https://hub.docker.com/r/oxisoft/oxitick).

### A note on backups

The database runs in SQLite's WAL mode, so on disk it is **three** files:
`oxitick.db`, `oxitick.db-wal` and `oxitick.db-shm`. Recent writes live in the
`-wal` file until they are checkpointed.

Back up the whole `data` directory, or take a consistent single-file copy:

```
sqlite3 /path/to/data/oxitick.db ".backup '/tmp/oxitick-backup.db'"
```

Copying `oxitick.db` on its own gives you a database that restores cleanly and
silently omits whatever had not been checkpointed yet.

---

## The API

Every endpoint is described in [`openapi.yaml`](openapi.yaml), rendered at
<https://oxisoft.github.io/oxitick/>.

There are two ways to authenticate, and they reach different things.

| | Session (`Bearer <jwt>`) | App token (`Bearer oxt_…`) |
|---|---|---|
| Obtained by | `POST /api/v1/auth/login` | Created in the app, Settings → Security |
| Lifetime | Hours, refreshable | Until revoked |
| Reaches | Everything | `/api/v1/personal/*` **only** |
| Intended for | The OxiTick apps | AI assistants, scripts |

An app token is deliberately the weaker credential. It cannot change a password,
disable two-factor, register or wipe a device, read or write shared lists, reach
the admin console, or create another token. It can be revoked from the app and
stops working on its next request.

- [Authentication in detail](docs/authentication.md)
- [App tokens](docs/app-tokens.md)
- [Using OxiTick from an AI assistant](docs/mcp.md) — Claude Desktop, Claude Code, Gemini CLI

### Quick example

```bash
SERVER=https://your-oxitick-server
TOKEN=oxt_your_token_here

# What is overdue?
curl -s -H "Authorization: Bearer $TOKEN" \
  "$SERVER/api/v1/personal/items?overdue=true&limit=10"

# Tick one off
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}' \
  "$SERVER/api/v1/personal/items/$ITEM_ID/completion"
```

More in [`examples/`](examples/).

### Things worth knowing before you write a client

**Lists are read-only over the API.** There is no endpoint that creates,
renames, archives or deletes one — not behind a scope, not behind a
confirmation. Deleting a list takes every task in it, and the shape of someone's
lists is a decision about how they organise their life. Everything writable is a
task or a subtask.

**Every write names one id.** The single exception is
`POST /api/v1/personal/items/completion`, which takes explicit ids and caps them
at 25. There is no filter-shaped mutation anywhere, because that is how one
wrong inference becomes a hundred wrong rows.

**Deletion is soft.** A deleted task is marked, not removed — that is how a
deletion reaches other devices, and it leaves the task recoverable in the app.

**Last write wins, and the API is not privileged.** A device that has been
offline with a newer edit will overwrite an API write when it next syncs. That
is correct behaviour for an offline-first system; do not build on the assumption
that a `200` is final.

**The server only knows what has been uploaded.** An account that has never
synced has nothing here. This is not a bug.

**Some lists are invisible on purpose.** A list can be closed to the API from
the app's list editor — "Hide from apps and AI assistants". A closed list and its
tasks answer `404` everywhere and never appear in any listing or search, which is
indistinguishable from not existing. That is the point.

**Rate limits are per token.** Roughly 600 reads and 60 writes a minute, with a
small burst. Over the limit you get `429` and a `Retry-After` you should honour.

---

## Reporting problems

Issues and questions about the API or these docs: use this repository's issue
tracker. Please do not include tokens, real task content, or your server's
hostname in a public issue.

## License

MIT. See [LICENSE](LICENSE).
