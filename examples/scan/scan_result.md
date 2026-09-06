# Scan result — 2026-09-06

US market, two sectors. Produced by the orchestrator's **scan** path: two agents
(`etf-candidate-finder`, one per sector) plus `tools/score.py`, reusing a same-day
market regime. 167k agent tokens, 58 network requests.

Prices as of the 2026-09-04 close. **These numbers are historical.**

> Research notes, not investment advice. Nothing here is a recommendation to buy or sell.

## Ranking (one-month profile)

| | ETF | Sector | Long | 1-month | Short | Breadth | Gate |
|---|---|---|---:|---:|---:|:--:|---|
| 🟠 | **XLE** | energy & power | 59.2 | **65.0** | 64.3 | 6/6 | conditional |
| 🟠 | **XOP** | energy & power | 59.2 | **65.0** | 64.3 | 6/6 | conditional |
| 🟡 | **XLK** | information technology | 32.2 | **49.5** | 48.2 | 3/6 | conditional |
| 🟡 | **RSPT** | information technology | 27.8 | **42.9** | 42.0 | 6/6 | conditional |
| 🟢 | **XLU** | energy & power | 33.2 | **36.1** | 35.2 | 1/6 | conditional |
| 🟢 | **SMH** | information technology | 16.1 | **36.0** | 35.6 | 1/6 | conditional |

Breadth is how many of the top holdings sit with the 20-day above the 60-day.

**XLE and XOP tie on every indicator.** That is not a rounding artifact — their
20-day return, relative strength, range position, distance from the high and volume
trend all agree in direction and magnitude. They occupy the same signal state. What
separates them is structure: XLE is 35% ExxonMobil and Chevron, XOP is 51 names
near-equally weighted. The scan does not measure that; the full pipeline's
value-chain mapping does.

## Macro is not one number

Every fund here was scored against the *same* regime — rates rising with a 60-67%
September hike probability, WTI up 9% on the week. The macro input still differs by
sector, because the same event flips sign:

| Sector | Macro | Why |
|---|---:|---|
| Energy (XLE, XOP) | 62 | Oil up is the direct driver; the rate headwind is secondary |
| Utilities (XLU) | 30 | Rate-sensitive by duration and capital intensity, and oil does not help |
| Broad tech (XLK, RSPT) | 15 | Oil reaches tech through rates, so both inputs point the same way |
| Semiconductors (SMH) | 12 | The same, plus the longest duration in the sector |

Copying one macro score across these would have inverted the ranking.

## Per fund

### XLE — Energy Select Sector SPDR

`64.06` (-0.87%) · 1-month **65.0** 🟠 · long 59.2 · short 64.3

- 🟠 External: 62 *(weight 10%)*
- 🟡 Valuation: 50 *(weight 5%)*
- 🔴 Chart (trend): 100 *(weight 25%)*
- 🟠 Momentum: 75 *(weight 20%)*
- 🔵 Position: 0 *(weight 20%)*
- 🔴 Relative strength: 100 *(weight 15%)*
- 🟢 Volume / flows: 25 *(weight 5%)*

  20d +11.41% · rs +11.81pp · range position 89% · from 60d high -2.23% · volume 0.81x

  Top holdings: 🟠 XOM 19.9% (62) · 🟠 CVX 15.2% (68) · 🟠 COP 6.3% (68) · 🟠 MPC 5.6% (72) · 🟠 PSX 5.5% (66) · 🟠 VLO 5.2% (66)

  Structure gate: **conditional** — tradability metrics unobtained: spread_pct, tracking_error, premium_discount_pct

### XOP — SPDR S&P Oil & Gas E&P

`190.71` (-0.84%) · 1-month **65.0** 🟠 · long 59.2 · short 64.3

- 🟠 External: 62 *(weight 10%)*
- 🟡 Valuation: 50 *(weight 5%)*
- 🔴 Chart (trend): 100 *(weight 25%)*
- 🟠 Momentum: 75 *(weight 20%)*
- 🔵 Position: 0 *(weight 20%)*
- 🔴 Relative strength: 100 *(weight 15%)*
- 🟢 Volume / flows: 25 *(weight 5%)*

  20d +14.61% · rs +15.01pp · range position 91% · from 60d high -2.11% · volume 0.76x

  Top holdings: 🟠 PBF 3.9% (66) · 🟠 DINO 3.3% (66) · 🟠 MPC 3.2% (72) · 🟠 DK 3.2% (79) · 🟠 VLO 3.1% (66) · 🟠 PARR 3.1% (66)

  Structure gate: **conditional** — tradability metrics unobtained: spread_pct, tracking_error, premium_discount_pct

### XLK — Technology Select Sector SPDR

`187.28` (+0.70%) · 1-month **49.5** 🟡 · long 32.2 · short 48.2

