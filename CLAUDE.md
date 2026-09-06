# ETF Discovery Harness

**Goal:** surface investment-candidate ETFs in the order sector → theme → ETF candidates → verification, and produce five structured reports covering the evidence and the risks — never a buy or sell recommendation.

**Two triggers. The discriminator is whether the request names a fund.**

- **A ticker is named** — "analyse LIT", "how does SOXX look", "should I keep holding this", "compare SMH and SOXX", a daily judgment, validating a pattern → `etf-signal-scoring`. Computation happens in `tools/score.py` and `tools/validate.py`; the model only interprets. Costs a handful of API calls and one turn.
- **No ticker is named** — "find ETF candidates worth reviewing", "what looks good in this market", analysing a sector or theme, diagnosing the regime → `etf-discovery-orchestrator`, which itself has two paths. **The scan is the default**: regime → sectors → a few representative ETFs each → score, 3 agents, ending in the same judgment blocks. The full pipeline (~60 agents, millions of tokens) runs only when depth, evidence, or reports are asked for — ask first if it is unclear.

Either way the deliverable is the judgment block defined in `etf-signal-scoring` — indicator lines with their own stickers and scores, constituent stickers from scoring not from eye, then the structural reason and a colloquial conclusion. A score table is working material, not an answer.

Getting this wrong is expensive in one direction only: routing a named ticker into the discovery pipeline spends a full run starting from the whole market, and may never reach the fund that was asked about. When in doubt, and a ticker is in the request, score it.

Simple questions can be answered directly.

**Output language follows the request.** Asked in Korean, answer in Korean, using the established verdict labels (검토 가능 / 조건부 검토 / 판단 보류 / 우선순위 낮음) and judgment format from `etf-signal-scoring`.

**Branches:** `ko` is the working branch and the source of truth for day-to-day use; `main` is the published English translation, updated periodically.
