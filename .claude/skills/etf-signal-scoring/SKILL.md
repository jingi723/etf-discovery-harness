---
name: etf-signal-scoring
description: "Standard for scoring one already-chosen stock or ETF across 7 indicators × 3 time horizons. Use this skill whenever the request names a fund or stock — 'analyse LIT', 'how does SOXX look', 'is TIGER semiconductors worth holding' — and when asked what state a specific ticker is in right now, to write a daily or weekly judgment, to check an open position, to compare two tickers, to judge a leveraged ETF over days, to score constituents for a heatmap, or to validate a chart pattern statistically. The discovery pipeline (sector → theme → ETF) belongs to etf-discovery-orchestrator; this skill is for when the target is already decided."
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
- **Two funds can legitimately tie.** Say so rather than inventing an order. If every indicator reads the same, they are in the same signal state, and what separates them is usually structure — concentration, replication, purity — which this framework does not measure. Point at what would settle it instead of splitting hairs on a score.
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

## The judgment block (fixed format)

**This format is fixed, and it is the answer to any ticker request.** Do not merge or drop lines, and do not substitute the score table for it. Asked about several tickers, emit this block separately for each.

`{holding/entry}` is `holding` when the user has a position and `entry` otherwise. With no position stated, write `entry` and give levels as where the case would start and stop being true, not as a stop-loss on a position that does not exist.

It has to paste into a chat client, so **no markdown tables, headers, or blockquotes** — they break in messengers. Plain text and line breaks only.

```
{TICKER} {holding/entry} call | {date} ({market} {weekday} close)

{●} Volume:     {multiple of the 20-day average} — reading            [{score}, weight {w}%]
{●} Flows:      {put/call, investor-type net buying, ETF creations}   [{score}, weight {w}%]
{●} Chart:      {% from the 60-day high and low, support/resistance}  [{score}, weight {w}%]
{●} Momentum:   {20-day return and whether volume confirms it}        [{score}, weight {w}%]
{●} Position:   {where in the 60-day range, distance from the 200-day}[{score}, weight {w}%]
{●} Valuation:  {top holdings against the sub-sector band}            [{score}, weight {w}%]
{●} External:   {rates, FX, policy — and its sign for THIS sector}    [{score}, weight {w}%]
{●} Total:      {weighted score}/100 on the {horizon} profile

Holdings:    {top 8 by weight, one per line: today / 1wk / 20d / 60-day position / trend}
             {share of weight still in an uptrend} — does "most constituents are near a bottom" hold?
Events:      {today's and this week's catalysts + 2σ shock count over the last 20 sessions
             + any pattern validated with historical numbers}
Catalysts (dated):       {only what has a date inside the judgment window: earnings, a
             regulatory decision, a policy calendar. Write "none" when there is none —
             that line decides the call}
Catalysts (conditional): {what the structure's tension is likely to produce, with the
             arithmetic. "Inventory at N days -> an expansion or price-rise announcement is
             likely within the month". Where tension is low, say "low hazard" and give the figures}

Structural reason: {2–3 sentences on why it is in this state, from industry structure — not from
             the scores. Direction here is a quarters-and-years matter; it reaches the one-month
             call only through Catalysts (conditional) above}

Conclusion: {2–3 conversational sentences. **One of the four verdict states**, the stop and
             target levels (on the underlying index), and a plain statement of what would prove
             it wrong}
```

For a Korean request, use the Korean field labels — this is the established wording, not a fresh translation:

```
{티커} {보유/진입} 판단 | {날짜} ({시장} {요일} 종가 기준)

{●} 거래량·수급: {20일 평균 대비 배율, 투자자별 순매수, 풋/콜} — 해석   [{점수}, 가중 {w}%]
{●} 차트(추세): {20선·60선·200선 관계, 지지·저항} — 해석                 [{점수}, 가중 {w}%]
{●} 모멘텀: {20일 수익률 + 거래량 동반 여부} — 해석                      [{점수}, 가중 {w}%]
{●} 위치·바닥: {60일 레인지 내 위치, 고점 대비} — 해석                    [{점수}, 가중 {w}%]
{●} 상대강도: {벤치마크 대비 20일 초과수익} — 해석                       [{점수}, 가중 {w}%]
{●} 가격 적정성: {상위 종목 배수를 서브섹터 밴드 대비, 배수 확보 비중} — 해석  [{점수}, 가중 {w}%]
{●} 외부 요인: {금리·환율·정책 — 이 섹터에 주는 부호} — 해석              [{점수}, 가중 {w}%]
{●} 종합: {가중 점수}/100 ({시간축} 기준, 커버리지 {N}%)

구성종목: 비중 내림차순, 한 줄에 한 종목. 색은 채점 결과이지 눈이 아니다.
  비중      종목            오늘      1주      20일   60일위치   추세
  26.76%  🟠 현대건설      +2.24%   -6.31%   +12.7%     55%   상승
  23.92%  🟡 두산에너빌리티   +3.76%   -9.32%    +7.9%     49%   하락
  ...
  0.30%     원화예금

차트(구성종목): {추세 생존 비중 %} — "구성종목 대부분 바닥" 조건 충족 여부
이벤트: {오늘·이번 주 재료 + 최근 20일 2σ 충격 상방/하방 횟수 + 검증된 패턴}
촉매(확정): {판정 기간 안에 날짜가 잡힌 것만. 실적일·규제 결정·정책 일정.
        없으면 "없음"이라고 적는다 — 이게 판정을 뒤집는다}
촉매(조건부): {구조 긴장도가 낳을 것으로 보이는 이벤트 + 남은 시간 계산.
        "재고 N일 → 증산·가격인상 발표가 한 달 안에 나올 확률 높음" 형태.
        긴장도가 낮으면 "해저드 낮음"과 그 근거 수치를 적는다}

구조적 이유: {점수가 아니라 산업 구조로 왜 이런 상태인지 2~3문장.
        방향은 분기 이상 얘기이고, 1개월에는 위 촉매(조건부)로만 넘어간다}

결론: {구어체 2~3문장. 4단계 판정 중 하나를 명시 + 손익절 레벨(기초 지수 기준)
     + "틀리면 자른다"는 솔직한 표현}
```

