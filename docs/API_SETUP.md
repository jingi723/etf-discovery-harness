# API Setup

The agent research workflow can run without vendor API keys when web research tools
are available. It uses official issuer, exchange and filing sources and records
coverage gaps. **The live `score.py` and `validate.py` CLIs require FMP access**;
they call FMP directly and do not fall back to web research or Toss. Viewing the
bundled sample and running `validate.py --self-check` require no credentials.

Adding a key changes two things that matter: numbers arrive as JSON instead of being
parsed out of rendered HTML, and every response carries an explicit as-of date, which
is what the sourcing rules require. It also cuts context usage substantially — one
`ratios-ttm` call replaces several search results and a long page read.

Two providers are supported, and they do not overlap:

| Data | Provider |
|---|---|
| Quotes, candles, order book | Toss (if configured), otherwise FMP |
| Korean investor-type flows, short selling, credit, securities lending | Toss only |
| KOSPI/KOSDAQ indices, Korean treasury yields, KRW FX | Toss only |
| Financial statements, TTM ratios, valuation multiples | FMP only |
| US ETF holdings, ETF AUM and expense ratio, company profile | FMP only |

## Configuration

```bash
cp .env.example .env
```

Fill in whichever keys you have and leave the rest as the placeholder — the tools skip
any provider whose key is still the placeholder value.

```ini
FMP_API_KEY=...
TOSS_CLIENT_ID=...
TOSS_CLIENT_SECRET=...
```

`tools/data.py` loads `.env` itself via `load_env()`, using `os.environ.setdefault`, so
a variable already exported in your shell always wins. For Claude Code sessions, export
it before launching:

```bash
set -a; source .env; set +a
claude
```

`.env` is gitignored. Keys must never appear in output files, logs, commit messages, or
source. See [SECURITY.md](../SECURITY.md).

## Financial Modeling Prep

Sign up at [financialmodelingprep.com](https://financialmodelingprep.com/). The free
tier covers the endpoints below at a lower rate limit.

**Use the `stable` path.** The legacy `/api/v3/` routes are blocked on current keys.

```
https://financialmodelingprep.com/stable/{endpoint}?symbol={sym}&apikey={key}
```

| Endpoint | Returns |
|---|---|
| `profile` | Market cap, beta, sector, description |
| `income-statement`, `balance-sheet-statement`, `cash-flow-statement` | Statements; add `period=quarter` |
| `ratios-ttm` | TTM margins, ROE, leverage, P/E |
| `key-metrics-ttm` | EV/EBITDA, FCF yield |
| `etf/holdings` | ETF constituents and weights |
| `etf/info` | AUM, expense ratio, inception |
| `quote`, `historical-price-eod/full` | Price and volume |
| `treasury-rates` | US treasury curve |

### Korean ticker coverage (verified 2026-09-04)

| Target | `quote` | `historical-price-eod/full` | `ratios-ttm` | `etf/holdings` |
|---|:--:|:--:|:--:|:--:|
| Korean stock (`005930.KS`) | ✅ | ✅ | ✅ | — |
| Korean ETF (`091230.KS`) | ✅ | ✅ | — | ❌ empty |

**Korean ETF holdings are supported by neither provider.** Pull them from the issuer's
official page. Most render the constituent table with JavaScript — Mirae Asset TIGER,
for example, only loads it after the "구성종목 보기" button is clicked, so browser
automation is required.

An empty array from FMP means "not covered", not "no holdings". Retry once with an
alternative symbol format, then record it as missing.

## Toss Securities Open API

Register at [developers.tossinvest.com](https://developers.tossinvest.com). Data is
relayed from the KRX/NXT integrated exchange feed.

```
POST https://openapi.tossinvest.com/oauth2/token
     grant_type=client_credentials&client_id=...&client_secret=...
Base https://openapi.tossinvest.com/api/v1
     Authorization: Bearer {access_token}
```

| Endpoint | Returns | Coverage |
|---|---|---|
| `prices?symbols=A,B` | Current price, up to 200 symbols per call | KR + US |
| `candles?symbol=X&interval=1d\|1m&count=N&adjusted=true` | OHLCV, max 200 bars, paginate with `before` (note: `symbol` is singular here) | KR + US |
| `orderbook`, `trades`, `price-limits` | Depth, tick data, limit-up/down | KR + US |
| `stocks?symbols=`, `stocks/all` | Listing date, shares outstanding, leverage factor, halt status | KR + US |
| `stocks/{symbol}/investor-trading` | Net buying by retail / foreign / institution (7 sub-types), foreign ownership | **KR only** |
| `stocks/{symbol}/short-selling`, `credit-trades`, `securities-lending`, `program-trades` | Short interest, margin, lending, program flow | **KR only** |
| `market-indicators/*` | KOSPI/KOSDAQ, KR treasury 2Y–30Y, index-level investor flow | KR |
| `exchange-rate?baseCurrency=USD&quoteCurrency=KRW` | FX, 1-minute refresh | KRW/USD |
| `rankings?type=TOP_GAINERS&...` | Top-100 movers by change, value, volume | KR + US |

Full spec: `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`

### Three things that will bite you

**Symbols differ from FMP.** Toss uses bare codes — `005930`, `AAPL`, `SOXL`. No `.KS`
suffix.

**One token is valid per client.** Issuing a new token immediately invalidates the
previous one. Parallel agents each requesting their own token will invalidate each
other mid-run. `tools/data.py` caches the token on disk and only re-issues on expiry;
any other client must do the same. Override the cache path with `TOSS_TOKEN_CACHE`.

**A 403 is about your IP, not your key.** `access_denied` / `"IP address not allowed"`
means the calling IP is not on the developer-console allowlist. This recurs whenever
you change networks — tethering, a different office.

```bash
curl -s https://api.ipify.org     # then check it against the console allowlist
```

`tools/data.py` detects this case and says so explicitly rather than reporting a
generic auth failure.

Responses may be gzipped; with `curl` you need `--compressed`. Rate limit is 15 req/s
per endpoint group, reported in the `x-ratelimit-*` headers. Batch quotes with the
comma-separated `symbols` parameter rather than looping.

Same-day flow figures are provisional while the market is open — retail and
institutional sub-breakdowns can be `null` until the evening settlement.

Toss also exposes order and account APIs. **This harness never calls them.**

## How sources are ranked

Both APIs are recorded as `secondary` (vendor) tier. When an official issuer,
exchange or regulatory filing (`primary`) is available for the same figure, it wins.
Conflicting numbers are both kept in `source_conflicts` along with the reason one was
used — they are never silently dropped.

Full policy:
[`.claude/skills/etf-evidence-standards/references/source-priority.md`](../.claude/skills/etf-evidence-standards/references/source-priority.md)
