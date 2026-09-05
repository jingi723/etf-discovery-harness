# Security

## Reporting a vulnerability

Open a [private security advisory](https://github.com/jingi723/etf-discovery-harness/security/advisories/new)
rather than a public issue. Please do not include live credentials in the report.

## Credentials

This project reads three optional secrets from the environment:

| Variable | Provider |
|---|---|
| `FMP_API_KEY` | Financial Modeling Prep |
| `TOSS_CLIENT_ID` | Toss Securities Open API |
| `TOSS_CLIENT_SECRET` | Toss Securities Open API |

They are read from `.env` or the process environment and are used nowhere else. Ignored
by git:

- `.env`, `.env.*` (except `.env.example`), `*.key`, `*.pem`
- `private/` — local notes, positions, cached tokens
- `output/`, `_workspace*/` — run artefacts, which contain point-in-time market data

Only `.env.example`, which holds placeholders, is tracked.

`tools/data.py` never logs a key or echoes a full request URL. Agents are instructed
never to write key values into reports, logs, or source. If you add a provider, keep
both properties.

**If you have committed a key:** revoke it at the provider first, then rewrite history.
Rotating the key is the step that actually matters — a key pushed to GitHub should be
treated as public, since history rewriting does not reach forks, clones, or caches.

## Toss token handling

Toss issues **one valid access token per client**. Requesting a new one immediately
invalidates the previous one, so parallel processes each fetching their own will
invalidate each other mid-run. `tools/data.py` caches the token to disk
(`TOSS_TOKEN_CACHE`, default `/tmp/.toss_token.json`) and re-issues only on expiry. On
a shared machine, point that path somewhere only you can read.

**The order and account endpoints are never called.** This harness is read-only against
market data and holds no trading authority. Keep it that way — a PR that adds order
placement will be declined.

## Scope

This is research tooling. It fetches public market data over HTTPS and writes files
locally. It does not execute trades, hold funds, accept network input, or run a server.
The realistic risk surface is credential leakage through committed files or pasted
output, which is what the rules above are aimed at.
