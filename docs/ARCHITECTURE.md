# ETF Research Agent — Architecture

Version 1.4 · a design summary, not the specification.

**The source of truth is `.claude/agents/` and `.claude/skills/`.** Where this document and those disagree, they win. This file exists to explain *why* ETF Research Agent is shaped this way; the phases, contracts, and rubrics themselves live in the skills and are not repeated here in full.

## What it reproduces

An experienced ETF investor's process — market regime → favoured sectors → themes within a sector → three core themes → ETF candidates → three-axis verification → four-state classification — rebuilt as an agent pipeline. The user does not have to name a fund. And the result is not a recommendation: it hands over candidates **with the evidence and the risks, so the investor can judge**.

## Entry points and analysis depth

A named ticker goes to `etf-signal-scoring`. Discovery without a named fund starts
with a scan: phases 0–3, one candidate-finder per sector, the structure gate, and
current-state scoring. It emits judgment blocks, not the full report set.
When full evidence is requested, the shared phases continue through the stages below.

**Discovery (phases 2–7)** narrows top-down from the market regime.
Market diagnosis → sectors graded on six criteria (3–5 selected) → 10 themes per sector → shortlist (3 per sector) → an evidence pack per theme → three core themes → 3–5 ETF candidates per theme. Output: 9–15 candidate ETFs, plus the basis and the rejection reasons at every step.

**Verification (phases 8–13)** works bottom-up on those candidates.
- **Value-chain mapping** computes chain weights and theme purity from **actual holdings**, never from the fund's name.
- **Three independent axes**: theme structure (forward-looking data only), financial condition (current financials only, no forecasts), valuation (price against current earnings, with growth context).
- **The structure/tradability hard gate** judges the product itself — leverage, inverse, synthetic, option overlay, AUM, turnover, spread, premium/discount, tracking error, listing age — separately from the three axes.
- Then comparison → Decision Gate (four states) → reports → QA and compliance review.

## The design decisions worth explaining

**Why the three axes may not read each other.** A compelling theme story would otherwise quietly upgrade a stretched multiple, and the same strength would be counted twice. Axis independence is enforced by the agents never receiving each other's output, and QA checks for leakage in both directions — current financials cited in the theme-structure axis, or forward-looking language in the financial axis.

**Why the structure gate is separate from the scores.** Trading quality does not trade off against theme quality. A leveraged fund with an excellent theme is still the wrong instrument for the judgment being made, so the gate can cap a verdict no score can lift.

**Why scores come from scripts.** If the model settles the final grade by intuition, the result moves between runs and the reasoning cannot be traced. Every weighted average goes through `weighted_grade.py`; the model explains the output.

**Why coverage suspends grades instead of estimating.** Below 60% coverage the grade becomes null with "analysis limited"; 60–80% keeps the grade but drops confidence. **More "on hold" verdicts is the correct behaviour**, not a failure to be retried around.

**Why a pattern must be backtested before it is cited.** Several patterns that read convincingly on a handful of charts lost to a random-day baseline over 1,255 sessions. `tools/validate.py` is the gate; see [METHODOLOGY.md](METHODOLOGY.md) for the ones that were dropped.

**Why the renderer is a script, not an agent** (changed in v1.4). The renderer copies
research values and computes layout deterministically. This avoids new model judgment,
but display bugs can still omit or mislabel data. Mechanical HTML checks and a visual
comparison against the payload remain necessary after rendering changes. The former
HTML rendering agents were replaced by `tools/render.py`.

## Agents

Execution mode: **subagents, pipeline plus fan-out.** Strict file contracts make data
flow inspectable; web research and model judgment are not deterministic. Scorers
may not reference each other's outputs. The orchestrator mediates the QA/report loop.

| # | Agent | Definition |
|---|---|---|
| 1 | Market Regime Analyst | `.claude/agents/market-regime-analyst.md` |
| 2 | Sector Scorer | `.claude/agents/sector-scorer.md` |
| 3 | Theme Discoverer | `.claude/agents/theme-discoverer.md` |
| 4 | Theme Evidence Collector | `.claude/agents/theme-evidence-collector.md` |
| 5 | Theme Ranker | `.claude/agents/theme-ranker.md` |
| 6 | ETF Candidate Finder | `.claude/agents/etf-candidate-finder.md` |
| 7 | Value Chain Mapper | `.claude/agents/value-chain-mapper.md` |
| 8 | Theme Structure Scorer | `.claude/agents/theme-structure-scorer.md` |
| 9 | Holdings Financial Scorer | `.claude/agents/holdings-financial-scorer.md` |
| 10 | Holdings Valuation Scorer | `.claude/agents/holdings-valuation-scorer.md` |
| 11 | ETF Evaluator | `.claude/agents/etf-evaluator.md` |
| 12 | Decision Gate | `.claude/agents/decision-gate.md` |
| 13 | Report Generator | `.claude/agents/report-generator.md` |
| 14 | QA & Compliance Guard | `.claude/agents/qa-compliance-guard.md` |
| 15 | UI Payload Builder | `.claude/agents/ui-payload-builder.md` |