Rules:
- Each line reads `label: figure — reading`. **Figure first, interpretation second.** No impressions, no feel.
- **Every indicator line carries its own sticker and score**, taken from `tools/score.py` output — not assigned by eye. Same for the constituents line: score each holding and let the band decide its colour. Hand-picking a sticker is the same violation as hand-picking a grade.
- Constituent stickers use all five bands, not three. Collapsing 🟠 into 🔴 or 🟢 into 🔵 loses the distinction the bands exist for.
- **Only the conclusion is conversational.** The indicator lines stay compressed and declarative.
- **Never drop the constituents line.** For an ETF, holdings are not an optional extra.
- **Never drop the structural reason.** Listing scores without it leaves out why.
- **The one-month profile is the default.** Long is quoted alongside on request, or when the two split badly; say which is primary. If the target is leveraged, short is primary. Long is not the default because macro carries 40% there — a single hand-entered number decides half the score. Changing macro from 25 to 65 on one Korean semiconductor fund moved the long score 33.1 -> 49.1 (16 points) while the one-month score moved 4.
- **Structure enters a one-month call as an event hazard, not as a direction.** Industry structure works over quarters and cannot push a price inside a month, but it does set the probability that an event lands within it. Inventory at the floor produces expansion, price-rise or allocation announcements with no calendar entry at all.

  ```
  tension = buffer / drawdown rate = time remaining
    time remaining on the order of the judgment window -> use it
    time remaining ten times the window or more        -> do not
  ```

  Memory sat under 10 days against a normal 28–42 and a broker note on no calendar moved SK Hynix +8.26% in a day — **the structure produced the event.** Lithium had a 109,000 t buffer against a 1,500–80,000 t annual deficit, so 1.4 to 70 years remained and nobody had a reason to hurry. Both are bullish structures; only one is a one-month case. **It is negative because tension was used, not because structure was excluded** — shrink the buffer to 30 days and the same structure turns the call positive.
- **Find both the numerator and the denominator of tension.** Never substitute a phrase like "the buffer is negative" or "it is already at the floor" for a timing figure. A five-year cumulative contracting shortfall of 226M lbs was read as "high hazard" on one uranium fund, while the actual buffer — EIA utility inventory — was 118M lbs, 2.5 years of cover, and **rising 3% year on year**. That mistook the direction of a shortage for its timing. With no numerator, write **"tension undetermined"** and claim no hazard.
- **For commodities the timing variable may not be inventory.** Uranium utilities contract two to five years ahead of delivery, so "who comes to market, and when" sets the timing. Establish what actually triggers an event in that market before reaching for inventory.
- **A date on the calendar is not a catalyst.** Check three things: does anything new become public that day; is its content already a known direction; and did that event historically beat the baseline (n<20 means do not cite it). A nuclear industry symposium was written in as a dated catalyst and failed all three — the biennial report was not due that year, an industry gathering says what the industry already says, and the 20-day performance after it was n=4 with a range of −21% to +23%. **Leave `Catalysts (dated)` as "none" rather than trawling a calendar to fill it.**
- **The one-month call is made on catalysts and location.** In order: (1) is there anything dated inside the window; (2) is tension high enough to produce an event without one; (3) how many 2σ shocks in the last 20 sessions; (4) which is nearer, resistance or support. One fund scored none, low, zero and support-nearer, and support breaking opened a 10.4% gap below. **Quote support and resistance as distances, with the gap beyond them** — levels alone hide the asymmetry.
- **Never use a forecast as grounds for a call.** Each time you write a reason, check it: is this something that has already happened, or something I think will happen? If the latter, convert it to a condition or drop it. A refining fund was marked low priority on "the crack will normalise", "demand destruction will widen" and "Russia will return" — all three predictions, none observations. What was observed was that margin was still climbing and the prior high had just been taken out on 2.43x volume. **Write the prediction as an observable condition instead: "if the crack drops below $60".**
- **Separate "no reason to win" from "unknown whether it lasts".** The first is low priority, the second is conditional. Using the first for the second dresses a forecast up as a verdict.
- **Write one of the four verdict states in the conclusion.** Worth reviewing / conditional / on hold / low priority. Do not substitute prose like "neither good nor bad" or "expected value near zero". Blurring the verdict is declining to make one. On hold is only for genuinely insufficient grounds; once "there is no reason to win" is established, that is low priority.
- **Stop/target levels and all directional wording are quoted on the underlying index.** Leveraged ETFs are path-dependent through negative compounding, so the same index level maps to a different price every time — SOXL/SOXS are the order-entry instrument, SOXX is the ruler. On an inverse position, "downside" is ambiguous, so append "(favourable/unfavourable for SOXS)".
- Anything you could not obtain is written as "not obtained". Never invented.

Banned language: see `etf-compliance-rules`. The five report formats for the discovery pipeline are defined separately in `etf-report-templates`.
