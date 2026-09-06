# Source Priority Policy

Division of labour between the two registered APIs: **quotes, volume, candles, investor-type flows, Korean indices and bond yields, and FX go to the Toss Securities Open API first**; **financial statements, valuation multiples, US ETF holdings, and company profiles go to FMP first**. Both rank above web search.

## Registered API ①: Toss Securities Open API — first for prices and flows

For quotes, volume, candles, investor-type trading, short-selling / margin / lending / program flow, Korean indices, Korean treasury yields, and FX, **call Toss before web search or FMP** (KRX/NXT integrated exchange feed, covering KR and US names).

- **Auth**: `TOSS_CLIENT_ID` and `TOSS_CLIENT_SECRET` in the environment (`.env`). `POST https://openapi.tossinvest.com/oauth2/token` with `grant_type=client_credentials&client_id=...&client_secret=...` (form-urlencoded), then `Authorization: Bearer {access_token}` on every call. Never write key values into output, logs, or source.
- **One token is valid per client.** Re-issuing immediately invalidates the previous token, so parallel agents each fetching their own will invalidate each other. **Cache the token to a file and share it, re-issuing only on expiry** — the same pattern as the parallel-scorer temp-file race.
- **Rate limit**: 15 req/s per endpoint group (`x-ratelimit-*` headers). Batch quotes with the comma-separated `symbols` parameter, up to 200 at a time, instead of looping.
- Responses may be gzipped — `curl` needs `--compressed`.
- **Verified endpoints** (checked 2026-08-26, base `https://openapi.tossinvest.com/api/v1`, spec at `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`):

| Endpoint | Use | Coverage |
|---|---|---|
| `prices?symbols=A,B` | Current price, up to 200 per call | KR + US |
| `candles?symbol=X&interval=1d\|1m&count=N&adjusted=true` | OHLCV, max 200 bars, paginate with `before` (note: `symbol` is singular here) | KR + US |
| `orderbook` / `trades` / `price-limits` | Depth, same-day ticks, limit up/down | KR + US |
| `stocks?symbols=` / `stocks/all` | Listing facts (market, listing date, shares outstanding, leverage factor, halt status) | KR + US |
| `stocks/{symbol}/investor-trading` | **Investor-type flow** — net buying by retail / foreign / institution (7 sub-types) / other corporates, foreign ownership | **KR only** |
| `stocks/{symbol}/short-selling`, `credit-trades`, `securities-lending`, `program-trades` | Short interest, margin, lending, program flow | **KR only** |
| `market-indicators/prices`, `market-indicators/{symbol}/candles`, `.../investor-trading` | KOSPI/KOSDAQ, Korean treasury 2Y–30Y (8-series catalogue), index-level investor flow | KR |
| `exchange-rate?baseCurrency=USD&quoteCurrency=KRW` | FX, 1-minute refresh (reference only) | KRW/USD |
| `rankings?type=TOP_GAINERS...&marketCountry=&duration=` | Top-100 by change, turnover, volume | KR + US |

- Symbol format: KR `005930`, US `AAPL` / `SOXL` — different from FMP's `.KS` suffix convention.
- Flow endpoints (investor-trading and friends) are KR-only; US symbols return 400 `unsupported-market`. Same-day figures are provisional while the market is open, so retail and institutional sub-breakdowns can be `null` until the evening settlement.
- **Not provided**: financial statements, valuation multiples, ETF holdings, company profiles → use FMP (below). Order and account APIs also exist, but **ETF Research Agent never calls them.**
- Record as: `source_name` "Toss Securities Open API", `source_type` "broker", `reliability_tier` "secondary" (exchange-data relay), `as_of_date` from the response's timestamp/date field.

## Registered API ②: FMP (Financial Modeling Prep)

For financial statements, valuation, US ETF holdings, and company profiles, **call FMP before web search** (secondary/vendor tier; structured data means fewer parsing errors and an explicit as-of date). Plain quotes and volume go to Toss first.

- **API key**: passed via `FMP_API_KEY`. Copy `.env.example` to `.env` to keep it locally, but never write the key value into output, logs, or source. With no key set, skip FMP and fall back to the official web sources ranked below.
- **Endpoint**: `https://financialmodelingprep.com/stable/{endpoint}?symbol={sym}&apikey=$FMP_API_KEY` — the `stable` path is required; legacy `/api/v3/` is blocked on current keys.
- **Verified endpoints** (checked 2026-07-05):

| Endpoint | Use | Axis |
|---|---|---|
| `profile?symbol=X` | Market cap, beta, sector, description | Common |
| `income-statement?symbol=X&limit=N` | Income statement (annual, or `period=quarter`) | Financials (09) |
| `balance-sheet-statement`, `cash-flow-statement` | Balance sheet, cash flow (FCF, debt) | Financials (09) |
| `ratios-ttm?symbol=X` | TTM margins, ROE, leverage, multiples | Financials (09), Valuation (10) |
| `key-metrics-ttm?symbol=X` | P/E, EV/EBITDA, FCF yield | Valuation (10) |
| `etf/holdings?symbol=X` | **ETF constituents and weights** (US-listed) | Value-chain mapping (07) |
| `etf/info?symbol=X` | AUM, expense ratio, inception | Candidates (06), structure gate |
| `quote?symbol=X` | Price, volume | Common |

- **Coverage**: broad for US stocks and US-listed ETFs. **Korean single stocks are supported in `005930.KS` form** for profile and financials. Holdings for Korea-listed ETFs (`463250.KS` and similar) are **not supported (empty response)** — keep using issuer pages and search for those.
- An empty array means "not covered". Retry once with an alternative symbol format, then record it as missing.
- Record as: `source_name` "FMP (Financial Modeling Prep)", `source_type` "vendor", `reliability_tier` "secondary", `as_of_date` from the response's date field.

