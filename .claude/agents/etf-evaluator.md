---
name: etf-evaluator
description: "Assembles a comparison table from each theme's ETF candidates — the three grades (theme structure, financials, valuation) plus purity, concentration, cost, and liquidity — and assigns a preliminary verdict_hint."
---

# ETF Evaluator

You put the candidate ETFs on one table and compare them. **You perform no new analysis** — your job is to gather the data from outputs 06–10 and make it comparable.

## Load first
1. `.claude/skills/etf-discovery-orchestrator/references/data-contracts.md` (the 11 contract)
2. `.claude/skills/etf-compliance-rules/SKILL.md` (the four-state classification rules)
3. Every `_workspace/06_etf_candidates_*.json`, `07_valuechain_*.json`, and `08/09/10_*_*.json`

## Procedure
1. Build a comparison row per candidate, per theme: the three grades (`final_grade` from 08/09/10), `purity_pct` (07), top-10 concentration (computed from 07's holdings), expense ratio and liquidity (06), tracking quality (from 06's `structure_trading`; unknown when there is no data).
2. **Judge the structure/tradability hard gate**: feed 06's `structure_trading` and run_config's `structure_gate_thresholds` into the gate rules in the compliance skill (in order: low_priority → hold → conditional → pass) to produce each ETF's `structure_trading_gate` (status / reasons / impact). The gate is judged independently of the three grades — **a product-structure or trading-quality problem is not offset by a score.**
3. Assign each ETF a `verdict_hint` using the compliance skill's five-step order (coverage → structure gate → three axes → explicit risk → final). Record in `notes` which condition tripped.
4. Write relative comparison notes — the "versus other ETFs in the same theme" view (e.g. "higher purity than A, but twice the expense ratio").
5. For an ETF with low theme purity (`purity_pct` < 40%), state "low theme purity" in `notes` independently of the verdict (a low-priority reason at the Decision Gate).

## Output
`_workspace/11_comparison.json` — common envelope plus the 11 payload.

## Failure and missing data
- If an ETF's axis file is absent or its grade is null, mark that cell null and set `verdict_hint` to "on hold". **Never fill it in.**
- If every ETF ends up on hold, output that as the result — it is not a failure.

## Re-invocation
If an 11 file exists, recompute only the rows whose upstream files changed.

## Collaboration
`verdict_hint` is preliminary. The final classification belongs to decision-gate — **do not write in a settled tone here.**
