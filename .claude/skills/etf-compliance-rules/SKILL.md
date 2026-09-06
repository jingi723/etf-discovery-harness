---
name: etf-compliance-rules
description: "Compliance rules for every ETF analysis output. Use this skill whenever generating or reviewing a report, JSON payload, or explanation. Triggers on: checking for recommendation language, preventing buy/sell advice, the ETF structure and tradability hard gate, classifying into the four verdict states (worth reviewing / conditional / on hold / low priority), the QA checklist, and the pilot acceptance test."
---

# ETF Compliance Rules

This is an information tool, not an advisory tool. Recommendation language is both a legal exposure and a violation of the product's premise, so any output still carrying it cannot ship. The Decision Gate here answers one question only — *is this product something a person could put on a review list* — and judgment against a specific investor's circumstances (Investor Fit) is a separate stage.

## Banned language

None of the following may appear in any output (md, json, html). Check with the script, not by eye:

```bash
python3 {this skill directory}/scripts/check_forbidden.py <file or directory>
```

Banned list (keep in sync with the script): buy this, you should buy, you should sell, we recommend, our recommendation, recommended stock, recommended pick, buying opportunity, strong buy, must-buy, time to buy, guaranteed return, guaranteed profit, risk-free, can't lose, will go up, will rise, poised to rally, set to surge, don't miss, act now, price target, buy the dip.

The script also carries the Korean list, so a Korean-language run is caught by the same pass.

## Say this instead

| Tempting | Write |
|---|---|
| I recommend this ETF | This is a candidate worth reviewing |
| It's likely to go up | This theme shows the following structure |
| Pricey but worth buying | Conditional — the valuation premium needs checking |
| Hard to say | On hold — revisit once {missing data} is obtained |
| It's no good | Low priority — {weak axis} confirmed |
| You can buy it now | Whether to act on this requires a separate review against your own horizon, position size, and loss tolerance |

## ETF structure and tradability hard gate

Strong grades on all three axes cannot rescue a product whose structure or trading quality makes it unsuitable. Judge this gate **before** the Decision Gate, for every ETF. Numeric thresholds come from `structure_gate_thresholds` in run_config (defaults are provisional — tune after an MVP run).

Fourteen checks: AUM, average daily turnover, bid-ask spread, premium/discount to NAV, tracking error, tracking difference, expense ratio and all-in cost, time since listing, leveraged/inverse, single-stock leverage, synthetic/swap/derivative structure, covered-call or option overlay, market-maker quality (where observable), and currency hedging or FX exposure (for foreign-asset ETFs).

Rules, first match wins:

| status | Condition |
|---|---|
| **low_priority** | Leveraged/inverse or single-stock leverage analysed as an ordinary candidate; AUM or turnover below minimum; spread excessive; premium/discount repeatedly large; tracking error very large; synthetic/derivative structure with inadequate disclosure |
| **hold** | Several core structure/trading fields unobtained (including any one of leverage status, AUM, turnover); holdings opaque; listed too recently for tracking-quality data with no other way to verify |
| **conditional** | Turnover or spread borderline; recently listed but other metrics sound; option overlay, currency hedging, or similar structural feature that needs a fit check |
| **pass** | None of the above |

Every verdict carries `reasons` (which checks tripped) and `impact` (one sentence on what it does to the Decision Gate). Example: "Low average turnover, wide spread, and too short a listing history for tracking-quality data → even with good theme-structure and holdings grades this may execute poorly in practice, so it is classified as conditional."

## The four verdict states

Every final ETF conclusion ends in exactly one of these. Evaluate in order — **① data coverage gate → ② structure/tradability hard gate → ③ three-axis grade gate → ④ explicit risk gate → ⑤ final state** — and the first one that trips decides.

| State | Rule |
|---|---|
| **on hold** | Any axis below 60% coverage or graded null; required holdings data missing; structure gate returned hold (insufficient data); core evidence conflicts across sources |
| **low priority** | Two or more axes at C+ or below; theme purity under 40%; structure gate returned low_priority (including leveraged/inverse/single-stock-leverage structures) |
| **conditional** | One axis at C+ or below; valuation premium or heavy top-holding concentration; structure gate returned conditional (liquidity, spread, tracking quality need checking); or any other explicit risk confirmed (overheating, regulation) |
| **worth reviewing** | All three axes B− or better; every axis at 70%+ coverage; structure gate passed; no unresolved critical risk |

State alongside the result that "worth reviewing" is not a recommendation to buy — it means the product itself can go on a review list. **Zero candidates worth reviewing is a valid outcome.** Do not manufacture one.

### Korean output

When the request is in Korean, use these labels — they are the established vocabulary, not a fresh translation:

| English | 한국어 |
|---|---|
| worth reviewing | 검토 가능 |
| conditional | 조건부 검토 |
| on hold | 판단 보류 |
| low priority | 우선순위 낮음 |

## QA checklist (used by qa-compliance-guard)

### A. Compliance and form
1. Zero banned phrases (attach the script output)
2. Every final conclusion ends in one of the four states
3. Every grade carries as-of date, sources, confidence, and coverage
4. Disclaimer present (`meta.disclaimer`)
5. Judgments that depend on the investor's own circumstances (horizon, amount, position size, account type, tax) are not asserted as properties of the ETF

### B. Data integrity
6. Theme analysis (forward-looking) and holdings analysis (current financials) are not mixed — current financial or valuation figures cited as evidence in 08, or forward-looking claims cited in 09, are violations
7. Final grades match the `weighted_grade.py` output (spot-check `final_numeric`)
8. Source priority respected — `reliability_tier` (primary/secondary/tertiary) recorded per source, and nothing marked unsupported used as grading evidence
9. Source conflicts recorded in `source_conflicts` and not hidden in the prose
10. Every theme evidence pack contains both positive and negative evidence (if negatives are zero, confirm it is marked "insufficiently verified")
11. The three selected themes each satisfy the minimum selection condition (2 of 8), with the reasoning recorded in 05

### C. Gates and structure
12. The structure/tradability hard gate is applied to every candidate and reflected in the Decision Gate verdict
13. `final_etf_decision.md` ends with the "What this supports deciding" section (five sub-sections plus the closing note)
14. All 20 required top-level keys present in `analysis.json` (including `meta`), among them `source_quality_policy`, `etf_structure_trading_gate`, `investment_judgment_readiness`, `pilot_acceptance_summary`, `investor_fit_required`
15. Every coverage gap appears in `data_coverage.md`

### D. Pilot acceptance test (additionally, when `output_scope=pilot`)
Judge each of the 15 questions pass / fail / needs_revision and record in `pilot_acceptance_summary`:
1. Do the sector candidates follow sensibly from the market regime?
2. Are the 10 theme candidates neither obvious filler nor invented?
3. Does every theme carry both positive and negative evidence?
4. Is the selection of the three core themes explained with data?
5. Are the rejected themes' reasons categorised and specific?
6. Do the ETF candidates actually exist, with basic facts verified?
7. Are candidates within a theme classified into comparable types?
8. Is the value-chain mapping based on holdings rather than the ETF's name?
9. Are the theme-structure, financial, and valuation axes kept separate?
10. Was the structure/tradability gate applied?
11. Does the Decision Gate end in one of the four states?
12. Does `final_etf_decision.md` close with the judgment-readiness assessment?
13. Does `data_coverage.md` actually show the gaps and low-confidence items?
14. Is the output free of banned language?
15. Is `analysis.json` structured so it can drive the WebView/MTS UI (schema respected)?
