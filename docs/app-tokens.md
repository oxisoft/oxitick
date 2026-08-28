# App tokens

An app token lets something that is not a person act on your own tasks: an AI
assistant over [MCP](mcp.md), a script, a home automation.

## Creating one

In the OxiTick app: **Settings → Security → App tokens → New token**.

You give it a name, choose what it may do, optionally set an expiry, and enter
your account password.

The password is asked for even though you are already signed in. A session lasts
hours and expires by itself; an app token is indefinite and does not. Without
that step, a device left unlocked on a desk turns into a credential that outlives
every other protection on the account — including changing the password.

**The token is shown once.** Copy it then. It is stored as a hash, so it cannot
be shown again, and the only recovery is to revoke it and make another.

## Scopes

Cumulative — each includes the ones above it.

| Scope | What it can do |
|---|---|
| `read` | See your lists and tasks, search them |
| `write` | Also add, edit and complete tasks and subtasks |
| `delete` | Also delete tasks and subtasks |

`delete` is separate from `write` on purpose. Most people want an assistant that
can tick things off without one that can throw them away.

**No scope lets a token touch a list.** Creating, renaming, archiving and
deleting lists are not in the API at all — see [the README](../README.md#things-worth-knowing-before-you-write-a-client).

## What a token can never do

It is accepted **only** on `/api/v1/personal/*`. Every other route refuses it,
including with a perfectly valid credential. So a leaked token cannot:

- change your password or disable two-factor
- register, revoke or wipe a device
- read or write shared lists, or see who is in them
- reach the sync endpoints or the admin console
- create another token, or extend its own life

A test walks the server's whole route tree on every build and fails if any route
outside the personal API accepts one.

## Revoking

Settings → Security → App tokens → the ⃠ button.

Revocation takes effect on the token's **next request** — the server checks on
every call, with no cache in between. It needs no password: switching a
credential off is the safe direction and should be the easy one.

Revoked tokens stay in the list, struck through. "This existed and is now off" is
different information from "this never existed", and you are the person who needs
to tell them apart.

## Keeping an eye on one

Each token shows its prefix (`oxt_7Kd2Qa…`), its scope, and when it was last
used. **"Never used"** on a token you set up hours ago almost always means the
configuration has the wrong URL or a truncated token.

The last-used address is taken from the connection. It is only read from
`X-Forwarded-For` when the server is started with `TRUSTED_PROXY=1`, because
otherwise that header is written by the client and a spoofable address displayed
as evidence is worse than none.

## Hiding a list from tokens

Any list can be closed to the API: open the list editor and turn on **"Hide from
apps and AI assistants"**.

A closed list and everything in it answers `404` on every endpoint and appears in
no listing or search — indistinguishable from not existing, which is the point. A
task id captured before you closed the list stops working the moment you do,
because access is re-resolved on every request.

It stays fully available on all your own devices. This closes it to the API, not
to you.

## If your server administrator has switched it off

An administrator can disable app tokens for a whole installation from the admin
console (System → App Tokens). While it is off, every token is refused with
`503 app_api_disabled` and the app shows a banner saying so.

Nothing is revoked. Names, scopes and history are kept, and everything resumes
when it is switched back on.

## Rate limits

Roughly 600 reads and 60 writes per minute per token, with a small burst.

Over the limit you get `429` with a `Retry-After` in seconds. Honour it — a
client that retries immediately makes the problem worse, and the cost lands on
the person's other devices, which queue behind the same database writer.

Limits are held in the server process, so they reset on restart and are not
shared between replicas.

## Security notes for anyone building on this

- Send the token in the `Authorization` header and nowhere else. In a query
  string it lands in this server's access log and in every proxy in front of it —
  a leak that leaves no trace of having happened.
- Store it the way you would store a password. It is a bearer credential: whoever
  holds it is the account, within its scope.
- Use the narrowest scope that works. A summarising assistant needs `read`.
- Expect `404` for anything you may not have. The API never distinguishes "does
  not exist" from "not yours" from "hidden", because distinguishing them confirms
  the thing exists.
