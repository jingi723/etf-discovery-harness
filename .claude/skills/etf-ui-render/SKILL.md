---
name: etf-ui-render
description: "Standard for turning research output (analysis.json) into mobile WebView HTML and one-off PDF/PNG/DOCX exports. Use it for the ui_payload.json contract, the constituent score map (treemap) structure, running the render script, and choosing an export format. No research judgment is created in this layer."
---

# UI and Report Delivery

This layer produces the **visual representation only**. It computes no grades, writes no verdicts, and uses no figure absent from the source.

## Two renderers

`tools/render.py` reads the full pipeline's `ui_payload.json`, which carries three
grading axes, value chains and a holdings heatmap. **A scan produces none of those**, so
it has its own renderer, `tools/render_scan.py`, reading `12b_signal_scores.json` plus
the structure gate:

```bash
python3 tools/render_scan.py _workspace/12b_signal_scores.json \
    --gate _workspace/11_structure_gate.json --meta meta.json -o _workspace/html/
```

Both are deterministic and both copy values without computing, so neither needs an agent
to review it. Everything below describes the full-pipeline layer.

## Layer structure

```
analysis.json   → [ui-payload-builder]  → ui_payload.json   (extraction — the only interpretation point)
ui_payload.json → [tools/render.py]     → html/*.html       (deterministic render — no interpretation)
html/*.html     → [export_report.py]    → pdf / png / docx  (optional)
```

analysis.json runs to hundreds of KB because it is an audit trail. A renderer reading it directly would waste context and risk reinterpreting (i.e. distorting) the source. Extraction has to happen in the payload builder alone for it to stay traceable.

## Rendering is done by a script

```bash
python3 tools/render.py _workspace/15_ui/ui_payload.json -o _workspace/15_ui/html/
python3 {this skill directory}/scripts/check_html.py _workspace/15_ui/html/ --payload _workspace/15_ui/ui_payload.json
```

**No agent hand-writes the HTML.** Two reasons:
1. A response tens of thousands of characters long loses the whole task to a dropped connection (this happened twice in the 2026-07-05 run).
2. The same payload produces the same bytes, avoiding new model judgment. Display
   bugs can still omit or mislabel values: after renderer changes, compare the
   rendered headline grades, states, and coverage with the payload and inspect the layout.

`check_html.py` mechanically checks for unresolved placeholders, banned phrases, tag balance, duplicate ids, and external resources. If it is not zero, fix the payload or `tools/render.py`.

To change the design, edit the style tokens in `tools/render.py` (`CARD`, `gcol`, `heat_col`, and so on). If the payload contract changes, change the renderer with it.

## ui_payload.json contract

Required top-level keys:

```json
{
  "meta": {"run_date": "", "as_of_date": "", "disclaimer": "", "data_dates": {"holdings": "", "price": "", "analysis_updated": ""}},
  "pages": ["discovery_index", "etf_463250", "..."],
  "discovery_index": {
    "headline": "", "market_one_liner": "",
    "selected_sectors": [{"name": "", "grade": "", "reason": ""}],
    "selected_themes": [{"name": "", "grade": "", "main_point": ""}],
    "finalists": [{"ticker": "", "name": "", "theme": "", "decision_state": "", "ratings": {}}],
    "data_warnings": [], "next_checks": []
  },
  "etf_pages": [ /* the etf_page contract below */ ],
  "compare_page": {"rows": [{"ticker": "", "name": "", "theme": "", "decision_state": "", "theme_structure": "", "financial": "", "valuation": "", "structure_gate": "", "why_remained": [], "check_points": []}]},
  "warnings": [],
  "source_trace": [{"field": "etf_pages[0].summary", "from": "analysis.json:explanation.463250.status_text"}]
}
```

Required etf_page fields:

```json
{
  "ticker": "", "name": "", "market": "", "theme": "",
  "price": null, "change": null,
  "decision_state": "conditional",
  "ratings": {"theme_structure": "", "financial": "", "valuation": ""},
  "ratings_meta": {"theme_structure": {"coverage_pct": 0, "confidence": ""}, "financial": {}, "valuation": {}},
  "summary": "one or two sentences",
  "why_conditionally_considered": ["reason for the verdict"],
  "structure_gate": {"status": "", "reasons": []},
  "theme_key_point": {"name": "", "structure_grade": "", "main_point": "", "interpretation": ""},
  "value_chain": [{"name": "", "pct": 0, "grade": "", "point": "", "risk": "", "related_holdings": []}],
  "holdings_heatmap": [{
    "name": "", "short_name": "", "ticker": null, "weight_pct": 0,
    "financial_grade": "", "valuation_grade": "",
    "value_chain": "the value chain this holding belongs to",
    "data_confidence": "high|medium|low",
    "is_analyzed": true
  }],
  "holdings_heatmap_meta": {
    "display_count": 0, "coverage_pct": 0, "top10_weight_pct": 0,
    "other_bucket_label": "Other", "other_bucket_pct": 0,
    "area_rule": "weight_pct", "color_rule": "selected_tab_grade"
  },
  "top_holdings": [{"name": "", "weight_pct": 0, "role": ""}],
  "financial_detail": {"summary": "", "uplift": [], "drag": []},
  "valuation_detail": {"summary": "", "uplift": [], "drag": []},
  "data_warnings": ["spread and tracking error not obtained, etc. — do not hide these"],
  "disclaimer": ""
}
```

