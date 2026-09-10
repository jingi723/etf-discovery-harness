# Structure and events — what the indicators can and cannot do

Measured 2026-09-08. Every figure here is reproduced by `tools/eventstudy.py`.
The universe is 20 tickers spread across sectors and themes (the `UNIVERSE`
constant), the benchmark is SPY, and the window runs 2021-09 to 2026-09,
roughly 1,250 sessions.

```bash
python3 tools/eventstudy.py all          # all four measurements below
python3 tools/eventstudy.py self-check   # checks for future-data leakage
```

---

## Summary — three layers

```
chart structure       -> tells you event frequency. Not direction.
fundamental structure -> sets an event's sign and its timing   <- what we don't collect
event                 -> actually happens. Direction and size become known.
```

Indicators are not a predictor. They are a **filter**. On their own they miss the
next month entirely (IC −0.065), but after an event lands they do separate "this
will retrace" from "this is the trend confirming" (down-shock Q4−Q1 +2.76pp).

---

## Measurement 1 — the score alone does not forecast a month ahead

`python3 tools/eventstudy.py ic` · 20,460 observations

Only the five chart indicators of the one-month profile are used, since macro and
valuation are hand-supplied and cannot be reconstructed for a past date. The
remaining weights are renormalised.

| Score band | n | mean 20-session return | win |
|---|---:|---:|---:|
| 🔴 80+ | 437 | **+0.45%** | 50.8% |
| 🟠 60–80 | 7,224 | +1.08% | 55.8% |
| 🟡 40–60 | 9,797 | +1.51% | 58.7% |
| 🟢 20–40 | 2,999 | **+2.19%** | 60.5% |
| all (baseline) | 20,460 | +1.44% | 57.7% |

**IC = −0.065.** The top band does not reach a third of the baseline.

The cause is that the indicators cancel each other. `score_position` rewards the
bottom of the 60-day range (contrarian) while `score_trend` and `score_momentum`
reward rising prices (trend-following). Averaged together they erase each other.

Individually they carry no forecast either.

| Indicator | IC (forward excess return) |
|---|---:|
| trend | +0.010 |
| momentum | +0.015 |
| position | −0.013 |
| rs | +0.016 |
| flow | −0.028 |

Raw values, before banding, do slightly better. **20-day return +0.035,
120-day return +0.057.** Turning a number into a five-level band costs signal,
and the longer lookback is the stronger one.

> This does not invalidate the harness. The README already says the score
> "measures how many conditions are met, not an expected return". The measurement
> confirms that sentence. The mistake was ours, in reading it as a forecast.

---

## Measurement 2 — after an event they do separate. Down-shocks only

`python3 tools/eventstudy.py shock` · 1,157 shocks (|daily return| > 2σ)

### Down-shocks (n=581) — 120-day momentum decides

| 120-day momentum before the shock | n | next-20d excess |
|---|---:|---:|
| Q1 (−38.7 to −3.5%) | 145 | **−1.61pp** |
| Q2 (−3.4 to +6.0%) | 145 | −0.26pp |
| Q3 (+6.0 to +14.9%) | 145 | +0.66pp |
| Q4 (+15.2% and up) | 146 | **+1.15pp** |

**Q4−Q1 spread +2.76pp, monotonic.** That is wider than the same indicator
measured unconditionally. Indicators get stronger when tied to an event.

The reading is simple: **bad news into an uptrend comes back; bad news into a
downtrend keeps going.** The first is a correction, the second is confirmation.

### Up-shocks (n=576) — the indicators say nothing

| 120-day momentum before the shock | next-20d excess |
|---|---:|
| Q1 | +0.69pp |
| Q2 | −0.14pp |
| Q3 | −0.03pp |
| Q4 | +0.79pp |

**Q4−Q1 spread +0.10pp**, U-shaped — both ends good, the middle bad. Cutting on
range position gives the same (+0.25pp).

**How far good news travels is not something a chart knows.** This is where a news
pipeline is needed, and nowhere else.

---

## Measurement 3 — structure tells you frequency, not direction

`python3 tools/eventstudy.py rate` · 20,460 observations

At each point, count the 2σ shocks over the following 20 sessions.

