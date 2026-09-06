# How a judgment gets produced

This is the actual procedure, in order, with the mistakes that shaped each step. It
covers the single-ticker path (`etf-signal-scoring`). The multi-agent discovery
pipeline is in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 0. Decide which question you are answering

Two different jobs get confused constantly:

- **"What should I look at?"** → the discovery pipeline. Starts from the market regime
  and narrows: sector → theme → ETF candidates → verification.
- **"What state is this ticker in right now?"** → signal scoring. The target is already
  chosen. Everything below is this path.

## 1. Pick the horizon before you look at the chart

Choosing afterwards is how you end up justifying a conclusion you already reached.

| Horizon | Question | Macro weight | Valuation weight |
|---|---|---:|---:|
| `long` | Is this worth owning at all? | 40% | 15% |
| `swing` | Which way over the next month? | 10% | 5% |
| `short` | 3–10 sessions, leveraged vehicle | 5% | 0% |

Macro dominates the long horizon because rates set direction and the chart only sets
the entry. Valuation is zero at the short horizon because multiples do not move in a
week. Leveraged ETFs are always scored on `short`, with `long` quoted alongside as
context.

**Run at least two.** When they disagree, that is the finding. A two-day rally once
scored +7.5 on `swing` and −3.6 on `long` — the rally improved trend while it destroyed
the entry point. Reporting only the blend would have thrown that away. Name the
indicator that split them.

## 2. Collect data with the as-of date attached

```bash
python3 tools/score.py SOXX --horizon swing --holdings
```

Rules that exist because they were broken:

- **Never compare intraday data to a close-based statistic.** Cumulative volume 1.6
  hours into the session was compared to a 20-day average and read as "0.58× — volume
  is drying up". Time-normalised, it was 1.5–1.8×. The conclusion inverted.
- **Article date ≠ announcement date ≠ as-of date.** Record the as-of date, always.
- **Qualitative words are not data.** "Strong", "robust", "elevated" never become a
  score. Background prose only.
- **Scope must match.** A figure for Chinese fabs is not a substitute for a global
  one; a company number is not a sector number.
- **Stale is unusable.** A quarterly series more than one quarter old, or a monthly
  series more than two months old, is dropped rather than discounted.

## 3. Score seven indicators — the same seven, every time

Macro · valuation · trend · momentum · range position · relative strength · flows.

Fixing the indicator set is what makes horizons comparable. If each horizon used its
own indicators you could not point at the one that made them disagree.

Details that are not obvious:

**Momentum needs direction *and* participation.** Falling on rising volume is
distribution, and scores zero. Direction alone cannot tell a quiet drift from a
liquidation.

**Range position cannot be "distance above the low".** In a downtrend the low is set
again every day, so that formula gives a falling knife full marks. Use position within
the range plus distance from the 200-day.

**Macro flips sign by sector.** Rising oil is negative for semiconductors — through
inflation, then rates, then the discount on high multiples — and positive for nuclear
and lithium. Never copy a macro grade across sectors. The oil→semiconductor path runs
through rates, not through input costs, so the chain is incomplete unless you also
carry the 10-year and the hike probability.

**Valuation uses sub-sector bands, and skips cyclicals entirely.**

| Sub-sector | Normal P/E |
|---|---|
| Fabless | 20–35× |
| Foundry | 15–25× |
| Memory | 8–15× (through-cycle) |
| Semi equipment | 25–50× |
| Utilities / IPP | 15–30× |

Miners are excluded on purpose: a commodity producer's P/E is *lowest* at the earnings
peak. SQM printed a forward 8.6× P/E on a 48.9% operating margin — that is a
cycle-peak signature, not a cheap stock. Judge miners on P/B, EV/EBITDA and cost-curve
position instead.

**Leave an indicator empty rather than filling it with the wrong thing.** Korean
semiconductor flows were dropped from the flow indicator during a period when
shareholder-return programmes, not sector conviction, drove the numbers. A missing
indicator is honest; a misleading one is not.

## 4. Score the constituents, then check breadth

An ETF scored as a single chart hides the case where the index holds while its
internals fall apart. `--holdings` scores the top constituents and reports how many are
in an uptrend.

Six of eight largest holdings in a downtrend while the index bounces means the bounce
is a retracement. This was the mentor's actual requirement — *the ETF score is the
weighted sum of its constituents*, not a property of the index chart.

Korean ETF holdings come from the issuer's page, not from an API. See
[API_SETUP.md](API_SETUP.md).

## 5. Backtest any pattern before citing it

**No pattern goes into a written judgment until `tools/validate.py` shows it beats
baseline on that specific ticker.**

```bash
python3 tools/validate.py SOXX --pattern ftd --horizon 10
```

The output always compares the pattern's forward return against the return of picking
a random day. Things that failed this test and were removed:

- *Gap down, close near the high = institutional accumulation.* Looked convincing on
  three charts. Over 1,255 sessions and 44 events it was **worse than baseline**.
- *Volume expansion on a decline signals reversal.* 43% vs a 50% base rate. The
  textbook says otherwise; the data says it has no discriminating power.
