# ETF Research Agent — Data Contracts

The output contract every agent obeys. Each agent must read the section covering its own input and output and follow it exactly.

## Contents
1. [Common envelope](#1-common-envelope)
2. [Grade and confidence standard](#2-grade-and-confidence-standard)
3. [Workspace layout](#3-workspace-layout)
4. [Payload contract per stage](#4-payload-contract-per-stage)
5. [analysis.json final schema](#5-analysisjson-final-schema)

---

## 1. Common envelope

Every numbered agent research artifact is wrapped in this envelope. Only `payload`
differs by stage. Run settings, `agent_costs.json`, `12b_signal_scores.json`, the
assembled `analysis.json`, and UI payloads use their own contracts below.

```json
{
  "artifact": "market_regime",
  "as_of_date": "YYYY-MM-DD",
  "generated_by": "market-regime-analyst",
  "sources": [
    {"source_name": "source name", "source_type": "exchange|issuer|filing|gov|vendor|research|media|other",
     "url_or_reference": "URL or 'internal calculation'", "as_of_date": "YYYY-MM-DD", "retrieved_at": "YYYY-MM-DD",
     "reliability_tier": "primary|secondary|tertiary|unsupported",
     "used_for": "what this source was used for", "notes": ""}
  ],
  "source_conflicts": [
    {"field": "the conflicting field", "values": [{"value": "...", "source_idx": 0}, {"value": "...", "source_idx": 1}],
     "resolution": "the value adopted and why (primary source wins / most recent as-of wins)"}
  ],
  "confidence": "high|medium|low",
  "coverage": {
    "available": ["data items obtained"],
    "missing": ["data items not obtained"],
    "impact_of_missing": "one or two sentences on what the gap does to the verdict"
  },
  "payload": {}
}
```

Rules:
- An output with an empty `sources` is invalid. Anything taken from the web records its URL and access date.
- Judge `reliability_tier` and per-domain source priority by the etf-evidence-standards skill (and `references/source-priority.md`). `unsupported` may never be used for grading.
- Never delete a source conflict — record it in `source_conflicts` (empty array when there is none).
- Leave anything without data as `null` and record it in `coverage.missing`. Never invent a value.

## 2. Grade and confidence standard

- Grade scale: `A+ A0 A- B+ B0 B- C+ C0 C- D` (10 levels). Numeric mapping A+=10 … D=1.
- Weighted-average grades must be computed with `scripts/weighted_grade.py` from the etf-grading-standards skill. **No mental arithmetic.**
- Below 60% coverage, use `null` instead of a grade, plus `"grade_note": "analysis limited — insufficient coverage"`.
- Source reliability has four tiers (`primary`/`secondary`/`tertiary`/`unsupported`) per the source-priority policy in etf-evidence-standards. Tertiary cannot stand alone; unsupported may not be used at all.
- A claim's `confidence` (high/medium/low) weighs source tier, source count, and how unambiguous the data is — a separate field from the tier itself.

## 3. Workspace layout

Base directory: `{project root}/_workspace/`

```
_workspace/
├── 00_input/run_config.json          # run settings (written by the orchestrator)
├── 00_coverage_precheck.md           # data coverage pre-check
├── 01_market_regime.json
├── 02_sector_scores.json
├── 03_themes_{sector_slug}.json      # one per sector
├── 04_evidence_{theme_slug}.json     # one per theme
├── 05_selected_themes.json
├── 06_etf_candidates_{theme_slug}.json
├── 07_valuechain_{etf_ticker}.json
├── 08_theme_structure_{etf_ticker}.json
├── 09_financial_{etf_ticker}.json
├── 10_valuation_{etf_ticker}.json
├── 11_comparison.json
├── 12_decision.json
├── 12b_signal_scores.json            # script results, no common envelope
├── agent_costs.json                 # agent usage log, no common envelope
├── 13_reports/                       # draft final outputs (4 pilot / 5 full)
├── 14_qa_report.json
├── 15_ui/                            # UI conversion layer
│   ├── ui_payload.json               # lightweight screen JSON (contract: etf-ui-render skill)
│   ├── ui_payload_audit.md
│   └── html/                         # discovery_index·etf_{ticker}·compare·report.html
└── 16_ui_render_qa.json              # saved check_html.py output
```

The UI layer's detailed contract (required ui_payload fields, rendering rules, mechanical checks) lives in `.claude/skills/etf-ui-render/SKILL.md`. Final copy location: `output/{run_date}/ui/`.

Slug rule: short lowercase ASCII slugs (`AI semiconductors` → `ai-semi`, `information technology` → `it`). The orchestrator records the mapping in run_config.json and every agent follows it.

### run_config.json

```json
{
  "run_date": "YYYY-MM-DD",
  "market_scope": ["KR", "US"],
  "sectors_scope": ["information technology", "industrials", "healthcare", "energy & power", "communications"],
  "max_themes_per_sector": 10,
  "evidence_shortlist_per_sector": 3,
  "selected_themes_count": 3,
  "max_etf_per_theme": 5,
  "deep_score_etf_per_theme": 3,
  "output_scope": "scan|pilot|full",
  "delivery_formats": ["pdf"],
  "structure_gate_thresholds": {
    "min_aum": {"KR": "KRW 50B", "US": "USD 100M"},
    "min_avg_trading_value": {"KR": "KRW 500M/day", "US": "USD 5M/day"},
    "max_spread_pct": 0.3,
    "max_abs_premium_discount_pct": 1.0,
    "min_listing_months": 6,
    "note": "provisional defaults — tune after the MVP run"
  },
  "slug_map": {"information technology": "it", "AI semiconductors": "ai-semi"}
}
```

`output_scope`: `scan` runs phases 0–3, S, 11.5, and S-end, producing judgment blocks
and workspace artifacts without reports or UI exports. Its 06 files use sector
slugs and contain `theme: null` plus `sector`; theme/deep-score settings do not apply.
`pilot` reduces the final outputs to four (data_coverage, sector_theme_discovery,
final_etf_decision, analysis.json) and folds etf_candidates.md into
final_etf_decision.md's candidate-comparison section. `full` produces all five.

`delivery_formats`: defaults to `["pdf"]`. PDF is the one-off report for reading and sharing, HTML is for interactive browsing, PNG is for sharing the `discovery_index` summary, and DOCX is only for when the user asks to edit the wording. HTML is generated regardless, since it is the source for the others. If an export tool is missing, preserve the HTML and state the omitted format and its requirement in the completion report.

## 4. Payload contract per stage

### 01_market_regime.json — payload

```json
{
  "summary": "3-5 sentences on the market regime",
  "indicators": {
    "rates": {"value": "...", "trend": "up|down|flat", "source_idx": 0},
    "fx": {}, "inflation": {}, "commodities": {}, "equity_indices": {},
    "risk_appetite": {}, "monetary_policy": {}, "policy_events": {},
    "sector_earnings_outlook": {}
  },
  "favorable_sector_types": [{"type": "information technology", "why": "..."}],
  "unfavorable_sector_types": [{"type": "...", "why": "..."}],
  "key_risks": ["..."]
}
```

### 02_sector_scores.json — payload

```json
{
  "sectors": [{
    "name": "information technology",
    "criteria": {
      "macro_fit": "B+", "earnings_momentum": "A-", "relative_strength": "B0",
      "valuation_burden": "C+", "risk_overheat": "B-", "flows_positioning": "B0"
    },
    "grade": "B+",
    "rationale": ["2-4 supporting points"],
    "risks_to_check": ["1-3 risks to verify"],
    "selected": true
  }],
  "selected_sectors": ["information technology", "industrials", "energy & power"]
}
```

`grade` is the equal-weighted average of the six criteria, computed with weighted_grade.py.

### 03_themes_{sector}.json — payload

```json
{
  "sector": "information technology",
  "themes": [{
    "name": "AI semiconductors",
    "positive": ["..."], "negative": ["..."],
    "value_chain": ["design", "foundry", "HBM", "equipment"],
    "key_metrics": ["candidate metrics to verify"],
    "data_availability": "high|medium|low",
    "etf_investable": true,
    "example_etfs": ["ticker or name"],
    "explainability": "high|medium|low",
    "impact": "high|medium|low",
    "confidence": "high|medium|low",
    "shortlisted": false
  }]
}
```

At least 10 themes per sector. `shortlisted` is set by the orchestrator after its filter.

### 04_evidence_{theme}.json — payload

```json
{
  "theme": "AI semiconductors",
  "checklist": ["the questions this theme has to answer — written before any data is collected"],
  "evidence": [{
    "claim": "one sentence of established fact",
    "data": "the specific figure or detail",
    "direction": "positive|negative",
    "source_idx": 0,
    "as_of": "YYYY-MM-DD",
    "confidence": "high|medium|low"
  }],
  "missing": ["data items not obtained"]
}
```

### 05_selected_themes.json — payload

```json
{
  "selected": [{
    "theme": "AI semiconductors",
    "reason": "why it was selected — name the supporting data",
    "vs_rejected": "why it ranks above the rejected themes",
    "main_point": "the single main point",
    "sub_points": ["supporting points"],
    "risks": ["risk points"],
    "etf_keywords": ["keywords for ETF search"],
    "value_chain": ["..."],
    "missing_data": ["data still missing"],
    "data_confidence": "high|medium|low",
    "etf_investability": "high|medium|low",
    "min_conditions_met": ["which minimum selection conditions were met (2 or more of 8)"]
  }],
  "rejected": [{
    "theme": "...",
    "reason_type": "insufficient data|too few ETF candidates|valuation premium too high|weak link to earnings|demand or bottleneck structure unclear|excessive risk|hard to explain|theme too broad or vague|no ETF holds the theme purely",
    "reason": "the specific reason, 1-2 sentences"
  }]
}
```

### 06_etf_candidates_{theme}.json — payload

```json
{
  "theme": "AI semiconductors",
  "candidates": [{
    "name": "ETF name", "ticker": "code", "market": "KRX|NYSE|NASDAQ",
    "issuer": "issuer", "index": "tracked index", "style": "passive|active",
    "holdings_count": 30, "aum": "string including its unit", "avg_volume": "...",
    "expense_ratio": "0.45%",
    "type": "pure theme|blended value chain|mega-cap led|broad index|highly diversified|active",
    "structure_trading": {
      "listing_date": "YYYY-MM-DD",
      "leverage_inverse": false,
      "single_stock_leverage": false,
      "synthetic_swap": false,
      "option_strategy": false,
      "currency_hedged": null,
      "spread_pct": null,
      "premium_discount_pct": null,
      "tracking_error": null,
      "tracking_difference": null,
      "real_cost_notes": "costs beyond the headline expense ratio worth checking",
      "lp_quality": null,
      "holdings_transparency": "daily|periodic|opaque"
    }
  }]
}
```

`structure_trading` is the input to the structure/tradability hard gate. Anything unverifiable goes to null and into `missing` — but the structural booleans must be confirmed from the prospectus or product page. **Never leave leverage or synthetic status as null.**

### 07_valuechain_{etf}.json — payload

```json
{
  "etf": {"name": "...", "ticker": "..."},
  "theme": "AI semiconductors",
  "chains": [{
    "chain": "AI semis & equipment", "weight_pct": 35.0,
    "holdings": [{"name": "holding", "weight_pct": 8.2, "role": "what this holding does in the chain"}]
  }],
  "unclassified_pct": 5.0,
  "purity_pct": 62.0,
  "holdings_coverage_pct": 95.0
}
```

`purity_pct` = the summed weight sitting in the theme's core value chains. Classify on actual holdings, never on the ETF's name.

### 08/09/10 score files — shared payload shape

```json
{
  "etf": {"name": "...", "ticker": "..."},
  "axis": "theme_structure|financial|valuation",
  "items": [{
    "name": "value chain or holding name", "weight_pct": 35.0,
    "grade": "A-", "rationale": "1-2 sentences citing the data behind the grade",
    "metrics": {}
  }],
  "final_grade": "B+",
  "final_numeric": 7.2,
  "coverage_pct": 88.0,
  "uplift_factors": ["what lifted the grade"],
  "drag_factors": ["what dragged it down"],
  "explanation": "the final grade explained, citing the weighted_grade.py output"
}
```

- 08 (theme structure): items = value chains, metrics = forward-looking and structural data. Reuse 07's `weight_pct` as-is.
- 09 (financial condition): items = top holdings (aim to cover 80%+ of weight), metrics = revenue growth, operating margin, ROE, FCF, leverage — **current and recent data only**.
- 10 (valuation): items = top holdings, metrics = P/E (TTM and forward), P/B, EV/EBITDA, FCF yield, each against the sub-sector band and the name's own history. Carry the growth context in `rationale`.

### 11_comparison.json — payload

```json
{
  "themes": [{
    "theme": "AI semiconductors",
    "table": [{
      "etf": "ticker",
      "theme_structure": "A-", "financial": "B+", "valuation": "C-",
      "purity_pct": 62.0, "top10_concentration_pct": 58.0,
      "expense_ratio": "0.45%", "liquidity": "high|medium|low",
      "tracking_quality": "high|medium|low|unknown",
      "structure_trading_gate": {
        "status": "pass|conditional|hold|low_priority",
        "reasons": ["why the gate returned this — which checks tripped"],
        "impact": "one sentence on what this does to the Decision Gate"
      },
      "verdict_hint": "conditional",
      "notes": ["comparison notes"]
    }]
  }]
}
```

Korean equivalents for `structure_trading_gate.status`: pass = 구조·거래 문제 없음, conditional = 조건부 확인 필요, hold = 판단 보류, low_priority = 우선순위 낮음.

### 12_decision.json — payload

```json
{
  "finalists": [{
    "etf": {"name": "...", "ticker": "...", "theme": "..."},
    "status": "worth reviewing|conditional|on hold|low priority",
    "axes": {"theme_structure": "A-", "financial": "B+", "valuation": "C-"},
    "structure_trading_gate": {"status": "pass|conditional|hold|low_priority", "reasons": []},
    "gate_trace": "one sentence naming which of the five gates decided this",
    "why_remained": ["why it remained"],
    "check_points": ["what to verify"],
    "recheck_conditions": ["conditions for revisiting"],
    "alternatives": ["alternatives worth comparing"]
  }],
  "excluded": [{"etf": "...", "why": "why it was excluded"}]
}
```

### 14_qa_report.json — payload

```json
{
  "forbidden_phrase_hits": [{"file": "...", "line": 0, "phrase": "..."}],
  "structural_checks": [{"check": "...", "passed": true, "evidence": "..."}],
  "data_integrity_checks": [{"check": "...", "passed": true, "evidence": "..."}],
  "gate_checks": [{"check": "structure gate applied, gate order respected, etc.", "passed": true, "evidence": "..."}],
  "pilot_acceptance": {"passed": [], "failed": [], "needs_revision": []},
  "verdict": "pass|fix_required",
  "fix_instructions": ["corrections to pass back to report-generator"]
}
```

`pilot_acceptance` holds the 15-question acceptance-test result when `output_scope=pilot` (null on a full run).

## 5. analysis.json final schema

`report-generator` assembles the 01–12 outputs. All 20 top-level keys are required, `meta` included:

```json
{
  "meta": {"run_date": "", "as_of_date": "", "harness_version": "1.1", "output_scope": "pilot|full", "disclaimer": "This material is for information only and is not a recommendation."},
  "market_regime": {},          // 01 payload
  "sector_scores": {},          // 02 payload
  "theme_candidates": [],       // array of 03 payloads (one per sector)
  "theme_evidence": [],         // array of 04 payloads
  "selected_themes": {},        // 05 payload
  "etf_candidates": [],         // array of 06 payloads
  "value_chain_mapping": [],    // array of 07 payloads
  "theme_structure_scores": [], // array of 08 payloads
  "financial_scores": [],       // array of 09 payloads
  "valuation_scores": [],       // array of 10 payloads
  "decision_gate_result": {},   // 12 payload
  "etf_structure_trading_gate": [],      // per-ETF gate result (structure_trading_gate from 11)
  "source_quality_policy": {},           // source quality summary
  "investment_judgment_readiness": {},   // what this supports deciding
  "investor_fit_required": true,         // always true — Investor Fit is a later addition
  "pilot_acceptance_summary": {},        // pilot checklist result (written by QA; may be null on a full run)
  "data_coverage": {},          // coverage rolled up from every stage
  "explanation": {},            // per-ETF display prose for the UI
  "sources": []                 // sources merged from every stage, deduplicated
}
```

### Added keys in detail

```json
"etf_structure_trading_gate": [{
  "etf": "ticker",
  "status": "pass|conditional|hold|low_priority",
  "checks": {"aum": {}, "trading_value": {}, "spread": {}, "premium_discount": {},
             "tracking_error": {}, "expense": {}, "structure": {}, "listing_period": {}},
  "reasons": [],
  "impact_on_decision_gate": ""
}],
"source_quality_policy": {
  "primary_sources_used": [],
  "secondary_sources_used": [],
  "tertiary_sources_used": [],
  "source_conflicts": [],       // source_conflicts from every stage
  "unsupported_claims": []      // claims dropped for resting on unsupported sources (should be empty; kept for audit)
},
"investment_judgment_readiness": {
  "can_decide_from_this_analysis": ["what this alone supports deciding"],
  "cannot_decide_without_user_context": ["what cannot be settled without the user's own circumstances"],
  "next_actions": ["what the user can do next"],
  "requires_investor_fit_check": true,
  "disclaimer": "This is reference material for assessing an ETF candidate's structure and risks. Whether to act on it depends on your holding period, position size, loss tolerance, and existing portfolio."
},
"pilot_acceptance_summary": {
  "passed": [], "failed": [], "needs_revision": []
}
```
