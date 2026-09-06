# Sample output

One example per depth, both from real runs. **The numbers are historical** — correct on
their as-of dates and not a current view of anything.

## `scan/` — the default path (2026-09-06, English)

What you get from "what's worth a look in this market". Two agents and a script:
167k tokens, 58 network requests, six funds across two sectors.

| File | What it is |
|---|---|
| `scan_result.md` | The deliverable — ranked funds, per-indicator scores, what the scan did not check |
| `06_etf_candidates_*.json` | Representative funds per sector, with the structure/tradability fields |
| `11_structure_gate.json` | Gate verdicts and why none reached `pass` |
| `12b_signal_scores.json` | Raw scores, three horizons, plus constituent scores |
| `02_sector_scores.json` | The sector grades the scan started from |
| `html/` | The same result as pages — open any `scan_*.html` in a browser, they are self-contained |

Worth reading for two things it demonstrates: the macro input differing by sector under
one regime (energy 62, utilities 30, tech 15, semis 12), and two funds tying on every
indicator — reported as a tie rather than split by an invented tiebreak.

## `full/` — the deep path (2026-07-05, Korean)

What the ~60-agent pipeline produces. This run predates the harness's English
translation, so its prose is Korean; it is kept because it is a real result rather than
a reconstruction. The Korean harness lives on the `ko` branch.

| File | What it is |
|---|---|
| `sector_theme_discovery.md` | Regime read, sector scores, themes kept and cut |
| `etf_candidates.md` | Candidates per theme with AUM, fees, index, structure |
| `final_etf_decision.md` | Three grading axes, structure gate, four-state verdict |
| `data_coverage.md` | What the run failed to obtain, per field |
| `etf_SOXX.html` | One ETF detail page — open it in a browser, it is self-contained |

The full run also writes `analysis.json` (1.5 MB, every intermediate grade with its
sources) and the `_workspace/` audit trail; both are omitted here for size.

## The difference, concretely

The scan ranks XLE and XOP identically because every indicator agrees. The full
pipeline is what would separate them — its value-chain mapping found, on the same day,
that two funds calling themselves semiconductor ETFs held 55% and 50% of their weight
outside the theme they are named for.
