#!/usr/bin/env python3
"""Render a scan's scores into static HTML.

The full pipeline's payload carries three grading axes, value chains and
holdings heatmaps; a scan carries none of those, so tools/render.py cannot read
it. This does the scan's shape — indicator rows with their bands, a holdings
treemap coloured by score rather than grade, and the structure gate.

    python3 tools/render_scan.py _workspace/12b_signal_scores.json \\
        --gate _workspace/11_structure_gate.json -o html/

Deterministic: same input, byte-identical output. It copies values and computes
nothing, so there is nothing for an agent to review.
"""
from __future__ import annotations

import argparse
import html as H
import json
import os

BANDS = [(80, "#B3261E", "#fff", "strong"), (60, "#C98A2B", "#fff", "firm"),
         (40, "#8A929C", "#fff", "mixed"), (20, "#3B63D6", "#fff", "soft"),
         (0, "#1E6FD9", "#fff", "weak")]
LBL = {"macro": "External", "value": "Valuation", "trend": "Chart (trend)",
       "momentum": "Momentum", "position": "Position", "rs": "Relative strength",
       "flow": "Volume / flows"}
CARD = ("margin:0 14px 12px;background:#fff;border:1px solid #EDF0F3;border-radius:16px;"
        "padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.04);")
SEC = "font-size:14px;font-weight:800;margin-bottom:12px;"
MUT = "font-size:11px;color:#8A929C;font-weight:700;"


def e(x):
    return H.escape(str(x)) if x is not None else ""


def band(v):
    for lo, bg, fg, name in BANDS:
        if v >= lo:
            return bg, fg, name
    return BANDS[-1][1:]


def dot(v):
    return "🔴" if v >= 80 else "🟠" if v >= 60 else "🟡" if v >= 40 else "🟢" if v >= 20 else "🔵"


def squarify(items, x, y, w, h):
    """Same layout as tools/render.py, kept local so this file stands alone."""
    if not items:
        return []
    total = sum(a for a, _ in items) or 1
    scale = (w * h) / total
    items = [(a * scale, o) for a, o in items]
    out, row, rx, ry, rw, rh = [], [], x, y, w, h

    def worst(row, length):
        if not row or length == 0:
            return float("inf")
        s = sum(row)
        mx, mn = max(row), min(row)
        return max(length * length * mx / (s * s), (s * s) / (length * length * mn))

    def flush(row, rx, ry, rw, rh):
        s = sum(row)
        res = []
        if rw >= rh:
            width = s / rh if rh else 0
            oy = ry
            for a in row:
                ah = a / width if width else 0
                res.append((rx, oy, width, ah)); oy += ah
            return res, rx + width, ry, rw - width, rh
        height = s / rw if rw else 0
        ox = rx
        for a in row:
            aw = a / height if height else 0
            res.append((ox, ry, aw, height)); ox += aw
        return res, rx, ry + height, rw, rh - height

    objs, i = [o for _, o in items], 0
    areas = [a for a, _ in items]
    while i < len(areas):
        length = min(rw, rh)
        if row and worst(row + [areas[i]], length) > worst(row, length):
            rects, rx, ry, rw, rh = flush(row, rx, ry, rw, rh)
            out += rects
            row = []
            continue
        row.append(areas[i]); i += 1
    if row:
        rects, *_ = flush(row, rx, ry, rw, rh)
        out += rects
    return list(zip(out, objs))


def page(t, r, gate, meta):
    bg, fg, name = band(r["swing"])
    rows = "".join(
        f'<div class="row">'
        f'<span style="width:16px;flex:none;">{dot(v) if v is not None else "⚪"}</span>'
        f'<span style="flex:1;min-width:0;font-size:12.5px;font-weight:600;'
        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{e(LBL[k])}</span>'
        f'<span style="{MUT}flex:none;white-space:nowrap;">wt {r["weights"][k]}%</span>'
        f'<span style="width:34px;flex:none;text-align:right;font-size:13px;font-weight:800;">'
        f'{v if v is not None else "n/a"}</span></div>'
        for k, v in r["parts"].items())

    tiles = ""
    hs = [(h["w"], h) for h in r["holdings"] if h["w"] > 0]
    for (rx, ry, rw, rh), h in squarify(sorted(hs, key=lambda p: -p[0]), 0, 0, 100, 100):
        hb, hf, _ = band(h["score"])
        big = rw * rh > 300
        named = rh > 6.0   # shorter than one line of text; a label would only clip
        tiles += (f'<div style="position:absolute;left:{rx:.2f}%;top:{ry:.2f}%;'
                  f'width:{rw:.2f}%;height:{rh:.2f}%;padding:2px;">'
                  f'<div style="width:100%;height:100%;background:{hb};color:{hf};'
                  f'border-radius:8px;padding:7px 8px;overflow:hidden;">'
                  f'<div style="font-size:{12 if big else 10}px;font-weight:800;">'
                  f'{e(h["sym"]) if named else ""}</div>'
                  + (f'<div style="font-size:10px;opacity:.85;margin-top:2px;">'
                     f'{h["w"]:.2f}% · {h["score"]:.0f}</div>' if big else "")
                  + "</div></div>")

    reasons = "; ".join(gate.get("reasons") or []) if gate else ""
    # Korean market convention: red is the strong end, blue the weak one.
    legend = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;{MUT}">'
        f'<span style="width:9px;height:9px;border-radius:50%;background:{c};"></span>'
        f'{n} {lo}+</span>'
        for lo, c, _, n in BANDS)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t)} scan</title>
