---
name: etf-discovery-orchestrator
description: "Orchestrator for the ETF discovery agent harness. Runs the 'sector → theme → ETF candidates → verification' pipeline to surface candidates and produce the final reports (4 in pilot scope, 5 in full), the mobile WebView UI, and one-off PDF / summary PNG / editable DOCX exports. Use this skill for any request to discover, analyse, or verify ETFs, to analyse sectors or themes, to diagnose the market regime, to compare ETF candidates, or to produce a candidate report. Also use it for follow-ups — re-running the analysis, updating it, re-running one stage only (themes again, reports again, re-verify one ETF, UI or PDF/image/Word only), improving or correcting a previous result, regenerating reports, and creating or modifying UI/HTML/WebView/PDF/PNG/DOCX output."
---

# ETF Discovery Orchestrator

Coordinates the agent pipeline that narrows candidates in the order sector → theme → ETF candidates → verification. This is not a tool for making a chosen ETF sound good; it starts from the market regime and narrows.

**Absolute rules** (they outrank every stage):
1. No buy or sell recommendations. Every final conclusion is one of `worth reviewing / conditional / on hold / low priority`.
2. Never estimate what the data does not show — when it is short, say "analysis limited / low confidence / on hold".
3. Keep score computation (scripts) separate from explanation (the model). Keep theme analysis (forward-looking) separate from holdings analysis (current financials).
4. Every result carries its as-of date, sources, and confidence.

## Execution mode: subagents (pipeline + fan-out)

Chosen because data flows between stages through a strict file contract (`references/data-contracts.md`), making this a deterministic pipeline; and because the three scoring axes are forbidden from referencing each other (axis independence), so peer-to-peer communication would actively cause rule violations. QA↔report is a generate-verify loop the orchestrator mediates. Specify `model: "opus"` on every Agent call.

## Agents

