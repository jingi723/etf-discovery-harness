---
name: etf-grading-standards
description: "Grading standards for the ETF Research Agent. Use this skill for every grade computed (A+ through D) — sector scores, theme structure, financial condition, valuation. Triggers on any scoring task needing weighted-average grades, grade-to-number mapping, coverage-based grade suspension, sub-sector valuation bands, macro sign flips by sector, bottom-detection methodology, or separating score computation from explanation."
---

# Grading Standards

The grade system every scoring agent follows. Core principle: **rules and scripts produce the score; the model explains it.** When the model picks the final grade by intuition, results move between runs and the reasoning cannot be traced.

## Grade scale

Ten levels: `A+ A0 A- B+ B0 B- C+ C0 C- D`. Numeric mapping A+=10 … D=1.

| Band | Meaning |
|---|---|
| A | Structure and data strongly support it |
| B | Sound, with points to verify |
| C | A weakness is confirmed, or the evidence is thin |
| D | A clear defect |

## Procedure (all scorers)

1. **Grade each item** — for every item (value chain / holding / criterion), in this order:
   - List the data obtained (figure + source + as-of date)
   - Apply the axis rubric (defined in each agent) to that data to reach a grade
   - Record in `rationale`, in one or two sentences, which datum tripped which criterion
   - If there is no data, leave the grade `null` and record it in `missing`. **Never estimate.**
2. **Compute the weighted average** — build an array of `{name, weight, grade}` and run the script:
   ```bash
   echo '{"items":[{"name":"AI semis","weight":35,"grade":"A-"}, ...]}' | python3 {this skill directory}/scripts/weighted_grade.py
   ```
   It returns `final_grade`, `numeric`, `coverage_pct`, and `contributions`. Never settle a final grade by mental arithmetic or intuition.
3. **Coverage gate** — if `coverage_pct < 60`, set the final grade to `null` and state `"Analysis limited — insufficient coverage"`. Between 60 and 80, grade it but drop confidence to `low`.
4. **Write the explanation** — cite the script's `contributions`. Include the principle that higher-weight items move the final grade more.

## Wording rules

- A grade describes a state. Do not translate it into forecast or recommendation language ("B+, so it looks promising").
- A C on the valuation axis is not "bad" — it is "a valuation premium is confirmed at current earnings", and it is stated alongside the growth context.
- Every final grade carries its as-of date, source count, `coverage_pct`, and `confidence`.

## Where "weak" begins (financial axis)

The financial rubric turns on how many areas are weak, but "weak" was undefined, and
two independent scorers reading identical figures split A- versus B0 on exactly that
word. Use these anchors so the boundary is a rule rather than a judgement call:

| Area | Weak when |
|---|---|
| Growth | Revenue growth below 0% YoY. **0–5% is modest, not weak** |
| Profitability | Operating margin below its sub-sector's typical range, or falling more than 5pp YoY |
| Balance sheet | Net debt/EBITDA above 3×, or interest coverage below 3× |
| Cash generation | Negative FCF outside a stated investment phase |

A range = no weak area. B range = one. C range = two or more. D = distress (sustained
losses plus excessive debt). These are conventions, not findings — they exist to make
runs reproducible, and changing them changes grades, so change them deliberately.

## Valuation — sub-sector multiple bands

Applying one P/E rule ("tech is 20–40×") misprices half the sector. **Normal multiples differ by sub-sector even within semiconductors.**

| Sub-sector | Normal P/E | Examples |
|---|---|---|
| Fabless | 20–35× (forward) | NVDA, AMD, AVGO, MRVL |
| Foundry | 15–25× | TSM |
| Memory | 8–15× (through-cycle) | MU, SK Hynix |
| Semi equipment | 25–50× | AMAT, LRCX |
| Utilities / IPP | 15–30× | CEG, PEG |
| Analog / mixed-signal IDM | **no band — see below** | TXN, ADI, NXPI, ON, STM, MCHP |

**Grading**: below the band → A range / inside the band → B range / 1–2× above → C range / more than 2× above, or lossmaking → D

### Analog IDMs are cyclical in the trough direction
Analog and mixed-signal IDMs sell into autos and industrials, so their earnings swing with that inventory cycle — and a trough inflates the P/E exactly as a peak deflates a miner's. **Check the margin before reading the multiple.** Measured across SOXX holdings on 2026-09-06:

