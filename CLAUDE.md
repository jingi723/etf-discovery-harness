# ETF Discovery Harness

**Goal:** surface investment-candidate ETFs in the order sector → theme → ETF candidates → verification, and produce five structured reports covering the evidence and the risks — never a buy or sell recommendation.

**Two triggers:**
- **Discovery** — for any request to discover, analyse, or verify ETFs, analyse sectors or themes, diagnose the market regime, or produce a candidate report, use `etf-discovery-orchestrator`. The same applies to partial re-runs ("themes again", "reports again", "re-verify ETF X").
- **Scoring** — when the target is already chosen (how a specific ticker looks right now, a daily judgment, a position check, a head-to-head comparison, validating a pattern), use `etf-signal-scoring`. Computation happens in `tools/score.py` and `tools/validate.py`; the model only interprets.

Simple questions can be answered directly.

**Output language follows the request.** Asked in Korean, answer in Korean, using the established verdict labels (검토 가능 / 조건부 검토 / 판단 보류 / 우선순위 낮음) and judgment format from `etf-signal-scoring`.

**Branches:** `ko` is the working branch and the source of truth for day-to-day use; `main` is the published English translation, updated periodically.
