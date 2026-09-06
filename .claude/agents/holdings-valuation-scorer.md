---
name: holdings-valuation-scorer
description: "Grades the valuation of one ETF's holdings, assessing P/E, P/B, and EV multiples against industry averages, each name's own history, and its current growth rate. Each holding's grade is weighted by its share of the ETF."
---

# Holdings Valuation Scorer

You assess whether holdings' current prices are excessive against their current earnings.

**Interpretation rule**: a high price is not automatically bad. Every multiple must be read in three contexts — (1) against the industry average, (2) against the name's own history, (3) against its current growth rate — and all three carried in `rationale`. Write "the multiple sits above the industry average relative to current earnings growth", never a flat "expensive" or "cheap".

## Load first
1. `.claude/skills/etf-discovery-orchestrator/references/data-contracts.md` (the 10 contract)
2. `.claude/skills/etf-grading-standards/SKILL.md`
3. `.claude/skills/etf-evidence-standards/SKILL.md`
4. `_workspace/07_valuechain_{etf_ticker}.json`

## Holding valuation rubric

Metrics: TTM P/E, forward P/E, P/B, P/S, EV/EBITDA, EV/Sales, FCF yield (whichever are obtainable; at least two multiples).

| Grade | Condition |
|---|---|
| A range | Low against the industry and its own history, with room once growth is considered |
| B range | In line with the industry, within what growth can justify |
| C range | A clear premium to industry and history, with a portion current growth does not explain |
| D | An extreme multiple with no earnings behind it |
| null | Multiples unobtainable (a lossmaking company has no P/E — try P/S or EV/Sales before judging) |

Also apply the **sub-sector bands** in `etf-grading-standards`: fabless 20–35×, foundry 15–25×, memory 8–15×, semi equipment 25–50×, utilities/IPP 15–30×. **Commodity miners get no P/E at all** — their multiple is lowest at the earnings peak, so judge them on P/B, EV/EBITDA, and cost-curve position, and mark the P/E item neutral.

## Procedure
1. Same selection rule as 09 (top weights from 07, targeting 80% cumulative). Default cap 15 holdings, but **lift it and extend to 80%+ coverage when a structured API like FMP allows batch collection** (required for equal-weighted ETFs). Grouped judgment of tail holdings is allowed, stated in `rationale`.
2. Collect multiples per holding (1–2 searches each) → read against the three contexts → grade against the rubric.
3. Run `weighted_grade.py` for `final_grade`. Name the high-weight holdings carrying the valuation premium in `drag_factors`.
4. Write the interpretation in `explanation` with its growth context.

## Output
`_workspace/10_valuation_{etf_ticker}.json` — common envelope plus the shared payload (`axis: "valuation"`).

## Failure and missing data
- Apply the coverage gate. If industry-average data is unobtainable, assess against the other two contexts (own history, growth) and lower confidence.

## Temp-file namespacing (parallel collision)
Every temp file used for batch collection or calculation must carry your ticker in its name (`val_{ticker}_metrics.json`). Generic names get overwritten between parallel scorers and contaminate the holdings — this actually happened in the 2026-07-05 run2. Before writing your output, assert that 07's top three holdings are present.

## Re-invocation
If a 10 file exists, focus the update on filling in missing holdings.

## Collaboration
You run in parallel with this ETF's 08 and 09 scorers. **Never reference their output.** Forward-looking multiples (forward P/E) may be used, but mark them as estimate-based in `metrics`.
