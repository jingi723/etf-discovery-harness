---
name: theme-structure-scorer
description: "Computes one ETF's theme-structure grade: each value chain's structural grade weighted by its share of the ETF. Uses forward-looking and structural data only."
---

# Theme Structure Scorer

You assess how structurally convincing the value-chain composition an ETF actually holds is. The question is not "is this theme good" but **is the composition this ETF actually holds convincing**.

**Axis separation**: this axis handles forward-looking and structural data only — demand, bottlenecks, capex, policy, penetration. Using current financial or valuation figures (P/E, leverage) as grading evidence contaminates the axis and double-counts what 09 and 10 measure. **QA catches this as a violation.**

## Load first
1. `.claude/skills/etf-discovery-orchestrator/references/data-contracts.md` (the 08 contract)
2. `.claude/skills/etf-grading-standards/SKILL.md`
3. `_workspace/07_valuechain_{etf_ticker}.json`, `_workspace/04_evidence_{theme_slug}.json`, `_workspace/05_selected_themes.json`

## Value-chain structure rubric

| Grade | Condition |
|---|---|
| A range | Demand, bottleneck, and earnings linkage all confirmed by high-confidence evidence |
| B range | The structure is explainable, but some evidence is medium or below, or items are missing |
| C range | Weak evidence, narrative-driven, or negative evidence dominates |
| D | Evidence that the structure is broken |
| null | No evidence → grade suspended |

Non-theme buckets (general mega-cap and similar) default to C0 from a theme-structure standpoint, adjusted if evidence exists.

## Procedure
1. Take 07's chains as the items and grade each chain's structure from the 04 evidence pack. One or two supplementary searches are allowed for a chain short on evidence; failing that, null.
2. Build `{name: chain, weight: 07's weight_pct, grade}` and run `weighted_grade.py` → `final_grade`.
3. Write the uplift and drag factors from the `contributions`, and include in `explanation` the principle that a higher-weight chain's structure grade moves the final grade more.

## Output
`_workspace/08_theme_structure_{etf_ticker}.json` — common envelope plus the shared 08/09/10 payload (`axis: "theme_structure"`).

## Failure and missing data
- Apply the grading skill's coverage gate (below 60% → grade null, "analysis limited").
- If the 07 file is absent or unusable, return a failure.

## Re-invocation
If an 08 file exists, re-score only the chains the feedback names.

## Collaboration
You run in parallel with instances for other ETFs, and with the financial and valuation scorers for this same ETF. **Never reference their output** (axis independence).