- 🔵 External: 15 *(weight 10%)*
- ⚪ Valuation: n/a — excluded, weights renormalised *(weight 5%)*
- 🔴 Chart (trend): 100 *(weight 25%)*
- 🟡 Momentum: 40 *(weight 20%)*
- 🟢 Position: 25 *(weight 20%)*
- 🟡 Relative strength: 50 *(weight 15%)*
- 🔵 Volume / flows: 0 *(weight 5%)*

  20d -0.37% · rs +0.03pp · range position 75% · from 60d high -3.61% · volume 0.57x

  Top holdings: 🟡 NVDA 14.9% (59) · 🟠 AAPL 13.0% (63) · 🟡 MSFT 10.2% (46) · 🟡 AVGO 4.6% (41) · 🟡 MU 4.0% (52) · 🟢 AMD 3.8% (38)

  Structure gate: **conditional** — tradability metrics unobtained: tracking_error, premium_discount_pct

### RSPT — Invesco S&P 500 Equal Weight Technology

`64.16` (-0.16%) · 1-month **42.9** 🟡 · long 27.8 · short 42.0

- 🔵 External: 15 *(weight 10%)*
- ⚪ Valuation: n/a — excluded, weights renormalised *(weight 5%)*
- 🟠 Chart (trend): 75 *(weight 25%)*
- 🟡 Momentum: 40 *(weight 20%)*
- 🟢 Position: 25 *(weight 20%)*
- 🟡 Relative strength: 50 *(weight 15%)*
- 🔵 Volume / flows: 0 *(weight 5%)*

  20d -0.76% · rs -0.36pp · range position 70% · from 60d high -4.08% · volume 0.55x

  Top holdings: 🟢 ZBRA 2.2% (37) · 🟠 CRM 2.0% (69) · 🟠 WDAY 1.9% (73) · 🟠 DELL 1.8% (69) · 🟠 SMCI 1.8% (62) · 🟡 PLTR 1.7% (49)

  Structure gate: **conditional** — tradability metrics unobtained: tracking_error, premium_discount_pct

### XLU — Utilities Select Sector SPDR

`43.08` (+0.12%) · 1-month **36.1** 🟢 · long 33.2 · short 35.2

- 🟢 External: 30 *(weight 10%)*
- ⚪ Valuation: n/a — excluded, weights renormalised *(weight 5%)*
- 🟢 Chart (trend): 25 *(weight 25%)*
- 🔵 Momentum: 0 *(weight 20%)*
- 🟠 Position: 75 *(weight 20%)*
- 🟡 Relative strength: 50 *(weight 15%)*
- 🟡 Volume / flows: 50 *(weight 5%)*

  20d -1.22% · rs -0.82pp · range position 26% · from 60d high -7.61% · volume 1.00x

  Top holdings: 🟡 NEE 13.1% (46) · 🟡 SO 7.5% (47) · 🟢 DUK 7.1% (39) · 🟠 CEG 6.8% (63) · 🟡 AEP 5.1% (48) · 🟡 D 4.3% (50)

  Structure gate: **conditional** — tradability metrics unobtained: spread_pct, tracking_error, premium_discount_pct

### SMH — VanEck Semiconductor

`567.01` (+2.61%) · 1-month **36.0** 🟢 · long 16.1 · short 35.6

- 🔵 External: 12 *(weight 10%)*
- ⚪ Valuation: n/a — excluded, weights renormalised *(weight 5%)*
- 🟢 Chart (trend): 25 *(weight 25%)*
- 🟡 Momentum: 40 *(weight 20%)*
- 🟠 Position: 75 *(weight 20%)*
- 🟢 Relative strength: 25 *(weight 15%)*
- 🔵 Volume / flows: 0 *(weight 5%)*

  20d -2.69% · rs -2.30pp · range position 38% · from 60d high -15.60% · volume 0.56x

  Top holdings: 🟡 NVDA 23.8% (59) · 🟡 TSM 9.7% (48) · 🟡 AVGO 5.9% (40) · 🟡 MU 5.6% (51) · 🟢 AMD 5.3% (38) · 🟡 ASML 5.0% (40)

  Structure gate: **conditional** — tradability metrics unobtained: tracking_error, premium_discount_pct

## What this scan did not check

- **Theme purity** — whether a fund's holdings actually sit in the value chain its name implies.
  In a full run on the same day, two semiconductor ETFs turned out to hold 55% and 50% of their
  weight outside their own theme.
- **Holdings-level financials** — revenue growth, margins, leverage, per constituent.
- **Valuation beyond the sub-sector band** — no own-history or growth-adjusted comparison.
- **Tracking quality** — spread, premium/discount and tracking error were unobtainable from FMP,
  which is why every fund is capped at `conditional` rather than reaching `pass`.

Deepening any of these means continuing from Phase 4 of the full pipeline against the
same workspace, at roughly 60 agents rather than two.
