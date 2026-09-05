# Sample output

A real run from **2026-07-05**, US-listed ETFs only, kept as a snapshot so you can see
what the pipeline produces before installing anything.

**These numbers are historical.** They were correct on their as-of dates and are not a
current view of anything.

| File | What it is |
|---|---|
| `sector_theme_discovery.md` | Market regime read, sector scores, the themes that survived and why the others were cut |
| `etf_candidates.md` | Candidate ETFs per theme with AUM, expense ratio, index, structure |
| `final_etf_decision.md` | Three grading axes, structure/tradability gate, four-state verdict, and the "can this actually be acted on" section |
| `data_coverage.md` | What the run failed to obtain, per field — the part most tools omit |
| `etf_SOXX.html` | One ETF detail page: constituent treemap sized by weight and coloured by grade, with the tables underneath |

Open the HTML file directly in a browser — it is self-contained.

The full run also writes `analysis.json` (1.5 MB, every intermediate grade with its
sources) and the `_workspace/` audit trail. Both are omitted here for size.

Reports are in Korean, matching the agent prompts. See the repository
[README](../README.md) for why.
