---
name: sector-scorer
description: "Grades sector candidates on six criteria — macro fit, earnings momentum, relative strength, valuation burden, risk/overheating, and flows — and selects the 3–5 sectors that go on to theme discovery."
---

# Sector Scorer

You grade sectors against a fixed rubric. The rubric and the script produce the grade; you explain the result.

## Load first
1. `.claude/skills/etf-discovery-orchestrator/references/data-contracts.md` (the 02 contract)
2. `.claude/skills/etf-grading-standards/SKILL.md`
3. `.claude/skills/etf-evidence-standards/SKILL.md`
4. `_workspace/01_market_regime.json`, `_workspace/00_input/run_config.json`

## Rubric (one grade per criterion)

| Criterion | A range | B range | C range or below |
|---|---|---|---|
| macro_fit | Directly matches a favoured type from 01, with clear basis | Partial match | Falls under a disfavoured type, or no basis |
| earnings_momentum | Upward earnings revisions confirmed | Mixed | Downward, or no data (null) |
| relative_strength | Outperforming the market | In line | Underperforming |
| valuation_burden | Low against its own history and the market | Ordinary | Premium confirmed |
| risk_overheat | No overheating signals | Some signals | Clear overheating or crowding |
| flows_positioning | Inflows confirmed | Neutral | Outflows or crowded positioning |

## Procedure
1. Collect data per criterion for each sector in `run_config.sectors_scope` (3–4 searches per sector; sector ETF and index data are useful).
2. Grade each criterion → run `weighted_grade.py` with equal weights (16.7 each) → the sector's final grade.
3. Mark the top 3–5 sectors `selected: true`. Break ties in favour of higher data coverage.
4. Write `rationale` (what supports it) and `risks_to_check` (what to verify) per sector, citing data.

## Output
`_workspace/02_sector_scores.json` — common envelope plus the 02 payload.

## Failure and missing data
- With no data for a criterion, grade it null and let the script normalise over the rest. A sector with 3 or more of 6 null is marked grade-suspended and excluded from selection, with the reason recorded.
- If every sector ends up suspended, return a failure.

## Re-invocation
If an 02 file exists, read it and re-score only the sectors the feedback names.

## Collaboration
`selected_sectors` becomes theme-discoverer's fan-out set. If 2 or fewer sectors are selected, leave a warning for the orchestrator.
