#!/usr/bin/env python3
"""Check workspace outputs against the data contract.

    python3 tools/check_workspace.py _workspace/

Exit code 0 when clean, 1 when anything fails. Catches the class of error an
agent cannot catch in itself: a summary that is right while the file it wrote
is not. One run had a mapper report "62 holdings, 55.31% weight, non-theme"
and then omit that bucket from its output, leaving the fund looking 100%
in-theme to everything downstream.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ENVELOPE = ["artifact", "as_of_date", "generated_by", "sources",
            "source_conflicts", "confidence", "coverage", "payload"]
TOL = 1.0   # percentage points; agents round per-holding weights


def check(path):
    """Yield failure strings for one workspace JSON file."""
    name = path.name
    try:
        d = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        yield f"{name}: unparseable — {e}"
        return

    # only the numbered agent artifacts carry the envelope; script bookkeeping
    # (12b_signal_scores, agent_costs) is not an agent output and is exempt
    is_agent_output = name[:2].isdigit() and "_" in name and not name.startswith("12b")
    if not is_agent_output:
        return
    if not isinstance(d, dict):
        yield f"{name}: agent artifact must be a JSON object"
        return
    for k in ENVELOPE:
        if k not in d:
            yield f"{name}: envelope missing '{k}'"
    if not d.get("sources"):
        yield f"{name}: sources is empty — the contract calls that invalid"
    p = d.get("payload") or {}
    if not isinstance(p, dict):
        yield f"{name}: payload must be a JSON object"
        return

    # 07 value chain: chain weights plus unclassified must close on 100
    if name.startswith("07_"):
        chains = p.get("chains") or []
        total = sum(c.get("weight_pct") or 0 for c in chains) + (p.get("unclassified_pct") or 0)
        if abs(total - 100) > TOL:
            yield (f"{name}: chain weights + unclassified = {total:.2f}%, expected ~100. "
                   f"{100 - total:.2f}% of the fund is unaccounted for")
        for c in chains:
            listed = sum(h.get("weight_pct") or 0 for h in (c.get("holdings") or []))
            if c.get("holdings") and abs(listed - (c.get("weight_pct") or 0)) > TOL:
                yield (f"{name}: chain '{c.get('chain','?')[:40]}' declares "
                       f"{c.get('weight_pct'):.2f}% but its holdings sum to {listed:.2f}%")
        theme_w = sum(c.get("weight_pct") or 0 for c in chains
                      if "non-theme" not in str(c.get("chain", "")).lower())
        if abs(theme_w - (p.get("purity_pct") or 0)) > TOL:
            yield (f"{name}: purity_pct {p.get('purity_pct')} does not match the "
                   f"theme chains' own weights ({theme_w:.2f}%)")

    # 08/09/10 scores: coverage gate and grade presence
    if name[:2] in ("08", "09", "10"):
        cov = p.get("coverage_pct")
        if cov is not None and cov < 60 and p.get("final_grade") is not None:
            yield (f"{name}: coverage {cov}% is below the 60% gate but "
                   f"final_grade is {p.get('final_grade')} — it should be null")
        for i in p.get("items") or []:
            if i.get("grade") and not i.get("rationale"):
                yield f"{name}: item '{i.get('name','?')[:30]}' is graded with no rationale"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default="_workspace")
    a = ap.parse_args()
    root = Path(a.path)
    files = sorted(root.glob("*.json")) if root.is_dir() else [root]
    if not files:
        ap.error(f"no JSON artifacts found in {root}")
    fails = [f for p in files for f in check(p)]
    for f in fails:
        print(f"  FAIL {f}")
    print(f"\n{len(files)} files checked, {len(fails)} failures")
    sys.exit(1 if fails else 0)


def demo():
    """Self-check: a fund whose buckets do not close must be caught."""
    import tempfile, os
    good = {k: "x" for k in ENVELOPE}
    good["sources"] = [{"source_name": "s"}]
    good["payload"] = {"chains": [{"chain": "a", "weight_pct": 60, "holdings": []},
                                  {"chain": "non-theme: cash & other", "weight_pct": 40,
                                   "holdings": []}],
                       "unclassified_pct": 0, "purity_pct": 60}
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "07_valuechain_OK.json"
        p.write_text(json.dumps(good))
        assert not list(check(p)), list(check(p))
        # drop the non-theme bucket, exactly the AIQ failure
        bad = json.loads(json.dumps(good))
        bad["payload"]["chains"] = bad["payload"]["chains"][:1]
        bad["payload"]["purity_pct"] = 60
        q = Path(td) / "07_valuechain_BAD.json"
        q.write_text(json.dumps(bad))
        fails = list(check(q))
        assert any("unaccounted for" in f for f in fails), fails
    print("ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        demo()
    else:
        main()
