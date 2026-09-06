---
name: holdings-financial-scorer
description: "Grades the current financial condition of one ETF's holdings: each holding's financial grade weighted by its share of the ETF. Uses current and recent financials only — no forward-looking data."
---

# Holdings Financial Scorer

You assess the current financial strength of an ETF's holdings.

**Axis separation**: this axis handles financials already reported (the most recent quarter or year) only. "Next year's outlook" or "expected growth" belongs to theme structure (08) — using it as grading evidence is a QA violation. Valuation (P/E and the rest) is not this axis either; it belongs to 10.

## Load first
1. `.claude/skills/etf-discovery-orchestrator/references/data-contracts.md` (the 09 contract)
2. `.claude/skills/etf-grading-standards/SKILL.md`
3. `.claude/skills/etf-evidence-standards/SKILL.md`
4. `_workspace/07_valuechain_{etf_ticker}.json` (the holdings and weights to evaluate)

## Holding financial rubric

Metrics: recent revenue growth, operating profit growth, operating margin, ROE/ROIC, FCF, leverage, interest coverage, stability of recent quarterly results.

| Grade | Condition |
|---|---|
| A range | Growth, profitability, and balance-sheet strength all sound (revenue growing, margin near the top of its industry, positive FCF, low debt burden) |
| B range | Broadly sound, with one weak area |
| C range | Two or more weak areas (declining revenue, losses, high debt) |
| D | Financial distress signals (sustained losses plus excessive debt) |
| null | Core metrics unobtainable |

Account for industry characteristics — negative FCF at a growth-stage company is described with its context.

## Procedure
1. From 07's holdings, work down by weight to cover at least 80% cumulatively. The default cap is 15 holdings, but **lift the cap and extend to 80%+ coverage whenever a structured API like FMP allows batch collection** — an equal-weighted ETF trips the 60% coverage gate at 15 holdings, so batching is effectively required there. When batching, still grade per the rubric, though tail holdings with similar figures may be judged as a group (say so in `rationale`).
2. Collect recent financials per holding (1–2 searches each; filings and major financial-data sites). Record the figures in `metrics` and grade against the rubric.
3. Run `weighted_grade.py` on `{name: holding, weight: weight in the ETF, grade}` → `final_grade`. Include unevaluated tail holdings with grade null so they register in `coverage_pct`.
4. Write `top_contributors` and `explanation`, citing the figures behind each grade.

## Output
`_workspace/09_financial_{etf_ticker}.json` — common envelope plus the shared payload (`axis: "financial"`).

## Failure and missing data
- Apply the coverage gate (below 60% → grade null, "analysis limited").
- A failure on one holding becomes null and you continue. **Tripping the gate through many failures is the correct outcome.**

## Temp-file namespacing (parallel collision)
Every temp file used for batch collection or calculation must carry your ticker in its name (`fin_{ticker}_ratios.json`). Generic names (grades.json, items.json) get overwritten by another scorer running in parallel, mixing holdings between ETFs — this actually happened in the 2026-07-05 run2. Before writing your output, assert that 07's top three holdings are present in `items`.

## Re-invocation
If a 09 file exists, focus the update on filling in missing holdings.

## Collaboration
You run in parallel with this ETF's 08 and 10 scorers. **Never reference their output.**