| Agent | Phase | Fan-out unit | Output (_workspace/) |
|---|---|---|---|
| market-regime-analyst | 2 | single | 01_market_regime.json |
| sector-scorer | 3 | single | 02_sector_scores.json |
| theme-discoverer | 4 | per sector | 03_themes_{sector}.json |
| theme-evidence-collector | 5 | per theme | 04_evidence_{theme}.json |
| theme-ranker | 6 | single | 05_selected_themes.json |
| etf-candidate-finder | 7 | per theme | 06_etf_candidates_{theme}.json |
| value-chain-mapper | 8 | per ETF | 07_valuechain_{etf}.json |
| theme-structure-scorer | 9 | per ETF | 08_theme_structure_{etf}.json |
| holdings-financial-scorer | 9 | per ETF | 09_financial_{etf}.json |
| holdings-valuation-scorer | 9 | per ETF | 10_valuation_{etf}.json |
| etf-evaluator | 10 | single | 11_comparison.json |
| decision-gate | 11 | single | 12_decision.json |
| report-generator | 12 | single | 13_reports/ (4 pilot / 5 full) |
| qa-compliance-guard | 13 | single | 14_qa_report.json |
| ui-payload-builder | 13.5a | single | 15_ui/ui_payload.json (+audit) |
| *(script)* `tools/render.py` | 13.5b | — | 15_ui/html/*.html |

## Workflow

### Phase 0: context check (supports follow-up work)

1. Check whether `_workspace/` exists.
2. Decide the run mode:
   - **Absent** → first run, go to Phase 1.
   - **Present + partial-change request** (e.g. "reports again", "redo the themes", "re-verify ETF X") → **partial re-run**: find the earliest phase the request touches and re-run from there downstream only. Reuse upstream output as-is. Include the existing output paths and the user's feedback in that agent's prompt.
   - **Present + new-run request** (different as-of date, new constraints) → move the existing `_workspace/` to `_workspace_{YYYYMMDD_HHMMSS}/`, then run from the start.
3. Downstream propagation on a partial re-run: if 05 changes, everything from 06 onward re-runs. The dependency graph follows the phase order in the table above.

### Phase 1: setup + data coverage pre-check

1. Write `_workspace/00_input/run_config.json` per the schema in data-contracts. When the user has not specified a scope, use the MVP defaults: `sectors_scope` = [information technology, industrials, healthcare, energy & power, communications], `max_etf_per_theme`=5, `deep_score_etf_per_theme`=3, `selected_themes_count`=3, and **`output_scope` = "pilot" on a first run** (4 outputs — `etf_candidates.md` folded into `final_etf_decision.md`), "full" afterwards. `delivery_formats` defaults to `["pdf"]`; add html for interactive browsing, png for a short shareable image, docx for later editing. Put the provisional defaults from data-contracts into `structure_gate_thresholds` (minimums for AUM, turnover, spread, premium/discount, listing age) and tune them after the MVP run. Fix the `slug_map` here.
2. **Coverage pre-check** → `_workspace/00_coverage_precheck.md`: make one sample query against each major data source (macro indicators, KR/US ETF information, holdings, financial and price data) and record whether it is reachable. If a core source is blocked, tell the user and settle whether to narrow scope (KR only, say) before continuing. This becomes the "pre-check" section of the final `data_coverage.md`.

### Phase 2: market regime
One `Agent(subagent_type: "market-regime-analyst", model: "opus")` call. State the run_config path and the output path in the prompt.

### Phase 3: sector scoring
`Agent(subagent_type: "sector-scorer", model: "opus")`, after 01 completes. Check `selected_sectors` (3–5) on completion — warn the user and continue if it is 2 or fewer.

### Phase 4: theme discovery (fan-out)
One `Agent(subagent_type: "theme-discoverer", model: "opus", run_in_background: true)` per selected sector, **all called in parallel in a single message**. State the assigned sector and the output slug in each prompt.

### Phase 4.5: shortlist for evidence collection (orchestrator does this directly)
Read the 03 files and pick the top `evidence_shortlist_per_sector` (default 3) themes per sector. Filter: impact=high first → `etf_investable=true` required → highest `data_availability`. Bonus for overlap with the priority theme list in run_config. Set `shortlisted` to true on the chosen themes and add their slugs to `slug_map`.

Deep evidence collection across all 30–50 themes is not worth the cost, so this narrows to 9–15. Rejected themes still appear in 05's `rejected` list with their reasons.

### Phase 5: evidence collection (fan-out)
One `theme-evidence-collector` per shortlisted theme, in parallel — at most 6 concurrent, split into batches beyond that.

### Phase 6: select the three core themes
One `theme-ranker` call. If fewer than three are selected, confirm the reason and proceed as-is. **Never pad the list.**

### Phase 7: ETF candidate discovery (fan-out)
One `etf-candidate-finder` per selected theme, in parallel.

### Phase 8: value-chain mapping (fan-out)
One `value-chain-mapper` per candidate ETF, in parallel (max 6 concurrent, batched). Retry a failed ETF once, then drop it from the candidate set and record that.

### Phase 8.5: shortlist for deep scoring (orchestrator does this directly)
Using `purity_pct` from the 07 files, send only the top `deep_score_etf_per_theme` (default 3) per theme to Phase 9. For type diversity, one broad-index or blended fund may be included as a comparison even if it is not top by purity. Excluded ETFs are marked "not deeply analysed" at stage 11.

### Phase 9: three-axis scoring (fan-out × 3)
For each target ETF call `theme-structure-scorer`, `holdings-financial-scorer`, and `holdings-valuation-scorer` in parallel (3 ETFs = 9 agents; max 6 concurrent, batched). **The three scorers never read each other's output.**

### Phase 10: comparison + structure/tradability hard gate
One `etf-evaluator` call, after every score file is complete (barrier). Alongside the comparison table it judges each ETF's structure/tradability hard gate (pass / conditional / hold / low_priority) — good grades on the three axes do not offset a product-structure or trading-quality problem.

### Phase 11: Decision Gate
One `decision-gate` call. Order: coverage gate → structure/tradability hard gate → three-axis grade gate → explicit risk gate → final state.

### Phase 12: report generation
One `report-generator` call → `_workspace/13_reports/`, 4 outputs (pilot) or 5 (full) per `output_scope`. `final_etf_decision.md` must contain the "What this supports deciding" section.

### Phase 13: QA and compliance (generate-verify loop)
1. Call `qa-compliance-guard`. When `output_scope=pilot`, it also runs the 15-question pilot acceptance test.
2. If `verdict=fix_required`, call `report-generator` again with the `fix_instructions`, then re-run QA. **At most 2 rounds.**
3. If it still fails after 2 rounds, put "unresolved QA items" and the list at the top of the report and proceed.

### Phase 13.5: UI and one-off report delivery (1 agent + scripts)

Runs after research QA passes. **This layer creates no new research judgment** — it is a visual presentation of upstream results. Follows the `etf-ui-render` skill.

1. **13.5a**: call `ui-payload-builder` → `_workspace/15_ui/ui_payload.json` + audit. This is the **only interpretation point**, where screen data is extracted from analysis.json, so review ends here too.
2. **13.5b**: run the render script — no agent involved.
   ```bash
   python3 tools/render.py _workspace/15_ui/ui_payload.json -o _workspace/15_ui/html/
   python3 .claude/skills/etf-ui-render/scripts/check_html.py _workspace/15_ui/html/ --payload _workspace/15_ui/ui_payload.json
   ```
   If `total_issues` is not 0, fix the payload or `tools/render.py` and re-run. The renderer copies payload values verbatim, so it cannot distort a grade or a sentence — the same payload always yields the same bytes.
3. **13.5c**: run `.claude/skills/etf-ui-render/scripts/export_report.py` per `delivery_formats`. PNG uses `discovery_index.html` as its source. If `--check` shows a required local tool is missing, do not fake the format — preserve the HTML and state the omission and its reason in the completion report.

Partial re-runs: "UI again" starts at 13.5a (reusing upstream output), "HTML only" runs 13.5b, "PDF/image only" runs 13.5c against the existing HTML.

### Phase 14: completion
1. Copy `_workspace/13_reports/` to `output/{run_date}/`, and `_workspace/15_ui/`'s ui_payload.json and html/* to `output/{run_date}/ui/`. Copy any selected PDF/PNG/DOCX to `output/{run_date}/deliverables/`.
2. Keep `_workspace/` (audit trail).
3. Report to the user: the final candidates and their states, the areas with missing data or low confidence, the QA result, the run's total agent tokens from `agent_costs.json`, and the path to the deliverable they can share. Close by inviting feedback: "Anything in the result or the workflow worth improving?"

## Record what the run costs

After each agent returns, append its usage to `_workspace/agent_costs.json` — `{phase, agent, fanout, tokens, tool_uses, duration_ms}`, taken from the Agent tool's own usage report. Report the total in the Phase 14 completion summary alongside the results.

This is the only place the cost of a run is visible: an agent cannot see its own token count, and the fan-out stages are where a run gets expensive. Measured figures live in `docs/RUN_COST.md`.

## Prompt rules for agent calls

Every call prompt must include: (1) an instruction to follow the agent's own definition file, which loads automatically; (2) the assigned target (sector/theme/ETF) and its slug; (3) absolute paths for every input file and the output file; (4) on a partial re-run, the existing output paths plus the user's feedback.

## Error handling

| Situation | Strategy |
|---|---|
| One agent fails | Retry once. On a second failure: if it is a fan-out unit (one sector/theme/ETF), drop that unit and continue, noting the omission in the report. If it is a single-instance stage (01/02/05/11/12), halt the pipeline and report to the user |
| Majority of a fan-out fails | Tell the user and confirm whether to continue |
| Output contract violated (JSON unparseable, required key missing) | Call that agent once more, stating the violation |
| Data conflict | Do not delete — record both sources and log it in data_coverage |
| QA loop exceeds 2 rounds | Ship with the unresolved items listed (Phase 13 above) |
| Many coverage gates trip | This is correct behaviour — more "on hold" verdicts is the right outcome. Do not retry in order to manufacture a grade |

## Test scenarios

### Normal path
1. User: "Find ETF candidates worth reviewing in the current market" → Phase 0 (first run) → Phase 1 (run_config + pre-check)
2. Phases 2–3: market regime → 3–5 sectors selected
3. Phases 4–6: 10 themes per sector → shortlist → evidence → 3 core themes
4. Phases 7–9: 3–5 ETFs per theme → value-chain mapping → deep three-axis scoring on 3 per theme
5. Phases 10–13: comparison + structure gate → Decision Gate → reports (4–5 by scope) → QA pass (+ pilot acceptance)
6. Expected: output in `output/{run_date}/`, 1–3 final candidates each classified into one of the four states, and `final_etf_decision.md` containing the judgment-readiness section

### Error path
1. At Phase 9, ETF X's holdings-financial-scorer returns a null grade at 40% financial-data coverage
2. The orchestrator does not retry (a tripped gate is normal) → X's financial axis is null at 11 → at 12 the rules put X on hold
3. The report states: "X: on hold, insufficient financial-data coverage. Revisit once constituent financials are obtained"

### Partial re-run path
1. User: "Just soften the tone of the final report" → Phase 0 detects `_workspace/` and classifies it as a partial change → re-run from Phase 12 (feedback passed to report-generator) → Phase 13 QA → done