<style>
 *{{box-sizing:border-box;margin:0;padding:0;-webkit-font-smoothing:antialiased;}}
 body{{background:#E7EAEE;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;color:#1A1D21;
       overflow-x:hidden;}}
 .row{{display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid #F2F4F6;}}
</style></head><body>
<div style="min-height:100vh;">
<div style="width:100%;max-width:430px;margin:0 auto;background:#F4F6F8;overflow:hidden;">
 <div style="background:#fff;border-bottom:1px solid #EAEDF0;padding:14px;">
  <div style="font-size:17px;font-weight:800;">{e(meta['names'].get(t, t))}</div>
  <div style="{MUT}margin-top:2px;">{e(t)} · {e(meta['sectors'].get(t,''))} · close {r['close']:,.2f} ({r['chg']:+.2f}%)</div>
 </div>
 <div style="{CARD}margin-top:14px;">
  <div style="display:flex;align-items:baseline;gap:10px;">
   <div style="font-size:32px;font-weight:800;color:{bg};">{r['swing']:.1f}</div>
   <div><div style="font-size:12px;font-weight:800;color:{bg};">{name.upper()}</div>
        <div style="{MUT}">one-month profile · long {r['long']:.1f} · short {r['short']:.1f}</div></div></div>
  <div style="margin-top:14px;">{rows}</div>
  <div style="{MUT}margin-top:10px;line-height:1.6;">
   20d {r['d20']:+.2f}% · rs {r['rs']:+.2f}pp · range position {r['pos60']:.0f}% ·
   from 60d high {r['fh']:+.2f}% · volume {r['vol']:.2f}x</div>
 </div>
 <div style="{CARD}">
  <div style="{SEC}">Top holdings, scored</div>
  <div style="{MUT}margin-bottom:10px;">Area is weight in the fund; colour is the holding's own score.</div>
  <div style="position:relative;width:100%;padding-top:62%;">
   <div style="position:absolute;inset:0;">{tiles}</div></div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;">{legend}</div>
  <div style="{MUT}margin-top:8px;">{e(r['breadth'])} of the top holdings have the 20-day above the 60-day.</div>
 </div>
 <div style="{CARD}">
  <div style="{SEC}">Structure &amp; tradability</div>
  <div style="font-size:12.5px;font-weight:700;color:#B7791F;">{e(gate.get('status','—') if gate else '—')}</div>
  <div style="font-size:11.5px;color:#5B6570;line-height:1.6;margin-top:6px;">{e(reasons)}</div>
 </div>
 <div style="{CARD}background:#FBFCFD;">
  <div style="{SEC}">What this scan did not check</div>
  <div style="font-size:11.5px;color:#5B6570;line-height:1.7;">
   Theme purity · holdings-level financials · valuation beyond the sub-sector band ·
   tracking quality. Deepening any of these means the full pipeline.</div>
  <div style="{MUT}margin-top:12px;padding-top:10px;border-top:1px solid #EDF0F3;line-height:1.6;">
   As of {e(r['date'])} · macro input {r['macro']} for this sector.
   Research notes, not investment advice.</div>
 </div>
 <div style="height:20px;"></div>
</div></div></body></html>"""


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("scores")
    a.add_argument("--gate")
    a.add_argument("--meta", help="optional JSON of {names:{}, sectors:{}}")
    a.add_argument("-o", "--out", default="html")
    n = a.parse_args()
    scores = json.load(open(n.scores))
    gates = json.load(open(n.gate))["payload"]["gates"] if n.gate else {}
    meta = json.load(open(n.meta)) if n.meta else {"names": {}, "sectors": {}}
    meta.setdefault("names", {}); meta.setdefault("sectors", {})
    os.makedirs(n.out, exist_ok=True)
    for t, r in scores.items():
        open(os.path.join(n.out, f"scan_{t}.html"), "w").write(page(t, r, gates.get(t, {}), meta))
    print("generated:", sorted(os.listdir(n.out)))


def demo():
    """Self-check: the treemap must place every holding and nothing else."""
    items = [(50, "a"), (30, "b"), (20, "c")]
    out = squarify(items, 0, 0, 100, 100)
    assert len(out) == 3, out
    area = sum(w * h for (_, _, w, h), _ in out)
    assert abs(area - 10000) < 1, area
    assert dot(85) == "🔴" and dot(10) == "🔵"
    assert band(90)[2] == "strong" and band(5)[2] == "weak"
    print("ok")


if __name__ == "__main__":
    import sys
    if "--self-check" in sys.argv:
        demo()
    else:
        main()
