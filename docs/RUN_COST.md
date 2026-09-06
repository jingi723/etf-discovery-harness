# What a run costs

Two separate budgets, and they bind at different times: **model tokens** (what the agent pipeline spends) and **data API calls** (what the free tier caps).

Everything below is measured from this repository's own runs, not estimated. Where a number is extrapolated, it says so.

## The tools: API calls only

`tools/score.py`, `validate.py`, and `render.py` call no model at all. They cost API requests and nothing else.

| Command | FMP calls |
|---|---:|
| `score.py TICKER --horizon X` | **3** (2 price series, 1 ratios) |
| the same ticker across all 3 horizons | **3**, not 9 — responses are cached in-process |
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

**Responses are cached in-process for 5 minutes** (`ETF_CACHE_TTL` seconds, 0 disables). It is time-bounded on purpose — serving yesterday's close as today's is worse than spending the request — and `data.clear_cache()` forces a refresh at a session boundary or after a market close. `call_summary()` separates `total` (calls your code made) from `network_requests` (the ones that count against a rate limit).

Without it, scoring six funds across three horizons issued over 150 requests, most of them refetches of the same price series. Cached, the same scan costs 58.

## The pipeline: model tokens

Measured on a **narrowed verification run** (2026-09-06): US only, 2 sectors, 2 themes per sector, 4 ETF candidates per theme, 2 deep-scored. Model: Sonnet. 26 agents, 2.75M tokens, 140 minutes of agent time. Numbers come from the Agent tool's own usage report and exclude the orchestrator's own tokens.

| Agent | Runs | Mean tokens | Mean tool calls | Mean wall |
|---|---:|---:|---:|---:|
| holdings-valuation-scorer | 2 | 136,001 | 25 | 10m 53s |
| theme-ranker | 1 | 122,604 | 20 | 5m 38s |
| theme-discoverer | 2 | 111,842 | 19 | 5m 27s |
| holdings-financial-scorer | 2 | 108,887 | 18 | 5m 45s |
| theme-evidence-collector | 4 | 105,584 | 22 | 5m 09s |
| etf-candidate-finder | 2 | 102,591 | 24 | 4m 40s |
| value-chain-mapper | 9 | 101,789 | 13 | 5m 09s |
| market-regime-analyst | 1 | 99,507 | 22 | 4m 54s |
| theme-structure-scorer | 2 | 90,857 | 11 | 3m 07s |
| sector-scorer | 1 | 87,124 | 18 | 2m 38s |

**Every agent type lands near 100k tokens**, within a 87k–136k band. The per-agent search budgets in each definition ("2–3 searches per item") are what hold them there. Wall time is 3–11 minutes each, and fan-out stages run in parallel, so elapsed time is set by the widest stage rather than the total.

### Cost is fixed overhead, not work done

This is the single most useful thing to know before trying to optimise. Fitting the value-chain mapper's cost against how many holdings it actually classified, across nine runs from 27 to 127 holdings:

```
cost ~ 95,651 tokens fixed + 111 tokens per holding
```

**87% of even the largest map is fixed overhead** — loading skills and contracts, fetching, writing the file. A 127-holding fund costs 12% more than a 20-holding one, not five times more.

The practical consequence: *making an agent do less work barely helps.* Savings come from not invoking an agent at all.

### Extrapolating to a full run

A default full run is 5 sectors, 3 themes shortlisted per sector, 3 core themes, 3 ETFs per theme, 3 deep-scored — roughly 66 agents. At ~100k each that is **on the order of 6–7M tokens**, dominated by the fan-out. The per-agent figure is now measured across all ten agent types, so the uncertainty is in the agent count, not the unit cost.

### What the run threw away

Of this run's 2.75M tokens:

| | Agents | Tokens | Share |
|---|---:|---:|---:|
| Evidence packs for themes later rejected | 2 | 217,386 | 8% |
| Value-chain maps for ETFs not deep-scored | 4 | 446,641 | 17% |

The first is structural — a theme has to be researched before it can be rejected on its merits, and the rejection reasons in this run came directly from those packs. The second looked like waste worth removing. It was not; see below.

### Optimisations tried and rejected

**Estimating purity from a sample instead of full mapping.** Phase 8.5 filters candidates on `purity_pct` alone, so the idea was to approximate purity cheaply and full-map only the survivors. Two estimators were tested against 8 fully mapped funds:

| Estimator | Purity error | Selection preserved |
|---|---|---|
| Top 15 holdings by weight | biased high, up to 23pp | fails — the head of a theme fund is purer than its tail |
| Top 10 + 10 sampled from the tail | ≤1.8pp on all 8 funds | 83.3% over 3,780 bootstrap trials |

83.3% means one run in six deep-scores a different ETF, which changes the finalists. The failures cluster where the decision is close (57% wrong when the purity gap at the cut is under 3pp, 5.7% when it is over 12pp), so a hybrid that full-maps only near-tie candidates reaches 98–99% accuracy.

**But the hybrid saves nothing**, because of the fixed-overhead finding above: it costs 94–99% of full mapping. A cheap scan is still an agent invocation, and the selected funds get mapped twice. Rejected.

A script-based pre-filter using FMP's own industry classification would avoid the agent entirely. Untested.

### Keeping it down

- **Start with `output_scope: "pilot"`.** That is the first-run default and roughly halves the fan-out.
- **The narrowing filters are where the money is.** `evidence_shortlist_per_sector` (default 3) and `deep_score_etf_per_theme` (default 3) each multiply through the widest stages. Dropping both to 2 cuts the agent count by about a third.
- **Partial re-runs are cheap.** "Reports again" re-runs one agent, not the pipeline. The orchestrator's Phase 0 detects this.
- **The tools are free of model cost.** For a single ticker, `etf-signal-scoring` with `tools/score.py` answers in 3 API calls and one model turn — use it instead of the pipeline whenever the target is already chosen. This is the largest saving available: the pipeline answers "what should I look at", and running it against a ticker you have already chosen spends 2.7M tokens on a question you did not ask.

## Recording your own

The orchestrator writes `_workspace/agent_costs.json` as it goes, one entry per agent call with tokens, tool uses, and duration. It is a plain file — read it, diff it between runs, or drop it. This repository's measurements above come from exactly that file.
