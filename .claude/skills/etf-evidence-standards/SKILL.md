---
name: etf-evidence-standards
description: "Standards for collecting and recording data and evidence in ETF, theme, and market analysis. Use this skill for any task that gathers market indicators, theme evidence packs, ETF data, or financial and price data from the web. Triggers on: citing sources, recording as-of dates, judging source priority and reliability tier, handling conflicting sources, and handling missing data."
---

# Evidence Standards

Collected data becomes the basis of a final verdict, so nothing is usable until it carries a source, an as-of date, and a reliability tier. Data that does not meet this standard is discarded by downstream scorers rather than used.

## Write the checklist first

Before looking for data, write down what needs to be established about this target as a list of questions. Then find data for each question.

Listing only what you happened to find produces confirmation bias and hides what is missing. The checklist makes the gaps visible.

## Both directions are mandatory

- Look for positive and negative evidence together. **An evidence pack with zero negative findings is incomplete.**
- If you could not find negatives, mark it **"insufficiently verified"** — not "no negatives found, therefore no risk". Not finding something and it not existing are different claims.
- Never assert that a theme is "risk-free" or simply "good". For example: "AI semiconductors have strong demand and promising growth" is wrong; "AI semiconductors show rising GPU/HBM demand and supply bottlenecks, but the valuation premium on the largest names and export-control risk have to be checked alongside" is right.

## Source priority and reliability tiers

Four tiers:

| Tier | Definition | Usable for grading |
|---|---|---|
| primary | Official statistics, central banks, exchanges, regulatory filings, issuer materials | Yes |
| secondary | Major press, broker research, reputable data vendors (Morningstar, ETF.com, FMP) | Yes |
| tertiary | General finance portals and news — for events and supporting context only | Not on its own |
| unsupported | Blogs, forums, unattributed | **Never** |

Per-domain source rankings (ETF basics / holdings / financials / prices / themes) and the **six rules for handling source conflicts** are in `references/source-priority.md`. Read the table for your domain before you start collecting.

- A claim resting on a single secondary-or-lower source gets reduced confidence.
- Never build a theme-structure grade from a single tertiary source (news).
- When figures conflict across sources, do not delete either — record both and log it in the envelope's `source_conflicts`.

## Recording format

Every output follows the common envelope in the data contract (`.claude/skills/etf-discovery-orchestrator/references/data-contracts.md`). Each entry in `sources` fills eight fields: `source_name`, `source_type`, `url_or_reference`, `as_of_date`, `retrieved_at`, `reliability_tier`, `used_for`, `notes`. Individual evidence items:

```json
{"claim": "one sentence of established fact", "data": "the specific figure",
 "direction": "positive|negative", "source_idx": 0,
 "as_of": "YYYY-MM-DD", "confidence": "high|medium|low"}
```

- `as_of` is the date the *data* refers to, not the date the article was published. When it is unclear, use the access date and lower the confidence.
- `claim` holds verifiable statements of fact only. "Promising" or "will grow" are opinions and cannot be claims.

## Missing data

- Record anything you could not find in `coverage.missing`, and write one or two sentences in `impact_of_missing` about what that gap does to the verdict.
- If two or three searches do not turn it up, mark it missing and move on. Do not burn the run on an unbounded search.
- **Never estimate a value to fill a gap.** Quoting an approximation that a source itself states, with attribution, is fine.