- *Follow-through days mark the bottom.* On SOXX, **−2.47pp against baseline** — a
  real, inverted signal. Textbook patterns still need per-ticker validation.

What survived:

- *The 61.8% Fibonacci retracement is a dividing line.* On SQM over 1,254 sessions and
  35 retracements: shallower than 61.8% recovered the prior high 7/7; deeper recovered
  10/28. Sample is one ticker — treat as provisional.
- *Distribution-day counting* as a warning, not a timing signal.

**Bottom calls need three independent signal groups.** No single indicator names a
cycle low. Range position over ~600 sessions, distance from the 200-day, and sub-sector
valuation band — scored separately, then averaged.

**Support is "defended" only when the retest low is higher.** A close back above the
level is not enough. SOXX printed lows of 498.93 → 495.09 → 493.31 → 489.21 while
closing above the level each time, on 28% lighter volume. That was not a defence; it
was a slow break.

## 6. Write the judgment

- **Number first, interpretation second**, one line per indicator.
- **Every level is quoted on the underlying index**, never the leveraged vehicle. SOXL
  and SOXS are path-dependent, so the same SOXX level maps to a different price every
  time. They are the order-entry instrument; SOXX is the ruler. Measured capture:
  101–108% in trending markets, 74–88% in chop.
- **Negative evidence is mandatory.** A note with no negatives is incomplete, not
  clean. If you looked and found none, write "insufficiently verified" — not "no risk".
- **Do not smuggle in judgment from outside the score.** If you want to argue the
  second-ranked name is actually better, either say explicitly what you added outside
  the score, or add it as an indicator. This rule exists because I once ranked LITP
  above LIT while LIT scored 78.8 to LITP's 73.8, and the entire gap was the trend
  indicator.
- **State the score's meaning.** It measures how many conditions are met. It is not an
  expected return.
- **A leveraged trade needs a time stop as well as a price stop.** Negative compounding
  makes "right eventually" indistinguishable from wrong.

Banned phrasings and the four-state verdict vocabulary are in
`.claude/skills/etf-compliance-rules/`.

## 7. Record what was dropped

Failed hypotheses are the most reusable output here. Three from this repo's own log:

- **Korean semiconductor exports +209%** was cited as resolving a concern about AI
  capex sustainability. It does not — it is shipment data for a period already past,
  and the stocks fell over the two days after its release. Retracted.
- **AMAT rising more than Micron** was offered as evidence the move was not
  memory-driven. Measured correlation of AMAT to MU is 0.703 (LRCX 0.754), so the
  comparison proves nothing. Replaced with a benchmark against 135 historical
  "MU +3–5%" days, where KLAC ran +5.21pp hot and NVDA −1.44pp / AVGO −2.65pp cold.
- **A semiconductor capacity-utilisation indicator** was scoped and rejected: TSMC
  publishes only qualitative language, SMIC's 93.7% is a scope mismatch, and every
  candidate figure was six months stale. FRED's series returns 403 without a key.
  Shelved with the reason recorded, so it is not re-proposed blind.

---

## How reproducible is any of this?

Two agents scored the same 12 holdings from the same data without seeing each other's
output — SMH and SOXX overlap, and their financial scorers ran in parallel. That is a
free reproducibility test, and it is worth knowing the answer before trusting a grade.

| Gap between the two independent scorers | Holdings |
|---|---:|
| identical | 6 |
| 1 notch | 5 |
| 2 notches | 1 |

**11 of 12 within one notch, and the ETF-level grades were unaffected** — both came out
B+, both reproducing exactly against `weighted_grade.py`. The weighted average absorbs
per-holding noise of that size.

The widest gap was not a data difference. Both scorers pulled identical figures for
Applied Materials — revenue +4.4%, operating margin 30.5%, D/E 0.29 — and split on
whether +4.4% growth counts as "one weak area". The rubric had not said, so it now
does: growth below 0% is weak, 0–5% is modest. Anchoring that boundary is what turns a
judgement call back into a rule.

**Read grades at the level they were measured.** A single holding's grade carries about
a notch of noise. The ETF-level grade, which is what ETF Research Agent actually reports, does
not.

## A known limitation: purity is a weak filter

Phase 8.5 picks which ETFs get deep-scored using `purity_pct` alone, and two cases in
one run showed the metric hiding what matters.

**Concentration inflates it.** Chain-stage coverage ran opposite to purity across four
AI-accelerator candidates: SMH ranked first on purity (55.0%) while holding nothing at
all in two of the theme's five value-chain stages, and AIQ ranked third (44.7%) as the
only fund covering all five. High purity meant weight piled into one stage, not that the
fund held the theme well.

**It can be near-perfect with zero exposure to the theme's own bottleneck.** WCLD maps at
99.99% purity because cloud software is one of the theme's defined stages — but that
theme's evidence names power and grid interconnection as the binding constraint, and
WCLD holds no hyperscaler, no data-center REIT, and no power name.

A coverage-aware filter would have picked differently in one of four slots. Whether it
would have picked *better* is not established, so the filter is unchanged and this is
recorded as a limitation rather than fixed. Read `purity_pct` alongside the chain
breakdown, never alone.