| Structure indicator | total shocks | net (up−down) Q5−Q1 |
|---|---|---:|
| 120-day momentum | 1.06 → 1.29 | −0.00 |
| 60-day range position | 1.09 → 1.33 | −0.07 |
| volume trend | 0.99 → 1.25 | +0.09 |
| gap to the 200-day | 1.01 → 1.34 | −0.10 |

**Total frequency varies by up to 33%, but net shocks are flat.** Events cluster
at the extremes (a very strong trend, or a very deep drawdown) and go quiet in the
middle — a U shape that holds across all four indicators.

**Do not lean on the frequency result.** Much of it is likely volatility
clustering, which is a known phenomenon rather than new information. The robust
finding is **that net shocks are zero**, and that held across all four.

### Why this result is unsurprising

Everything here is **chart** structure, which is the mark a resolved imbalance left
on price — not the cause of the next event. Reading a result and trying to infer
the cause from it will not give you direction.

---

## Measurement 4 — what an event does to the score

`python3 tools/eventstudy.py shift` · 576 up-shocks

```
total score  55.2 -> 57.2   (+2.0)
fell in 39% of cases

  trend      61.2 -> 66.7    +5.4
  momentum   54.9 -> 67.8   +12.9
  position   49.7 -> 30.1   -19.6   <- the only penalty
  rs         50.8 -> 61.4   +10.6
  flow       61.0 -> 63.7    +2.6
```

**"Good news raises the price and so lowers the score" is true of `position`
only.** It drops 19.6 points, but the other four more than offset it and the total
*rises* 2.0. In 61% of cases the score does not fall at all.

Nor is there evidence the penalty is wrong.

| | n | next-20d excess | win |
|---|---:|---:|---:|
| score fell | 224 | +0.26pp | 50% |
| score held or rose | 352 | +0.37pp | 53% |

A gap of 0.11pp. **The score is not saying the wrong thing about an event; it is
saying nothing at all.** It is neither right nor wrong — it is unrelated.

---

## Design conclusions

### What not to do — adding events as an eighth indicator

Fed into a weighted average, an event score is diluted by the other six, exactly
as `position` losing 19.6 points and `momentum` gaining 12.9 cancel today.
Measurement 3 says the same thing: up-shocks are not separable by indicator.

The score also describes the *present* rather well. Mixing future information into
it degrades the part that already works.

### What to do — keep them separate and show both

```
score (diagnosis)   unchanged. "what state is this in now"
event (separate)    beside the score, never inside it
                    type · certainty · size · whether price already moved
weight              decided by reading both
range               the price band over which that weight holds
```

The nuclear case demands this shape. "Low score (bottom of range, weak trend) plus
a live event (high certainty, large, not yet priced)" is a genuine conflict and has
to be shown as one, with position size as the answer. Collapse it into a single
number and one of the two disappears.

### Fundamental structure — what creates direction

"Structure" is not valuation. It is an **unresolved imbalance**. A P/E of 8 forces
nothing; ten days of inventory forces one of three things — a price rise, an
expansion, or allocation. All three point up. The sign of the imbalance sets the
direction of the events. Oversupply inverts it: cuts, closures, write-downs.

### Tension — how structure enters a short horizon

If the sign sets direction, **tension sets timing.** Structure works over quarters
and years and cannot push a price inside a month, but it does set **the probability
that an event lands within the month.** That is the only route by which structure
enters a short-horizon judgment.

```
tension = buffer / drawdown rate = time remaining
  time remaining on the same order as the judgment window -> high hazard, use it
  time remaining ten times the window or more             -> do not use it
```

The same "structure is bullish" means opposite things depending on tension.

| | buffer | drawdown rate | time remaining | 1-month hazard |
|---|---|---|---|---|
| Memory | finished inventory 10 days (28–42 normal) | already below threshold | 0 | **very high** |
| Lithium | 109,000 t surplus | 1,500–80,000 t/yr deficit | 1.4–70 years | low |

In memory, a broker note that appeared on no calendar was published at 08:12 on
2026-09-07 and moved SK Hynix +8.26% that day. **The structure produced the event;
the catalyst did not arrive from outside.** Lithium has over a year of buffer, so
nobody has a reason to announce an emergency expansion — which is why its structure
is bullish and its one-month read is still negative.

The point is that this is **negative because tension was used, not because
structure was excluded**. Shrink the buffer to 30 days and the same structure with
the same sign turns the one-month read positive.

