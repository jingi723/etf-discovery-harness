---
name: etf-report-templates
description: "Templates for the ETF Research Agent's final outputs (sector_theme_discovery.md, etf_candidates.md, final_etf_decision.md, analysis.json, data_coverage.md). Use this skill whenever generating final reports, regenerating them, adjusting report format, writing the judgment-readiness section, or producing the reduced pilot output set."
---

# Report Templates

`report-generator` assembles the final outputs from the 01–12 files in `_workspace/`. **A report performs no new analysis** — writing anything not present upstream breaks the evidence trail, so every sentence must reduce to data in the upstream JSON.

Common rules:
- Every file opens with the as-of date (`run_date`), the generation date, and the disclaimer: "This material is for information only and is not a recommendation. Responsibility for any investment decision rests with the investor."
- Grades are always written as `grade (coverage %, confidence, as-of date)`.
- Nothing from the banned list in `etf-compliance-rules`.
- Write the report in the language of the user's request. In Korean, use the established verdict labels (검토 가능 / 조건부 검토 / 판단 보류 / 우선순위 낮음) from `etf-compliance-rules`.

## The scan produces no reports

A scan (the orchestrator's default path) does not generate the five files below. Its deliverable is one judgment block per fund, per `etf-signal-scoring`, ranked best first, plus one line naming what the scan did not check — theme purity, holdings-level financials, valuation beyond the sub-sector band. Writing a `final_etf_decision.md` off a scan would present three agents' worth of evidence in a format that implies sixty.

The templates below are for the full pipeline.

## Output scope (`run_config.output_scope`)

| Scope | Outputs |
|---|---|
| **pilot** (first run) | Four required: data_coverage.md, sector_theme_discovery.md, final_etf_decision.md, analysis.json. `etf_candidates.md` is not produced; its content (candidate set, type, purity, cost, liquidity) is folded into the "Candidate comparison" section of final_etf_decision.md |
| **full** (later runs) | All five — `etf_candidates.md` becomes its own file |

`analysis.json` always fills the complete schema regardless of scope; only the markdown reports shrink.

## sector_theme_discovery.md

```markdown
# Sector and Theme Discovery ({run_date})
## 1. Current market regime        ← 01 summary + indicators + key_risks
## 2. Sector scores and selection  ← 02 table (sector / grade / basis / risk) + the 3–5 selected
## 3. Theme candidates by sector   ← 03 table of 10 per sector (theme / positive / negative / ETF-investable / confidence)
## 4. The three core themes        ← 05 selected (why chosen, supporting data, missing data, risks, why over the rejected, linked ETFs, confidence, ETF investability)
## 5. Rejected themes and why      ← 05 rejected (rejection category + specific reason)
## 6. Missing data                 ← coverage.missing gathered from 01–05
```

## etf_candidates.md (a separate file in full scope only)

```markdown
# ETF Candidates ({run_date})
## Candidates by theme             ← 06 (per theme: name / code / market / issuer / type / AUM / expense ratio)
## Value-chain weights and purity  ← 07 (per ETF: chain weight table + purity_pct)
## Structure and trading           ← 06 structure_trading (listing age / structure type / spread / premium-discount / tracking quality)
## Liquidity, concentration, cost  ← 06+11 (top-10 concentration, turnover, expense ratio)
## Data confidence                 ← 06–07 confidence/coverage
```

## final_etf_decision.md

Follow this section order exactly:

```markdown
# Final ETF Verification ({run_date})
## 1. Candidate summary            ← 12 finalists (per ETF: three grades + one-line verdict)
## 2. Verdict per candidate        ← 12 status, stated alongside "worth reviewing ≠ a recommendation to buy"
## 3. Three-axis detail per candidate
### {ETF name} — {verdict}
- Theme structure: {grade} — ← 08 explanation
- Financial condition: {grade} — ← 09 explanation
- Valuation: {grade} — ← 10 explanation (with growth context alongside)
## 4. Structure/tradability gate   ← 11 structure_trading_gate (per ETF: status + reasons + impact)
## 4b. Current state                ← 12b_signal_scores.json (per ETF: long / swing / short score, constituent breadth, macro used)
     State plainly that this is timing context and does not change the verdict:
     the four states describe the product, not the moment.
## 5. Why it remained              ← 12 why_remained
## 6. Why others were excluded     ← 12 excluded
## 7. Conditions to revisit        ← 12 recheck_conditions
## 8. Alternative directions       ← 12 alternatives
   (pilot scope: add a "Candidate comparison" section here — etf_candidates.md content, compressed)
## 9. What this supports deciding  ← fixed structure below
## 10. Data limits and disclaimer  ← coverage rollup + disclaimer
```

### Section 9, "What this supports deciding" (required — its absence is a QA failure)

```markdown
## What this supports deciding

### What you can judge from this alone
- Which sectors and themes surfaced as candidates, and why this theme was chosen
- Which ETFs actually hold that theme (on a holdings basis)
- Each ETF's theme structure, financial condition, valuation, and structure/trading quality
- Each ETF's verdict (worth reviewing / conditional / on hold / low priority)

### What this cannot settle (needs your own circumstances)
- Whether it fits your holding period and loss tolerance
- Whether it overlaps ETFs and stocks you already hold
- Whether it suits your account type and tax situation
- What position size would be appropriate

### Data still to obtain
← 12 recheck_conditions + missing items from every stage (made specific to this run)

### Next actions
- Compare against other ETFs in the same theme / check overlap with your portfolio / revisit if the valuation premium eases
- Hold pending the missing data / run a fit review against your own constraints (Investor Fit — a later addition)

### Why this is not a recommendation to buy
ETF Research Agent evaluates only whether the product itself belongs on a review list. It does not incorporate the circumstances an actual decision requires — horizon, amount, loss tolerance, existing portfolio.

> This is reference material for assessing an ETF candidate's structure and risks. Whether to act on it depends on your holding period, position size, loss tolerance, and existing portfolio.
```

Use the fixed items above as the base for "what you can judge", but keep only what this particular run actually established. If every candidate came back on hold, for example, describe the three-axis comparison as correspondingly limited.

## analysis.json

Follow the schema (20 top-level keys) in section 5 of the data contract (`etf-discovery-orchestrator/references/data-contracts.md`) exactly. Assembly rules:
- Put each stage's payload under its top-level key as-is — minimise reworking so the UI conversion keeps its trace to the original
- Additional keys: `etf_structure_trading_gate` (from 11), `source_quality_policy` (sources and source_conflicts across every stage), `investment_judgment_readiness` (same content as section 9), `investor_fit_required` (always true), `pilot_acceptance_summary` (filled by QA — null at generation time)
- `data_coverage`: an array of `{stage, available, missing, impact}`
- `explanation`: per ETF, `{ticker, theme_structure_text, financial_text, valuation_text, structure_gate_text, status_text}` — display-ready prose, compliance-clean
- `sources`: every stage's sources merged and deduplicated by URL

## data_coverage.md

```markdown
# Data Coverage ({run_date})
## Pre-check result       ← 00_coverage_precheck.md
## Coverage by domain     ← table: market regime / sector / theme / ETF candidates / structure & trading / holdings / financials / prices — obtained % and gaps
## Source quality         ← primary/secondary/tertiary usage split, list of source conflicts
## Low-confidence areas   ← items at confidence=low, with reasons
## Not analysable         ← items graded null, and what that did to the verdict
```
