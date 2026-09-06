---
name: etf-signal-scoring
description: "Standard for scoring one already-chosen stock or ETF across 7 indicators × 3 time horizons. Use this skill when asked what state a specific ticker is in right now, to write a daily or weekly judgment, to check an open position, to compare two tickers, to judge a leveraged ETF over days, to score constituents for a heatmap, or to validate a chart pattern statistically. The discovery pipeline (sector → theme → ETF) belongs to etf-discovery-orchestrator; this skill is for when the target is already decided."
---

# Signal Scoring (7 indicators × 3 horizons)

The discovery harness answers *what should I look at*. This skill answers **what state is this already-chosen target in**. Daily judgments, position checks, and head-to-head comparisons all live here.

The discovery pipeline also calls it, at Phase 11.5, to put a current-state score next to each finalist's three structural grades — the axes say whether a product is sound, not whether now is a reasonable moment. It costs about 15 API calls per ETF and no agent tokens.

**Absolute rule**: the script produces the score, the model only interprets it. Never eyeball the indicators and call a total.

```bash
python3 tools/score.py SOXX --horizon swing --holdings
python3 tools/score.py LIT  --horizon long --sub-sector miner --benchmark SPY
```

## The seven indicators

Every horizon uses the **same seven**. Only the weights and measurement windows change. Fixing the set is what lets you put two horizons side by side and point at the indicator that made them disagree.

| Indicator | What it measures | Primary data |
|---|---|---|
| Macro | Which way rates, oil, and policy push *this sector* | 10-year, fed-funds futures probability, oil |
| Valuation | Multiple against the sub-sector band | P/E, P/B, EV/EBITDA |
| Trend | 20-day vs 60-day, close against the averages | Daily bars |
| Momentum | 20-day return **and whether volume confirms it** | Daily bars |
| Position / bottom | Position in the 60-day (short) or full (long) range, distance from the 200-day | Daily bars |
| Relative strength | 20-day excess return vs the benchmark | Daily bars |
| Flows | Volume trend, investor-type net buying (KR), put/call | Toss API / AlphaQuery |

### Notes that are not obvious

- **Momentum needs direction and participation.** Falling on rising volume is distribution, so it scores zero. Direction alone cannot separate a quiet drift from a liquidation.
- **Position cannot be "distance above the low".** In a downtrend the low resets daily, which gives a falling knife full marks. Use range position plus distance from the 200-day.
- **Macro flips sign by sector.** Rising oil is negative for semiconductors (via rates) and positive for nuclear and lithium. Never copy a grade across sectors — see the table in `etf-grading-standards`.
- **Valuation uses sub-sector bands, and miners get no P/E at all.** Cyclicals print their lowest multiple at the earnings peak.

### Scoring macro (40% of the long horizon — this is where runs diverge)

`--macro` in `tools/score.py` is the one value a human supplies. Leaving the default of 50 (neutral) makes 40% of the long-horizon score meaningless, so **always fill it using this procedure:**

1. Pick the one dominant macro variable for the sector (semis and growth = US 10-year; utilities and nuclear = rates plus power demand; lithium and EV = rates plus commodity prices; defence = fiscal spending).
2. Establish its **direction**, recording the figure and its as-of date.
3. Use the sign-flip table in `etf-grading-standards` to judge favourable or unfavourable for this sector.
4. Convert with the band below.

| Score | Condition |
|---|---|
| 100 | Dominant variable clearly favourable, and policy/events point the same way |
| 75 | Favourable direction, but only one supporting source |
| 50 | Mixed, or insufficient basis — **use this when you don't know** |
| 25 | Unfavourable, but weakly |
| 0 | Clearly unfavourable, with a near-term event (FOMC, CPI, payrolls) that could worsen it |

**If you could not establish a basis, use 50 and say "macro not assessed" in the judgment.** Never quietly pass 50 and write as though it had been assessed.

### A missing indicator is excluded, not filled in

`tools/score.py` drops any indicator with no data and renormalises the remaining weights, reporting the coverage; below 60% it suspends the score entirely. Quote the coverage whenever it is under 100%.