> Not yet measured. Measurement 3 only showed chart structure moving event
> frequency by 33%; whether fundamental tension separates better than that needs an
> event log. For now it is a hypothesis with a clear mechanism.

Collection difficulty varies sharply by layer.

| Item | Difficulty | Frequency | Lag | Source |
|---|---|---|---|---|
| Days of inventory, turns | low | quarterly | 45–90d | FMP statements (Korean tickers included) |
| Revenue and COGS growth | low | quarterly | 45–90d | FMP |
| Industry utilisation | low | monthly | 30–40d | FRED `CAPUTLG3344S`, no key needed |
| Petroleum inventories, demand, crack | low | weekly | ~5d | EIA weekly report, no key needed |
| Capex guidance | medium | quarterly | manual | earnings decks |
| Backlog ÷ annual revenue | medium | quarterly | manual | filings |
| Channel and customer inventory | **high** | — | — | not disclosed. Calls and broker notes only |
| Spot minus contract price | high | weekly | — | TrendForce and similar, paid |
| Lead times | high | monthly | — | paid research |

**The item that matters most is the hardest to get.** Balance-sheet days of
inventory (SK Hynix at 121.5 days when measured) and the market's "10 days of
memory" **are different layers** and must never be mixed.

---

## What to take from the news — facts, not sentiment

Uncertainty in news-derived data has to be split by layer.

```
1. Fact:      "KB Securities published, at 08:12 on 2026-09-07, that inventory
               is under 10 days"     -> no uncertainty. Verified by tracing it.
2. Estimate:  "inventory is actually 10 days"
               -> uncertain. An analyst estimate, not a disclosure.
3. Reading:   "so it goes up"        -> the most uncertain of the three.
```

**Only (1) belongs in an event log.** Whether inventory is really 10 days or 13 does
not matter to measuring "the 20-day return after a note like that appears".
Score sources by hit rate and you no longer have to assign the weights yourself.

Fields for the log — all of them either numbers or four-to-five categories. No
arbitrary quantification such as a sentiment score.

```
published at | subject | type | certainty (signed / announced / in talks / observed)
size (% of existing revenue) | timing (this quarter / next year / unknown)
source | price reaction after publication
```

### A worked entry

```
2026-09-07 08:12 | Samsung Electronics, SK Hynix | supply shortage | certainty: estimate (broker)
size: under 10 days against a normal 4-6 weeks | cause: HBM4 eating capacity
source: KB Securities | reaction: SK Hynix +8.26%, KOSPI +4.61% same day,
foreign +2.55tn KRW, institutions +2.63tn
```

This one was **published before the open (08:12)** and was the direct cause of the
day's move. Miss the same-day house note and you attribute the move to something
else.

---

## Limits

- **The event definition is backward-looking.** Right now an event is a 2σ move,
  which catches the price after it has gone. It is especially late on up-shocks.
  Once a news log exists this should be redefined on publication time.
- **Observations overlap.** The 20-day forward return is computed every day, so the
  windows are nested. Two thousand observations may look large, but the independent
  sample is closer to a twentieth of that. Read the direction; never treat the
  second decimal as a confidence interval.
- **IC estimates are unstable.** Split by year, the composite IC runs from −0.309
  (2022) to +0.003 (2025). The sign is consistent — negative in four of five years
  and in both halves — but the magnitude is not. The 120-day momentum result is
  weaker still: negative in 2024 and 2026. **Do not swap an indicator on the third
  decimal place.**
- **US ETFs only.** Korean tickers and funds were not tested.
- **Macro and valuation were excluded** because they are hand-supplied and cannot
  be reconstructed for a past date. Macro carries 40% at the long horizon, so the
  conclusions here apply to the one-month profile only.
- **Volatility clustering is mixed into the frequency result.** See the caution in
  Measurement 3.

## Next

1. Fix the event-log schema and fill thirty or so entries — the nuclear agreement,
   the KOSPI upgrade, the buyback, the KB memory note.
2. Let a backtest assign weights per event type. Do not assign them by hand.
3. `tools/structure.py` already automates the low-difficulty rows above; extend it
   as more become reachable.
4. Build a rule that separates up-shocks by the nature of the event. The chart
   provably cannot, which makes this the one place news is required.