Below, per data domain: rank 1 = primary, 2 = secondary, 3 = tertiary. When the same figure exists in several places, always take the higher-ranked source and use the lower one only to cross-check.

## ETF basics (name, index, fees, AUM, replication method)

| Rank | Source |
|---|---|
| 1 (primary) | Exchange official data (KRX and equivalents), issuer ETF pages, issuer fact sheets, prospectus |
| 2 (secondary) | ETF.com, Morningstar, issuer data feeds, reputable vendors |
| 3 (tertiary) | General finance portals, news |
| Never | Blogs, forums |

## ETF holdings

| Rank | Source |
|---|---|
| 1 (primary) | Issuer daily holdings, official PCF, issuer fact sheet, exchange disclosure |
| 2 (secondary) | Data vendors, Morningstar, ETF.com |
| 3 (tertiary) | General finance portals |
| Never | Unattributed data |

Issuer daily holdings always win, because composition can change daily.

## Constituent financials

| Rank | Source |
|---|---|
| 1 (primary) | Company filings (DART, SEC EDGAR), exchange and regulator disclosures, financial data vendors |
| 2 (secondary) | Reputable financial APIs, issuer and broker research |
| 3 (tertiary) | General web results — supporting evidence only |

## Prices, volume, investor-type flows, indices, FX

| Rank | Source |
|---|---|
| 1 (primary) | Toss Securities Open API, exchange official data (KRX) |
| 2 (secondary) | FMP `quote`, reputable finance portals |
| 3 (tertiary) | News — for event evidence only |

## Valuation data

| Rank | Source |
|---|---|
| 1 (primary) | Data vendors, exchanges, official financials, company filings |
| 2 (secondary) | Reputable portals, Morningstar, material citing Bloomberg/Refinitiv/FactSet |
| 3 (tertiary) | News — for event evidence only |

## Theme data (demand, bottlenecks, capex, policy)

| Rank | Source |
|---|---|
| 1 (primary) | Government and institutional publications, industry reports, company filings, IR materials, reputable research |
| 2 (secondary) | Issuer research, trade-association data, market data vendors |
| 3 (tertiary) | News — for event evidence only |

**Never build a theme-structure grade from news alone.** News establishes that an event happened; a structural judgment needs at least one primary or secondary source.

## Handling source conflicts

When sources disagree on a figure or a fact:

1. Primary wins.
2. Within the same tier, the more recent `as_of_date` wins.
3. For ETF holdings, issuer daily holdings always win.
4. When figures differ, do not delete either — record both in the envelope's `source_conflicts`, with both values, both sources, and the reason one was adopted.
5. If the conflict affects a headline grade, lower that item's confidence.
6. Do not hide the conflict in the prose — write it out: "sources differ on this figure; stated on the basis of {adopted source}".

## Field notes (added 2026-09-04)

### Toss Open API — IP allowlist
A token request failing with 403 `access_denied` / `"IP address not allowed"` is **an IP problem, not a key problem**. Toss only accepts calls from IPs registered in the developer console. It recurs whenever the network changes (tethering, a different office).
- Diagnose: `curl -s https://api.ipify.org`, then check that address against the console allowlist
- Fix: pre-register the IPs of networks you use often. Until then, fall back to FMP

### FMP — Korean ticker coverage (verified 2026-09-04)
| Target | `quote` | `historical-price-eod/full` | `ratios-ttm` | `etf/holdings` |
|---|---|---|---|---|
| Korean stock (`005930.KS`) | ✅ | ✅ | ✅ | — |
| Korean ETF (`091230.KS`) | ✅ | ✅ | — | ❌ **empty** |

→ **Korean ETF holdings are supported by neither provider.** Get them from the issuer's official page (browser automation usually required — most render the table in JavaScript). Mirae Asset TIGER, for example, only loads the constituent table after the "구성종목 보기" button is clicked.

### Using a figure from the news (five mandatory checks)
1. **Article date ≠ announcement date ≠ as-of date** — always record the **as-of** date in the output
2. **State the scope** — region (US / Taiwan / China / global) × subject (single company / sub-sector / whole industry). A figure at a different scope is not a substitute
3. **Freshness** — unusable once it is older than the series' own update cycle (one quarter for quarterly, two months for monthly)
4. **No qualitative words as data** — "high", "strong", "robust" never become a score. Background prose only
5. **Tier** — 1st (Fed, SEMI, WSTS, company filings and earnings calls) > 2nd (TrendForce, Counterpoint, SMM and similar vendors) > 3rd (general news). Third tier evidences only that an event occurred

**A rejection, recorded:** adding a semiconductor capacity-utilisation indicator was scoped and dropped — TSMC publishes only qualitative language, SMIC's 93.7% is a scope mismatch (Chinese firm), and every candidate figure was six months stale. FRED (`CAPUTLG3344S`) returns 403 over both CSV and fetch; revisit if a free API key is obtained.

### Commodity producers — do not plug in the spot price
A producer's earnings are set by contracted volume, realised price, and position on the cost curve — not by spot.
- Case (SQM, 2026-09): Chinese lithium spot was **−10.3%** over one month while the stock was **+10.1%** over 20 days. Why: ① **80% of 2026 volume already contracted** ② realised price **$21.80/kg, +23% QoQ** (above the $18.14 spot) ③ Tier-1 cost of **$3–5/kg**, so falling prices remove higher-cost competitors first
→ Spot is directional context only. **Collect contracted share, realised price, and cost ranking alongside it.**