This matters most for **valuation on an ETF**: FMP's `ratios-ttm` returns nothing for a fund, so `value` reads `n/a`. That is correct — an ETF has no P/E of its own. To grade an ETF's valuation, score its holdings (`--holdings`, or the pipeline's holdings-valuation-scorer). Never let a gap stand in as a number.

- **The flow indicator only looks at the volume trend.** In `tools/score.py` it is 20-day volume over the prior 40-day volume — a weak proxy. If you obtained put/call or investor-type flow, quote those figures in the judgment and note that the score itself rests on the proxy.
- **Leave an indicator empty rather than filling it with the wrong thing.** Korean semiconductor flows were dropped during a period when shareholder-return programmes, not sector conviction, drove the numbers. A missing indicator is honest; a misleading one is not.

## Three horizons and their weights

| Indicator | `long` | `swing` (default) | `short` (3–10 sessions) |
|---|---:|---:|---:|
| Macro | 40 | 10 | 5 |
| Valuation | 15 | 5 | 0 |
| Trend | 15 | 25 | 25 |
| Momentum | 5 | 20 | 25 |
| Position / bottom | 15 | 20 | 20 |
| Relative strength | 5 | 15 | 15 |
| Flows | 5 | 5 | 10 |

- **Long is 40% macro** because rates set the direction and the chart only sets the entry.
- **Short is 0% valuation** because multiples do not move in a week.
- **If the target is leveraged (SOXL/SOXS/LITP and the like), short is the primary horizon** and long is quoted alongside as context.

### Horizons disagreeing is normal
The same two-day rally once scored +7.5 on the one-month profile and −3.6 on the long-term profile: the rally raised the trend score while destroying the position score (further from a cheap entry). **When the axes split, name the indicator that split them.** Comparing only the totals throws the information away.

## Five signal levels (Korean market convention: red is positive)

`🔴 80+ / 🟠 60–80 / 🟡 40–60 / 🟢 20–40 / 🔵 0–20`

The score measures **how many conditions are met, not an expected return.** Never translate "80 points" into "8% upside".

## An ETF's score is the weighted sum of its constituents

Scoring an ETF from its own chart alone hides the case where the index holds while its internals fall apart. Use `--holdings` to score the top constituents and report **breadth**: how many of the top ten sit with the 20-day above the 60-day. Six of eight largest holdings in a downtrend means an index bounce is more likely a retracement than a bottom.

Korean ETF holdings return an empty array from FMP `etf/holdings`. Collect them from the issuer's official page.

## Validate a pattern before asserting it

**Repository rule: a pattern that has not passed a backtest does not go into a judgment.**

```bash
python3 tools/validate.py SOXX --pattern ftd --horizon 10
```

The output always shows three things — the pattern's forward return, the return of picking any random day (baseline), and the difference. If it does not beat baseline, it is noise.

Actually dropped:
- *"Gap down closing near the high = institutional accumulation"* — 1,255 sessions, 44 events, **worse than baseline**. Dropped.
- *"Volume on the decline signals a reversal"* — no discriminating power (43% vs 50%). Not used.
- *SOXX's Follow-Through Day* was **−2.47pp against baseline** over 1,255 sessions — an inverted signal. Even textbook patterns are re-validated per target.

Survived:
- *The 61.8% Fibonacci retracement* — 100% recovery of the prior high below the line, 36% above it. A decisive divider.

## Three common errors

1. **Never compare intraday data to a close-based statistic.** Cumulative volume 1.6 hours into a session was once read against a 20-day average as "0.58× — volume is drying up". Normalised for elapsed time it was 1.5–1.8×, and the conclusion inverted.
2. **Support is defended by a higher low, not by a close back above the level.** Lows of 498.93 → 495.09 → 493.31 → 489.21 closed back above the level every time while support was breaking down.
3. **Do not smuggle in judgment from outside the score.** To argue the second-ranked name is actually better, either say explicitly what you added outside the score, or fold that basis in as an indicator.

## Judgment output format (fixed)

**This format is fixed.** Do not merge or drop lines. Asked about several tickers, emit this block separately for each.

It has to paste into a chat client, so **no markdown tables, headers, or blockquotes** — they break in messengers. Plain text and line breaks only.

```
{TICKER} {holding/entry} call | {date} ({market} {weekday} close)

Volume:      {multiple of the 20-day average} — reading
Flows:       {put/call, investor-type net buying, ETF creations} — reading
Chart:       {% from the 60-day high and low, support and resistance} — reading
Holdings:    {top 8 by 60-day position and trend (20>60), count} — does "most constituents are near a bottom" hold?
Events:      {today's and this week's catalysts, plus any pattern validated with historical numbers}
Valuation:   {top holdings' P/E and EV/EBITDA against the sub-sector band} — cheap or rich
External:    {rates, FX, policy}
Constituents: 🔴 {strong} / 🟡 {watch} / 🔵 {weak}

Structural reason: {2–3 sentences on why it is in this state, from industry structure — not from the scores}

Conclusion: {2–3 conversational sentences. The call, the stop and target levels (on the underlying index), and a plain statement of what would prove it wrong}
```

For a Korean request, use the Korean field labels — this is the established wording, not a fresh translation:

```
{티커} {보유/진입} 판단 | {날짜} ({시장} {요일} 종가 기준)

거래량: {20일 평균 대비 배율} — 해석
수급: {풋/콜, 투자자별 순매수, ETF 자금유출입} — 해석
차트(지수): {60일 고점·저점 대비 %, 지지·저항 레벨} — 해석
차트(구성종목): {상위 8종목의 60일 위치·추세(20선>60선) 개수} — "구성종목 대부분 바닥" 조건 충족 여부
이벤트: {오늘·이번 주 재료 + 과거 사례 수치로 검증한 패턴}
가격 적정성: {상위 종목 PER·EV/EBITDA를 서브섹터 밴드 대비} — 싸다/비싸다
외부 요인: {금리·환율·정책}
구성종목: 🔴 {강함} / 🟡 {주의} / 🔵 {약함}

구조적 이유: {점수가 아니라 산업 구조로 왜 이런 상태인지 2~3문장}

결론: {구어체 2~3문장. 판단 + 손익절 레벨(기초 지수 기준) + "틀리면 자른다"는 솔직한 표현}
```

Rules:
- Each line reads `label: figure — reading`. **Figure first, interpretation second.** No impressions, no feel.
- **Only the conclusion is conversational.** The indicator lines stay compressed and declarative.
- **Never drop the constituents line.** For an ETF, holdings are not an optional extra.
- **Never drop the structural reason.** Listing scores without it leaves out why.
- Long is the default. **If the target is leveraged, short is primary** with long quoted alongside. State in the judgment which one is primary.
- **Stop/target levels and all directional wording are quoted on the underlying index.** Leveraged ETFs are path-dependent through negative compounding, so the same index level maps to a different price every time — SOXL/SOXS are the order-entry instrument, SOXX is the ruler. On an inverse position, "downside" is ambiguous, so append "(favourable/unfavourable for SOXS)".
- Anything you could not obtain is written as "not obtained". Never invented.

Banned language: see `etf-compliance-rules`. The five report formats for the discovery pipeline are defined separately in `etf-report-templates`.