`decision_state` carries the verdict in the run's own language — English (`worth reviewing` / `conditional` / `on hold` / `low priority`) or Korean (`검토 가능` / `조건부 검토` / `판단 보류` / `우선순위 낮음`). The renderer colours it from either set.

## Conversion rules (payload builder)

- Never create a figure absent from the source. Never recompute a grade. Copy grades, coverage, confidence, and verdict from analysis.json verbatim.
- Text may be shortened to fit the UI but never changed in meaning. Softening "conditional" into "worth reviewing", or the reverse, is distortion.
- Do not discard long explanations — move them into the detail/accordion fields.
- Never hide missing data, source conflicts, or low confidence — put them in `data_warnings`. Visible warnings are this product's trust mechanism.
- Fill `price`/`change` only when analysis.json has them. Otherwise null (the renderer shows "no price data").
- Record the source field of every headline sentence in `source_trace` (traceability).
- No recommendation language (follow the banned list in `etf-compliance-rules`).

### Page composition

| Page | Content |
|---|---|
| discovery_index.html | One-line market regime + selected sectors + 3 core themes + 3 finalists (verdict badge) + coverage warnings + next checks |
| etf_{ticker}.html | Header (name/code/price) → analysis summary (verdict + summary) → three-axis grade bar → reasons for the verdict → theme key point → value-chain weights (interactive selection) → constituent score map (heatmap required, structure below) → top holdings → data as-of and disclaimer |
| compare.html (optional) | The 3 candidates × (verdict / three axes / gate / why it remained / what to check), as cards — a wide table becomes cards |
| report.html | The PDF/DOCX source. One document in the order: market, sector, theme summary → candidate comparison → per-finalist verdict, three axes, gate, risks → coverage gaps, as-of dates, disclaimer. No interaction, includes print CSS (`@media print`) |

### Constituent score map — required structure (order is fixed)

The main UI of this section is the **holdings treemap**. A table alone is a failure — the heatmap must come before the table. The point of this screen is to make it visible at a glance how the grades of the largest holdings drag the ETF's overall grade, and the area × colour encoding is what does that.

1. Section title: constituent score map
2. Short caption: "Area is weight within the ETF; colour is the grade on the selected axis."
3. Tabs: [financial | valuation] — switching changes colour only (area stays weight)
4. The treemap: area = `weight_pct`, colour = the selected tab's grade (`financial_grade` / `valuation_grade`). A null grade is grey, "analysis limited". Compute the layout at render time (squarify); the tab switch swaps only colours and labels in JS
5. Selected-holding summary beneath the map: name, weight, financial grade, valuation grade (updated on tile tap/click)
6. Legend: A range favourable / B range sound / C range check needed / D–F range caution / grey analysis limited
7. Top-weight summary: "The top {N} holdings account for {top10_weight_pct}% of the fund."
8. A "show constituent detail" toggle button
9. The top-10 table (name / weight / financial / valuation) — as detail beneath the button

## Choosing an export format

- **PDF (default)**: the most reliable for reading, keeping, and sharing. Long documents split into pages and the layout stays fixed.
- **HTML**: use when the value-chain and heatmap interactions matter. Always generated, since it is the source for every other format.
- **PNG**: only for the `discovery_index.html` summary, for a quick look on a phone or in a messenger. Never render a long full report as one image — the text becomes unreadable.
- **DOCX**: only when the user needs to edit the wording or move it into a corporate template. Not a default for archiving or distribution.

Checking local tools, and exporting:

```bash
python3 {this skill directory}/scripts/export_report.py --check
python3 {this skill directory}/scripts/export_report.py report.html --format pdf --output final_report.pdf
python3 {this skill directory}/scripts/export_report.py discovery_index.html --format png --output summary.png
python3 {this skill directory}/scripts/export_report.py report.html --format docx --output final_report.docx
```

PDF and PNG use Chrome/Chromium (path overridable with `CHROME_BIN`); DOCX uses pandoc or macOS `textutil`. The script installs nothing and sends nothing over the network. If a required tool is missing, preserve the HTML as the fallback and state which format was omitted.
