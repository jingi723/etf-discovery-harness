# What a run costs

Two separate budgets, and they bind at different times: **model tokens** (what the agent pipeline spends) and **data API calls** (what the free tier caps).

Everything below is measured from this repository's own runs, not estimated. Where a number is extrapolated, it says so.

## The tools: API calls only

`tools/score.py`, `validate.py`, and `render.py` call no model at all. They cost API requests and nothing else.

| Command | FMP calls |
|---|---:|
| `score.py TICKER --horizon X` | **3** (2 price series, 1 ratios) |
| `score.py TICKER --holdings` | **15** (the above + holdings + 10 constituent price series) |
| `validate.py TICKER --pattern X` | **1** |
| `render.py` | **0** (reads a local payload) |

FMP's free tier is 250 requests/day at the time of writing. That is roughly **80 plain scores**, or **16 scores with holdings**, per day.

`tools/data.py` counts calls for you:

```python
import data
data.load_env()
# ... your calls ...
print(data.call_summary())   # {'by_endpoint': {'fmp:quote': 2, ...}, 'total': 5}
```

Set `ETF_API_LOG=/path/to/log.jsonl` to also append one JSON line per call, which survives across processes.

## The pipeline: model tokens

Measured on a **narrowed verification run** (2026-09-06): US only, 2 sectors, 2 themes per sector, 2 ETFs deep-scored. Model: Sonnet. Numbers come from the Agent tool's own usage report and exclude the orchestrator's own tokens.

| Phase | Agent | Runs | Mean tokens | Mean tool calls | Mean wall time |
|---|---|---:|---:|---:|---:|
| 2 | market-regime-analyst | 1 | 99,507 | 22 | 4m 55s |
| 3 | sector-scorer | 1 | 87,124 | 18 | 2m 39s |
| 4 | theme-discoverer | 2 | 111,842 | 19 | 5m 27s |
| 5 | theme-evidence-collector | 3 | 103,427 | 21 | 4m 40s |

**About 100k tokens per agent**, fairly flat across agent types — the budget instructions in each definition ("2–3 searches per item") hold them in a narrow band. Wall time is 3–6 minutes each, and fan-out stages run in parallel, so the elapsed time is set by the widest stage rather than the total.

### Extrapolating to a full run

A default full run is 5 sectors, 3 themes shortlisted per sector, 3 core themes, 3 ETFs per theme, 3 deep-scored. That is roughly:

| Stage | Agents |
|---|---:|
| Market regime, sector scoring | 2 |
| Theme discovery (per sector) | 5 |
| Evidence collection (per shortlisted theme) | 15 |
| ETF candidates (per theme) | 3 |
| Value-chain mapping (per ETF) | 9 |
| Three-axis scoring (3 per ETF) | 27 |
| Evaluator, decision gate, reports, QA, payload | 5 |
| **Total** | **~66** |

At ~100k tokens each that is **on the order of 6–7M tokens** for a full run, mostly in the fan-out. Treat this as an estimate — only the four agent types above have been measured, and the scorers may run leaner because they read files instead of searching.

### Keeping it down

- **Start with `output_scope: "pilot"`.** That is the first-run default and roughly halves the fan-out.
- **The narrowing filters are where the money is.** `evidence_shortlist_per_sector` (default 3) and `deep_score_etf_per_theme` (default 3) each multiply through the widest stages. Dropping both to 2 cuts the agent count by about a third.
- **Partial re-runs are cheap.** "Reports again" re-runs one agent, not the pipeline. The orchestrator's Phase 0 detects this.
- **The tools are free of model cost.** For a single ticker, `etf-signal-scoring` with `tools/score.py` answers in 3 API calls and one model turn — use it instead of the pipeline whenever the target is already chosen.

## Recording your own

The orchestrator writes `_workspace/agent_costs.json` as it goes, one entry per agent call with tokens, tool uses, and duration. It is a plain file — read it, diff it between runs, or drop it. This repository's measurements above come from exactly that file.
