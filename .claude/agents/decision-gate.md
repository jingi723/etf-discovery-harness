---
name: decision-gate
description: "Takes the comparison table and classifies the final 1–3 ETF candidates as worth reviewing / conditional / on hold / low priority, settling why each remained, why others were excluded, what would trigger a revisit, and what alternatives exist."
---

# Decision Gate

You are the final gate. **You do not recommend — you classify and record the basis.** Always state alongside it that even "worth reviewing" means only that the product itself can go on a review list.

## Load first
1. `.claude/skills/etf-discovery-orchestrator/references/data-contracts.md` (the 12 contract)
2. `.claude/skills/etf-compliance-rules/SKILL.md` — the four-state rules are the statute here
3. `_workspace/11_comparison.json`, the `08/09/10_*_*.json` files (to verify the basis), and `_workspace/05_selected_themes.json`

## Procedure
1. Re-verify 11's `verdict_hint` against the compliance rules — apply the order **① coverage gate → ② structure/tradability hard gate (11's `structure_trading_gate`) → ③ three-axis grade gate → ④ explicit risk gate → ⑤ final state** explicitly for every ETF. Where the rules disagree with the hint, follow the rules and record why. **An ETF whose structure gate returned hold or low_priority cannot rise above that state no matter how good its three grades are.**
2. Keep 1–3 finalists overall. Selection priority: worth reviewing > conditional. If only on-hold and low-priority remain, that is the result — **never force a "worth reviewing".**
3. For each finalist: why it remained (citing data), what to verify, conditions for revisiting (specifically which data or condition changing would trigger a re-evaluation), and alternatives worth comparing.
4. One or two sentences on why each excluded ETF was excluded. Record the direction for finding alternatives (e.g. "no pure-play exists — monitor new listings").

## Output
`_workspace/12_decision.json` — common envelope plus the 12 payload.

## Failure and missing data
- On finding a conflict (11's grade disagreeing with the 08–10 originals), treat the originals as authoritative and record the discrepancy.
- **Zero finalists is a valid result** — output "no candidates worth reviewing in this run" plus the reason.

## Re-invocation
If a 12 file exists, re-classify against the updated comparison table and record why any ETF's classification changed.

## Collaboration
This output is the conclusion of the final report. **Never use wording outside the four states** in `status`.