Rendering is done by `tools/render.py`, not by an agent.

Seven shared skills: `etf-discovery-orchestrator` (the pipeline), `etf-signal-scoring` (7 indicators × 3 horizons for a single ticker), `etf-grading-standards` (grade arithmetic + `weighted_grade.py`), `etf-evidence-standards` (sourcing standards + source priority), `etf-compliance-rules` (banned language + `check_forbidden.py` + the four states), `etf-report-templates` (report contracts), `etf-ui-render` (payload contract + rendering).

## Data contract

Fully defined in `.claude/skills/etf-discovery-orchestrator/references/data-contracts.md`. The essentials:

- **Common envelope**: every JSON output is `{artifact, as_of_date, generated_by, sources[], source_conflicts[], confidence, coverage{available, missing, impact_of_missing}, payload}`. **An output with empty `sources` is invalid.**
- **Source metadata**: each source carries eight fields, including `reliability_tier` (primary / secondary / tertiary / unsupported). Unsupported may never be used for grading.
- **File layout**: `_workspace/01_market_regime.json` through `14_qa_report.json`, numbered in dependency order.

### Source priority

Per-domain rankings live in `etf-evidence-standards/references/source-priority.md`. In short: exchanges, issuers, and filings are primary; Morningstar, ETF.com, and data vendors are secondary; general portals and news are tertiary (events and supporting context only); blogs and forums are unusable. Issuer daily holdings always win for holdings. A single news item never supports a theme-structure grade.

The agent source policy prefers structured vendor data where available, with
official filings, exchanges, and issuers taking precedence for conflicting facts.
FMP and Toss are secondary-tier sources. Web research can fill agent evidence gaps;
the scoring/backtesting CLIs call FMP directly and have no web or Toss fallback.
**Key values must never appear in repository files, logs, or output.** See [API_SETUP.md](API_SETUP.md).

**Six rules for source conflicts**: ① primary wins ② within a tier, the later as-of date wins ③ issuer daily holdings win for holdings ④ conflicting figures are recorded in `source_conflicts`, never deleted ⑤ a conflict touching a headline grade lowers its confidence ⑥ the conflict is stated in the prose, not hidden.

## Coverage handling

- **Pre-check** (phase 1): sample each data source and record reachability in `00_coverage_precheck.md`. If a core source is blocked, decide on narrowing scope before proceeding.
- **Per stage**: every agent records what it obtained, what it did not, and the impact, in the envelope's `coverage`.
- **Gate**: below 60% → grade null, "analysis limited". 60–80% → grade kept, confidence low.
- **Rollup**: report-generator gathers every stage's coverage into `data_coverage.md` and analysis.json. QA spot-checks for omissions.

## analysis.json

Twenty top-level keys (full schema in section 5 of data-contracts.md): `meta`, `market_regime`, `sector_scores`, `theme_candidates`, `theme_evidence`, `selected_themes`, `etf_candidates`, `value_chain_mapping`, `theme_structure_scores`, `financial_scores`, `valuation_scores`, `decision_gate_result`, `etf_structure_trading_gate`, `source_quality_policy`, `investment_judgment_readiness`, `investor_fit_required`, `pilot_acceptance_summary`, `data_coverage`, `explanation`, `sources`.

Upstream payloads go in unmodified so the trace to the original survives. **analysis.json is the extension point**: a WebView, an image card, or an MTS widget consumes this file and picks the keys it needs — no change to ETF Research Agent required.

## Failure handling

| Situation | Behaviour |
|---|---|
| Agent failure | Retry once. A fan-out unit is then dropped with the omission noted; a single-instance stage halts the pipeline and reports |
| Contract violation (unparseable, key missing) | One more call, stating the violation |
| Missing data | No estimating — null + missing + impact recorded, grade suspended by the coverage gate |
| Conflicting data | Never deleted — both sources carried |
| QA fails twice | Ship with the unresolved items listed |
| Zero candidates, or fewer than 3 themes | A valid result, reported as-is. **Never padded** |

## QA and compliance

Defined in `etf-compliance-rules`, with script checks. Checklists A (compliance and form), B (data integrity), and C (gates and structure) total 15 items; checklist D adds a 15-question acceptance test on pilot runs, recorded in `pilot_acceptance_summary`.

## Planned extension: Investor Fit

Today's Decision Gate answers only "can this product go on a review list", and "worth reviewing" is not a buy. Whether to actually act on it needs the user's own context, and that is a separate gate:

- Input: holding period, amount, objective, loss tolerance, experience, existing ETFs and holdings, account type, tax considerations
- Output (four states): fits my constraints / conditionally fits, small or staged / on hold / does not fit
- Placement: consumes `decision_gate_result` and `investment_judgment_readiness` from analysis.json and runs **after** the Decision Gate. `investor_fit_required: true` marks that this step is still owed.