| | P/E TTM | Net margin | Revenue YoY | |
|---|---:|---:|---:|---|
| NXPI | 19.3× | 22.6% | −2.7% | near-normal margin |
| TXN | 39.1× | 31.1% | +13.0% | normal margin — a real premium |
| ADI | 42.8× | 29.8% | +16.9% | normal margin — a real premium |
| ON | 47.1× | 10.2% | −15.3% | **trough** |
| STM | 99.0× | 3.5% | −10.8% | **trough** |
| MCHP | 102.8× | 8.8% | +7.1% | **margin still depressed** |

The 19–103× spread is not valuation dispersion; it is margin dispersion. Names at a normal ~25–30% net margin sit at 19–43×, and everything above that is a compressed denominator.

**Rule**: if an analog IDM's net margin is well below the ~25–30% peer normal, the P/E is uninformative. Grade on EV/Sales, P/B, and margin position within the cycle, and mark the P/E item neutral — the same treatment miners get, for the opposite reason. Do not fall back on the fabless band; these are different business models and it was only ever used as a loose stand-in.

### Commodity cyclicals do not get a P/E
Commodity miners (uranium, lithium, base metals) print their **lowest P/E at the earnings peak**. A low multiple may be a cycle-top signal, not a cheap stock.
- Case: SQM at a 48.9% operating margin (cycle-peak margin) with a forward P/E of 8.6×. That does not hold once lithium prices roll over
- **Instead**: judge miners on **P/B, EV/EBITDA, and cost-curve position**, and mark the P/E item neutral

## Macro flips sign by sector

**The same event pushes different sectors in opposite directions.** Never copy a macro grade across sectors.

| Event | Semiconductors | Nuclear / power | Lithium / EV | Why |
|---|---|---|---|---|
| Oil up | **Negative** | **Positive** | **Positive** | For semis the path is oil → inflation → rates → discount on high multiples (indirect). For nuclear it is alternative-energy demand; for EVs, economics versus combustion |
| Rates up | Negative | Negative (utilities especially) | Negative | In proportion to duration and capital intensity |

- Rate sensitivity also differs within a sector: utilities (dividend, capital-intensive) > IPP > miners (growth-like).
- **Oil's direct effect on semiconductor input costs is small.** The channel is rates, not costs. So do not look at oil alone — carry the 10-year and the hike probability to complete the chain.

## Bottom detection — institutional methodology

Judging a bottom by "distance above the low" alone **gives a falling knife full marks in a downtrend**, because the low keeps being reset. Split it in two layers.

### Short-term bottom — the Follow-Through Day (O'Neil/IBD)
1. **Rally attempt**: the most recent low is Day 1. A new low resets the count
2. **FTD condition**: from Day 4 onward, a close **+1.25% or better** (strong signals run 1.5–2%) **on higher volume than the prior day**
3. **Day 4–7 is optimal.** FTDs after Day 10 have a statistically weaker record
4. **Invalidation**: undercutting the rally-attempt low voids the FTD
5. **About a 20% failure rate** (O'Neil's own figure). Narrow participation raises it

**Its pair — the distribution day**: a close **−0.2% or worse on higher volume** is a footprint of institutional selling. In a 25-session window, **4–5 is a warning, 6 or more is a correction.**

### Structural bottom — three independent signal groups
Per institutional practice: no single indicator can call a cycle bottom; at least three independent signal groups must confirm.
- Range position (600-session basis) · distance from the 200-day · sub-sector valuation band
- Score each on five levels, then average

### Pullback or break — the Fibonacci retracement (validated)
Validated on SQM over 1,254 sessions and 35 retracements:

| Retracement | Sample | Recovered the prior high |
|---|---|---|
| 38.2–61.8% | 6 | **100%** |
| <38.2% | 1 | 100% |
| **≥61.8%** | 28 | **36%** |

- **61.8% is the decisive divider** (100% vs 36%)
- Holding the 200-day: 62% vs 41% when lost — weakly useful
- **The volume criterion (a reversal when volume comes in on the decline) has no discriminating power (43% vs 50%)** — contrary to the textbook. Not used
- Limits: one ticker, 35 events, and only 7 samples below 61.8%. Needs validation across more names

### What counts as support being defended
"Broke intraday, closed back above" is not enough. **The retest low must be higher** for it to count as a defence. If the lows keep falling, that is not a defence — it is a slow break in progress.
- Case: SOXX lows of 498.93 → 495.09 → 493.31 → 489.21 (four consecutive lower lows) on 28% lighter defending volume. It closed back above every time, and support was weakening throughout
