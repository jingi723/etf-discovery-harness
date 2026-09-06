# ETF Discovery Harness

[English](README.md) · [한국어](README.ko.md)

[![Checks](https://github.com/jingi723/etf-discovery-harness/actions/workflows/checks.yml/badge.svg)](https://github.com/jingi723/etf-discovery-harness/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#the-tools)
[![Built for Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-d97757.svg)](https://claude.ai/code)

**Turn ETF research into evidence you can inspect.**

A Claude Code research harness with 15 agents, holdings-level grades, and Python
tools that test market patterns against a baseline. Follow the path from
**market → sector → theme → ETF → evidence, risks, and missing data**.

[Try the sample](#quick-start) · [Read a decision report](examples/final_etf_decision.md) ·
[Inspect missing data](examples/data_coverage.md) · [How it works](docs/HARNESS_DESIGN.md)

<p align="center">
  <img src="docs/images/scan-scores.png" width="100%" alt="Scan output for one ETF: a one-month score of 49.5, then each of the seven indicators with its own colour, score and weight">
</p>
<p align="center">
  <img src="docs/images/scan-holdings.png" width="100%" alt="The same fund's top holdings as a treemap, each tile sized by weight and coloured by that holding's own score, with a legend">
</p>
<p align="center">
  <sub><b>The default output.</b> Every indicator carries its own score, weight and colour;
  the constituent colours come from scoring each holding rather than from eye.<br>
  Colours follow the Korean market convention, where red is the strong end.</sub>
</p>

<p align="center">
  <img src="docs/images/holdings-heatmap.png" width="100%" alt="Constituent score map from the full pipeline: a treemap where each tile is a holding, sized by portfolio weight and coloured by its financial grade">
</p>
<p align="center">
  <sub><b>What the full pipeline adds.</b> The same map, coloured by a graded financial
  assessment of each holding instead of a price signal — Micron at 8.16% carries an A+,
  Intel at 6.17% a C−. Sixty agents rather than three. Both are real output; see
  <a href="examples/">examples/</a>.</sub>
</p>

**Inspect the holdings, not just the ticker.** Separate theme, financial, and valuation
grades make disagreements visible. Missing data stays visible in a coverage report.
Python tools use the standard library only; sample viewing needs no API key or Claude Code.

If this approach is useful, **star the repo** to keep it handy. Reproducible bug
reports and [small contributions](CONTRIBUTING.md#good-first-contributions) help it improve.

> Research notes, not investment advice. The screenshot and bundled reports are
> historical examples, not live market views.

## Quick start

### 1. Explore the sample — no API key

With Git and Python 3.9+ installed:

```bash
git clone https://github.com/jingi723/etf-discovery-harness.git
cd etf-discovery-harness
python3 -m http.server 8000 --bind 127.0.0.1 --directory examples
```

Open **http://127.0.0.1:8000/etf_SOXX.html** to explore the holdings map and grade
tables. Stop the server with `Ctrl+C`. You can also open the HTML file directly.
This is one saved detail page; the full run's navigation pages are not bundled.
The historical sample is in Korean. Prompts on `main` are English, and reports
follow your request's language; [한국어 안내](README.ko.md).

### 2. Score a ticker — FMP key required

The live scoring and backtesting CLIs require an FMP key with access to the endpoints
they call. They do not fall back to web research. See [API setup](docs/API_SETUP.md).

```bash
cp .env.example .env
# Edit .env and replace FMP_API_KEY with your key, then run:
python3 tools/score.py SOXX --horizon swing --holdings
python3 tools/validate.py SOXX --pattern ftd --horizon 10
```

No `pip install` or virtualenv is needed. To check the backtester without credentials:

```bash
python3 tools/validate.py --self-check
```

Expected output: `ok`.

### 3. Start a discovery scan — Claude Code required

Launch `claude` in the cloned repository, then paste this prompt into its session:

```text
Find US-listed ETF candidates worth reviewing in the current market.
Start with a scan and summarize each candidate's current state and data gaps.
```

The agent workflow can research official sources without vendor API keys when its
web tools are available. Claude Code needs its own setup and access; provider keys
and endpoint access are separate. Each candidate ends in **worth reviewing /
conditional / on hold / low priority**.

The scan is the default. For holdings-level evidence and the full report set, ask
to deepen the scan into a full analysis. This invokes substantially more agents;
see the [measured run costs](docs/RUN_COST.md) before choosing the depth.

## Why this exists

Most LLM stock analysis has the same two failure modes. It asserts patterns it never
tested, and it grades everything on one time horizon. This harness is built against
both:

**Patterns must survive a backtest before they may be cited.** Real casualties from
this repo's own notes:

| Claim | Verdict |
|---|---|
| "Gap down closing near the high = institutional accumulation" | 44 events over 1,255 sessions — **worse than baseline**. Dropped. |
| "Volume expansion on a decline signals reversal" | 43% vs 50% hit rate. **No discriminating power.** Dropped. |
| "Follow-Through Days mark the bottom" (O'Neil/IBD) | On SOXX: **−2.47pp vs baseline**. Textbook pattern, inverted on this ticker. |
| "A pullback past the 61.8% Fibonacci retracement is different in kind" | 100% recovery below the line, 36% above it. **Kept.** |

Run these yourself — `tools/validate.py` is the script that killed them.

**Two horizons disagreeing is information, not a bug.** The same two-day rally scored
+7.5 on the one-month profile and −3.6 on the long-term profile, because the rally
improved trend while it destroyed the entry point. A single blended score would have
hidden that. The harness reports which indicator split them.

Not ready to install? [`examples/`](examples/) holds one real run per depth — a
[scan](examples/scan/scan_result.md) (two agents, ranked funds with per-indicator
scores) and a [full run](examples/full/) (the five reports plus an interactive ETF
detail page).

## The tools

Six scripts you can run without Claude Code at all. They are the deterministic core;
the agents call the same logic and explain the output.

### `tools/score.py` — seven indicators, three horizons

```console
$ python3 tools/score.py SOXX --horizon swing

SOXX  2026-09-04  519.86 (+3.52%)
🟡 swing score 42.1/100  (95% of weight has data)

  macro        50 pt  (weight 10%) ->  5.26  🟡
  value       n/a  (weight  5%) -> excluded, renormalised
  trend        25 pt  (weight 25%) ->  6.58  🟢
  momentum     40 pt  (weight 20%) ->  8.42  🟡
  position     75 pt  (weight 20%) -> 15.79  🟠
  rs           25 pt  (weight 15%) ->  3.95  🟢
  flow         40 pt  (weight  5%) ->  2.11  🟡

  ma20 523.42 / ma60 550.72 / ma200 431.53
  20d -4.3%  rs -3.9pp  pos60 29%  from-high -20.7%  vol 0.68x
```

Every horizon scores the *same* seven indicators — macro, valuation, trend, momentum,
range position, relative strength, flows — so you can point at the one indicator that
made two horizons disagree. Only the weights change:

| Indicator | `--horizon long` | `--horizon swing` | `--horizon short` |
|---|---:|---:|---:|
| Macro | 40 | 10 | 5 |
| Valuation | 15 | 5 | 0 |
| Trend | 15 | 25 | 25 |
| Momentum | 5 | 20 | 25 |
| Range position | 15 | 20 | 20 |
| Relative strength | 5 | 15 | 15 |
| Flows | 5 | 5 | 10 |

Macro carries 40% at the long horizon because rates set the direction and the chart
only sets the entry. Valuation is worth 0 at the short horizon because multiples do
not move in a week. Leveraged ETFs default to the short profile.

`--holdings` also scores the ETF's top constituents and reports **breadth** — how many
are actually in an uptrend. An index holding up while six of its eight largest holdings
roll over is a retracement, not a bottom.

Colour bands follow the Korean market convention, where **red is positive**:
`🔴 80+ / 🟠 60–80 / 🟡 40–60 / 🟢 20–40 / 🔵 0–20`. The score is a measure of how many
conditions are met — not an expected return.

An indicator with no data is excluded and the remaining weights are renormalised, with
the coverage stated — never filled in with a neutral guess. Below 60% coverage the score
is suspended outright. (ETFs have no P/E of their own, which is why `value` reads `n/a`
above; the pipeline scores an ETF's valuation from its holdings instead.)

### `tools/validate.py` — backtest before you believe

```console
$ python3 tools/validate.py SOXX --pattern ftd --horizon 10

SOXX  2021-09-07 -> 2026-09-04  (1255 sessions)  10-day forward return

  ftd                    n=43    mean  -1.27%  median  -2.00%  win  37.2%
  baseline (any day)     n=1245  mean  +1.19%  median  +1.14%  win  56.5%

  edge -2.47pp over baseline  ->  INVERTED — it predicts the opposite of the folklore
```

Patterns: `ftd` (O'Neil follow-through day), `distribution` (IBD distribution-day
count), `fib618` (61.8% retracement break), `touch200`, `golden_cross`. Every run
prints the pattern's forward return next to the return of picking a random day. If it
does not beat the baseline, it is noise — and the script says so.

### `tools/render.py` — payload to static HTML

Turns the pipeline's `ui_payload.json` into self-contained mobile pages — a constituent
treemap sized by weight and coloured by grade, plus a single-document print version for
PDF export. Deterministic: the same payload produces byte-identical HTML.

```bash
python3 tools/render.py path/to/ui_payload.json -o ./html
```

It copies payload values verbatim and computes nothing, which is why no agent reviews
its output — a renderer that cannot invent a grade cannot misreport one. The treemap at
the top of this README came out of it; open
[`examples/etf_SOXX.html`](examples/etf_SOXX.html) to click through the whole page.

The sample run's prose is Korean and predates the English translation — see below.

### `tools/render_scan.py` — scan scores to static HTML

The full pipeline's payload carries three grading axes and value chains; a scan carries
neither, so `render.py` cannot read it. This renders the scan's own shape — indicator
rows with their bands, and a treemap coloured by each holding's score rather than by a
grade. The two images at the top of this README came out of it.

```bash
python3 tools/render_scan.py _workspace/12b_signal_scores.json \
    --gate _workspace/11_structure_gate.json -o html/
```

### `tools/data.py` — market data, two optional backends

Selected automatically by which environment variables are set. Handles gzip, 429
backoff, and disk-caches the Toss OAuth token (Toss issues **one valid token per
client**, so a fresh token silently invalidates the one another process is holding).

It also counts your API calls, because the free tier's daily cap binds long before
anything else does — `data.call_summary()` at any point, or `ETF_API_LOG=path.jsonl`
for a log that survives across processes. A plain `score.py` run costs 3 calls; with
`--holdings` it costs 15. See [docs/RUN_COST.md](docs/RUN_COST.md).

## Repository layout

```text
.
├── tools/                              # stdlib-only Python — runs without Claude Code
│   ├── data.py                         # FMP + Toss Securities providers
│   ├── score.py                        # 7 indicators × 3 horizons
│   ├── validate.py                     # pattern backtester
│   ├── render.py                       # full-pipeline payload → static HTML
│   ├── render_scan.py                  # scan scores → static HTML
│   └── check_workspace.py              # validates run output against the contract
├── .claude/
│   ├── agents/                         # 15 specialised agent definitions
│   └── skills/
│       ├── etf-discovery-orchestrator/ # main entry point, 13-phase pipeline
│       ├── etf-signal-scoring/         # the 7-indicator framework
│       ├── etf-evidence-standards/     # sourcing, tiers, source-conflict handling
│       ├── etf-grading-standards/      # grade arithmetic + scripts
│       ├── etf-compliance-rules/       # banned phrasing, four-state verdicts
│       ├── etf-report-templates/       # report contracts
│       └── etf-ui-render/              # WebView / PDF / PNG / DOCX rendering
├── examples/                           # one real run per depth
│   ├── scan/                           # the default path, English
│   └── full/                           # the ~60-agent pipeline
├── docs/
│   ├── API_SETUP.md                    # FMP and Toss setup, coverage matrix
│   ├── RUN_COST.md                     # measured tokens and API calls per run
│   ├── METHODOLOGY.md                  # how a judgment is actually produced
│   └── HARNESS_DESIGN.md               # architecture and data contracts
└── CLAUDE.md                           # trigger pointers and change log
```

**Two branches.** `main` is English — prompts, skills, docs, and tools. `ko` is the
Korean working branch this was built and used in for two months, and it stays the
day-to-day version; `main` is its published translation. Output follows the language you
ask in, so an English request produces an English report on either branch.

The scan example is English; the full-pipeline example predates the translation and is in Korean.

## Two ways in, and two depths

Which path runs is decided by one question: **does the request name a fund?**

```text
"how does SOXX look"          →  score it            3 API calls, 1 turn
"what's worth a look"         →  scan               2-4 agents
"...and I need the evidence"  →  full pipeline      ~60 agents
```

A named ticker never enters the pipeline. It goes straight to the seven-indicator
scoring above and comes back as a judgment block. Routing it into discovery would
spend a market-wide run that might never reach the fund that was asked about.

When no fund is named, discovery runs — sharing its first four phases and then
forking on depth:

```text
market regime → sector scoring
      │
      ├── scan (default) ── representative ETFs per sector → score → judgment blocks
      │
      └── full ─────────── theme discovery + two-sided evidence
                            → theme selection
                            → ETF candidate search
                            → holdings & value-chain mapping
                            → three independent axes: theme structure / financials / valuation
                            → structure & tradability hard gate
                            → four-state decision gate
                            → current-state scoring
                            → report QA → WebView + print HTML → PDF / PNG / DOCX
```

The scan answers *what is worth a look and what state is it in*. The full pipeline
answers *why, with the evidence*, and is the one that produces the five reports. A
scan can be deepened afterwards from the same workspace, so the cheap path is never
a dead end.

**What the scan misses is theme purity.** In one run, two funds that both call
themselves semiconductor ETFs turned out to hold 55% and 50% of their weight
*outside* the theme's own value chain — visible only once every holding is
classified, which is the full pipeline's job.

Every path ends in the same judgment block: one line per indicator with its own
score and colour, constituent colours from scoring rather than from eye, then the
structural reason and a plain-language conclusion.

| Stage | Agents |
|---|---|
| Market & sector (both paths) | `market-regime-analyst`, `sector-scorer` |
| Theme discovery | `theme-discoverer`, `theme-evidence-collector`, `theme-ranker` |
| ETF candidates | `etf-candidate-finder` (takes a sector on the scan, a theme on the full path), `value-chain-mapper` |
| Independent grading | `theme-structure-scorer`, `holdings-financial-scorer`, `holdings-valuation-scorer` |
| Decision & reporting | `etf-evaluator`, `decision-gate`, `report-generator`, `qa-compliance-guard` |
| Rendering | `ui-payload-builder`, then `tools/render.py` (a script, not an agent) |

The three grading axes are deliberately forbidden from reading each other. A great
theme story must not quietly upgrade a stretched multiple.

Details: [docs/HARNESS_DESIGN.md](docs/HARNESS_DESIGN.md). What it costs to run:
[docs/RUN_COST.md](docs/RUN_COST.md) — measured across all ten agent types, plus the
optimisations that were tried and did not work.

## Design principles

- **Scores come from scripts, explanations come from the model.** If the model picks
  the final grade by intuition, the result moves between runs and the reasoning cannot
  be traced.
- **Missing data is recorded, never estimated.** Coverage below 60% suspends the grade
  outright.
- **Negative evidence is mandatory.** An evidence pack with zero negative findings is
  marked incomplete, not clean.
- **Conflicting sources are both kept**, along with the reason one was used.
- **Levels are quoted on the underlying index, never the leveraged vehicle.** Path
  dependency means the same index level maps to a different SOXL price every time.
- **"Worth reviewing" is not a buy.** Position sizing, holding period and loss
  tolerance are a separate step this harness does not perform.

## Requirements

- Python 3.9+ (standard library only)
- [Claude Code](https://claude.ai/code) — for the agent pipeline, not for the tools
- An [FMP](https://financialmodelingprep.com/) key for live CLI scoring/backtesting;
  optional for the agent research workflow — see [docs/API_SETUP.md](docs/API_SETUP.md)
- Optional: Chrome/Chromium for PDF and PNG export, pandoc or `textutil` for DOCX

Without a vendor API key, the agent workflow can use official issuer, exchange and
filing sources through its web tools. The live Python CLIs require FMP access;
the bundled sample and backtester self-check work offline.

## Contributing

Pattern contributions are especially welcome — but a new pattern needs a
`tools/validate.py` run showing it beats baseline. Open PRs against `main`. See
[CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Acknowledgements

Repository structure and documentation layout follow
[revfactory/webtoon-harness](https://github.com/revfactory/webtoon-harness).

## License

[MIT](LICENSE)
