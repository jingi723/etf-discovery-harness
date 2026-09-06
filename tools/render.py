#!/usr/bin/env python3
"""Render ui_payload.json into static mobile HTML pages.

Deterministic: same payload in, byte-identical HTML out. It copies payload
values verbatim and computes nothing, which is why no agent reviews its output
— a renderer that cannot invent a grade cannot misreport one.

    python3 tools/render.py path/to/ui_payload.json -o path/to/html/

Produces discovery_index.html, etf_{ticker}.html per finalist, and compare.html.
Self-contained: inline styles, no external resources, 430px container.
"""
import argparse
import html as H
import json
import os

_a = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
_a.add_argument("payload", help="path to ui_payload.json")
_a.add_argument("-o", "--out", default="html", help="output directory (default: ./html)")
A = _a.parse_args()

P = json.load(open(A.payload, encoding="utf-8"))
OUT = A.out
os.makedirs(OUT, exist_ok=True)


def e(x):
    return H.escape(str(x)) if x is not None else ""

# grade colours
def gcol(grade):
    if not grade:
        return ("#98A0AA", "#F1F3F5")
    t = grade[0]
    return {"A": ("#0F7A54", "#E6F4EE"), "B": ("#1D4ED8", "#EAF0FE"),
            "C": ("#B7791F", "#FBF3E4"), "D": ("#E5342A", "#FDEAE8")}.get(t, ("#98A0AA", "#F1F3F5"))

def gtxt(grade):
    return e(grade) if grade else "analysis limited"

def state_col(state):
    # both label sets — a run is in one language or the other
    return {"worth reviewing": ("#1D4ED8", "#EAF0FE"), "검토 가능": ("#1D4ED8", "#EAF0FE"),
            "conditional": ("#B7791F", "#FBF3E4"), "조건부 검토": ("#B7791F", "#FBF3E4"),
            "on hold": ("#5B6570", "#EEF1F4"), "판단 보류": ("#5B6570", "#EEF1F4"),
            "low priority": ("#5B6570", "#EEF1F4"), "우선순위 낮음": ("#5B6570", "#EEF1F4"),
            }.get(state, ("#5B6570", "#EEF1F4"))

CARD = "margin:0 14px 12px;background:#fff;border:1px solid #EDF0F3;border-radius:16px;padding:16px;box-shadow:0 1px 2px rgba(16,24,40,.04);"
SEC_T = "font-size:14px;font-weight:800;margin-bottom:12px;display:flex;align-items:center;gap:6px;"
AI_CHIP = '<span style="display:inline-flex;width:20px;height:20px;border-radius:6px;background:#1D4ED8;color:#fff;font-size:10px;font-weight:800;align-items:center;justify-content:center;">AI</span>'
MUT = "font-size:11px;color:#8A929C;font-weight:700;"

# treemap colours - solid fill, white text
def heat_col(grade):
    if not grade:
        return ("#C7CDD4", "#5B6570")  # analysis limited
    return {"A": ("#0F7A54", "#fff"), "B": ("#3B63D6", "#fff"),
            "C": ("#C98A2B", "#fff"), "D": ("#E5342A", "#fff"),
            "F": ("#E5342A", "#fff")}.get(grade[0], ("#C7CDD4", "#5B6570"))

def squarify(items, x, y, w, h):
    """Squarified treemap. items: [(area, obj)] descending. Coordinates are 0-100 percentages."""
    rects = []
    items = [it for it in items if it[0] > 0]
    while items:
        if w <= 0 or h <= 0:
            break
        total = sum(a for a, _ in items)
        row, rest = [items[0]], items[1:]
        def worst(row, length, total_area):
            s = sum(a for a, _ in row)
            side = s / length if length else 1
            r = []
            for a, _ in row:
                d = a / side if side else 1
                r.append(max(side / d, d / side) if d else 1e9)
            return max(r)
        length = min(w, h)
        scale = (w * h) / total if total else 1
        while rest:
            cand = row + [rest[0]]
            if worst([(a * scale, o) for a, o in cand], length, total) <= \
               worst([(a * scale, o) for a, o in row], length, total):
                row.append(rest.pop(0))
            else:
                break
        s = sum(a for a, _ in row) * scale
        if w >= h:  # lay out as a vertical column
            cw = s / h if h else 0
            cy = y
            for a, o in row:
                ch = (a * scale) / cw if cw else 0
                rects.append((x, cy, cw, ch, o))
                cy += ch
            x += cw; w -= cw
        else:      # lay out as a horizontal row
            rh = s / w if w else 0
            cx = x
            for a, o in row:
                cw2 = (a * scale) / rh if rh else 0
                rects.append((cx, y, cw2, rh, o))
                cx += cw2
            y += rh; h -= rh
        items = rest
    return rects

def badge(text, fg, bg, size=11):
    return (f'<span style="font-size:{size}px;font-weight:800;color:{fg};background:{bg};'
            f'border-radius:6px;padding:3px 8px;white-space:nowrap;">{e(text)}</span>')

def grade_chip(grade, size=12):
    fg, bg = gcol(grade)
    return badge(gtxt(grade), fg, bg, size)

def warn_card(warnings, title="Data to verify"):
    if not warnings:
        return ""
    items = "".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;">'
        f'<span style="flex:none;margin-top:3px;font-size:10px;color:#B7791F;">▲</span>'
        f'<span style="font-size:11.5px;color:#6B5A2E;line-height:1.55;">{e(w)}</span></div>'
        for w in warnings)
    return (f'<div style="margin:0 14px 12px;background:#FFFDF5;border:1px solid #F2E3BC;border-radius:14px;padding:13px 15px;">'
            f'<div style="font-size:12px;font-weight:800;color:#8A6D1F;margin-bottom:4px;">⚠ {e(title)}</div>{items}</div>')

BODIES = []  # (title, body) in render order — reused by report.html


def page_shell(title, body, footer_dates):
    BODIES.append((title, body))
    meta = P["meta"]
    dates = "".join(f'<div style="display:flex;justify-content:space-between;padding:3px 0;">'
                    f'<span style="{MUT}">{e(k)}</span><span style="font-size:11px;color:#39414B;font-weight:600;">{e(v)}</span></div>'
                    for k, v in footer_dates if v)
    return f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>
  * {{ box-sizing: border-box; -webkit-font-smoothing: antialiased; margin:0; padding:0; }}
  body {{ background:#E7EAEE; font-family:Pretendard,-apple-system,'Apple SD Gothic Neo','Noto Sans KR',sans-serif; }}
  ::-webkit-scrollbar {{ display:none; }}
  a {{ text-decoration:none; color:inherit; }}
  details summary {{ list-style:none; cursor:pointer; }}
  details summary::-webkit-details-marker {{ display:none; }}
</style></head>
<body>
<div style="min-height:100vh;background:#E7EAEE;">
<div style="width:100%;max-width:430px;margin:0 auto;background:#F4F6F8;position:relative;color:#1A1D21;overflow:hidden;">
{body}
  <div style="{CARD}margin-bottom:0;">
    <div style="font-size:12px;font-weight:800;margin-bottom:8px;">Data basis</div>
    {dates}
    <div style="font-size:10.5px;color:#A6AEB8;line-height:1.6;margin-top:10px;padding-top:9px;border-top:1px solid #EDF0F3;">{e(meta['disclaimer'])} Grades describe the fund's characteristics; they are not buy or recommendation ratings.</div>
  </div>
  <div style="height:32px;"></div>
</div></div>
</body></html>"""

def header(title_main, title_sub, back_href=None):
    back = f'<a href="{back_href}" style="font-size:20px;color:#5B6570;">‹</a>' if back_href else '<span style="font-size:20px;color:#C4CBD4;">‹</span>'
    return (f'<div style="position:sticky;top:0;z-index:20;background:#fff;border-bottom:1px solid #EAEDF0;">'
            f'<div style="display:flex;align-items:center;gap:10px;padding:12px 14px;">{back}'
            f'<div style="flex:1;min-width:0;"><div style="font-size:16px;font-weight:800;line-height:1.25;">{e(title_main)}</div>'
            f'<div style="font-size:11px;color:#8A929C;margin-top:1px;">{e(title_sub)}</div></div></div></div>')

def ratings_bar(ratings, meta_r):
    ts, fi, va = ratings.get("theme_structure"), ratings.get("financial"), ratings.get("valuation")
    def cell(label, g, m):
        fg, _ = gcol(g)
        cv = m.get("coverage_pct")
        cov = f'<div style="font-size:9.5px;color:#A6AEB8;margin-top:3px;">coverage {cv}% · {e(m.get("confidence",""))}</div>' if cv is not None else ""
        return (f'<div style="flex:1;padding:12px;"><div style="font-size:11px;color:#1F2937;font-weight:800;">{e(label)}</div>'
                f'<div style="font-size:19px;font-weight:800;color:{fg};margin-top:6px;line-height:1;">{gtxt(g)}</div>{cov}</div>')
    return (f'<div style="margin-top:14px;"><div style="{MUT}margin-bottom:8px;">Key grades</div>'
            f'<div style="display:flex;border:1px solid #EDF0F3;border-radius:12px;overflow:hidden;">'
            f'{cell("Theme structure", ts, meta_r.get("theme_structure",{}))}'
            f'<div style="width:1px;background:#EDF0F3;"></div>'
            f'{cell("Financials", fi, meta_r.get("financial",{}))}'
            f'<div style="width:1px;background:#EDF0F3;"></div>'
            f'{cell("Valuation", va, meta_r.get("valuation",{}))}</div></div>')

def bullet_list(items, color="#39414B"):
    return "".join(f'<div style="display:flex;gap:8px;align-items:flex-start;padding:4px 0;">'
                   f'<span style="flex:none;width:5px;height:5px;border-radius:50%;background:#B4BBC4;margin-top:7px;"></span>'
                   f'<span style="font-size:12px;color:{color};line-height:1.6;">{e(t)}</span></div>' for t in items)

# ---------------- discovery_index ----------------
def render_index():
    d = P["discovery_index"]
    sectors = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid #F5F7F9;">'
        f'{grade_chip(s["grade"], 13)}<div style="flex:1;"><div style="font-size:13px;font-weight:800;">{e(s["name"])}</div>'
        f'<div style="font-size:11.5px;color:#5B6570;line-height:1.55;margin-top:2px;">{e(s["reason"])}</div></div></div>'
        for s in d["selected_sectors"])
    themes = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid #F5F7F9;">'
        f'<span style="flex:none;width:26px;text-align:center;font-size:12px;font-weight:800;color:#1D4ED8;background:#EAF0FE;border-radius:6px;padding:3px 0;">{i+1}</span>'
        f'<div style="flex:1;"><div style="display:flex;align-items:center;gap:6px;"><span style="font-size:13px;font-weight:800;">{e(t["name"])}</span>'
        f'<span style="font-size:10px;color:#A6AEB8;font-weight:700;">confidence {e(t.get("data_confidence") or "-")}</span></div>'
        f'<div style="font-size:11.5px;color:#5B6570;line-height:1.55;margin-top:2px;">{e(t["main_point"])}</div></div></div>'
        for i, t in enumerate(d["selected_themes"]))
    fins = ""
    for f in d["finalists"]:
        sfg, sbg = state_col(f["decision_state"])
        r = f["ratings"]
        fins += (f'<a href="etf_{f["ticker"]}.html" style="display:block;padding:12px 0;border-bottom:1px solid #F5F7F9;">'
                 f'<div style="display:flex;align-items:center;gap:8px;"><div style="flex:1;min-width:0;">'
                 f'<div style="font-size:13.5px;font-weight:800;">{e(f["name"])}</div>'
                 f'<div style="font-size:10.5px;color:#8A929C;margin-top:1px;">{e(f["ticker"])} · {e(f["theme"])}</div></div>'
                 f'{badge(f["decision_state"], sfg, sbg)}'
                 f'<span style="font-size:13px;color:#B4BBC4;">›</span></div>'
                 f'<div style="display:flex;gap:6px;margin-top:8px;"><span style="{MUT}">theme {gtxt(r.get("theme_structure"))}</span>'
                 f'<span style="{MUT}">fin {gtxt(r.get("financial"))}</span><span style="{MUT}">val {gtxt(r.get("valuation"))}</span></div></a>')
    body = f"""
{header("ETF Discovery", f'{e(P["meta"]["run_date"])} · sector -> theme -> candidates -> verification')}
<div style="padding:14px 0 8px;">
  <div style="{CARD}">
    <div style="{SEC_T}">{AI_CHIP}Summary</div>
    <div style="font-size:15.5px;font-weight:800;line-height:1.55;letter-spacing:-.2px;">{e(d["headline"])}</div>
    <div style="font-size:12px;color:#39414B;line-height:1.65;margin-top:10px;">{e(d["market_one_liner"])}</div>
  </div>
  <div style="{CARD}"><div style="{SEC_T}">Selected sectors</div>{sectors}</div>
  <div style="{CARD}"><div style="{SEC_T}">Core themes</div>{themes}</div>
  <div style="{CARD}"><div style="{SEC_T}">Final candidates <a href="compare.html" style="margin-left:auto;font-size:11px;font-weight:700;color:#1D4ED8;">compare ›</a></div>{fins}
    <div style="font-size:10.5px;color:#A6AEB8;line-height:1.5;margin-top:10px;">A 'conditional' verdict is not a recommendation - it means the product itself can go on a review list once the noted conditions are resolved.</div>
  </div>
  {warn_card(d["data_warnings"])}
  <div style="{CARD}"><div style="{SEC_T}">Next checks</div>{bullet_list(d["next_checks"])}</div>
</div>"""
    dates = [("As-of date", P["meta"]["as_of_date"]), ("Holdings as of", P["meta"]["data_dates"].get("holdings")), ("Analysis updated", P["meta"]["data_dates"].get("analysis_updated")),
             ("Price as of", P["meta"]["data_dates"].get("price"))]
    open(os.path.join(OUT, "discovery_index.html"), "w", encoding="utf-8").write(
        page_shell("ETF Discovery", body, dates))

# ---------------- etf detail ----------------
def render_etf(pg):
    tick = pg["ticker"]
    sfg, sbg = state_col(pg["decision_state"])
    gate = pg.get("structure_gate", {})
    price_note = f'Price as of {e(P["meta"]["data_dates"].get("price") or "-")} · not live'
    # value chain (details accordion)
    vc_rows = ""
    for c in pg.get("value_chain", []):
        fg, bg = gcol(c.get("grade"))
        rel = ", ".join((h.get("name", "") if isinstance(h, dict) else str(h))
                        for h in (c.get("related_holdings") or []))
        risk = f'<div style="font-size:11px;color:#8A6D1F;line-height:1.55;margin-top:6px;">Risk · {e(c["risk"])}</div>' if c.get("risk") else ""
        relh = f'<div style="font-size:10.5px;color:#8A929C;margin-top:6px;">Related holdings · {e(rel)}</div>' if rel else ""
        vc_rows += (f'<details style="border-bottom:1px solid #F5F7F9;"><summary style="padding:10px 0;">'
                    f'<div style="display:flex;align-items:center;gap:8px;">'
                    f'<span style="flex:1;font-size:12.5px;font-weight:700;">{e(c["name"])}</span>'
                    f'<span style="font-size:12px;font-weight:800;color:#39414B;">{e(c.get("pct"))}%</span>{grade_chip(c.get("grade"))}'
                    f'<span style="font-size:11px;color:#B4BBC4;">▾</span></div>'
                    f'<div style="height:5px;background:#EEF1F4;border-radius:3px;margin-top:8px;overflow:hidden;">'
                    f'<div style="width:{min(float(c.get("pct") or 0),100)}%;height:100%;background:{fg};"></div></div></summary>'
                    f'<div style="padding:2px 0 12px;"><div style="font-size:11.5px;color:#39414B;line-height:1.6;">{e(c.get("point") or "insufficient supporting data")}</div>{risk}{relh}</div></details>')
    # constituent score map - the treemap is the main UI (area = weight, colour = selected tab's grade)
    heat = pg.get("holdings_heatmap", [])
    meta_hm = pg.get("holdings_heatmap_meta", {})
    rects = squarify(sorted([(float(h1.get("weight_pct") or 0), h1) for h1 in heat],
                            key=lambda x: -x[0]), 0, 0, 100, 100)
    tiles = ""
    for i, (rx, ry, rw, rh, h1) in enumerate(rects):
        ffg = heat_col(h1.get("financial_grade"))
        vfg = heat_col(h1.get("valuation_grade"))
        big = rw * rh > 400  # two-line labels on large tiles only
        label = (f'<div style="font-size:{11 if big else 9}px;font-weight:800;line-height:1.2;'
                 f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{e(h1.get("short_name") or h1["name"])}</div>'
                 + (f'<div style="font-size:9.5px;opacity:.85;margin-top:2px;">{e(h1.get("weight_pct"))}% · <span class="hm-g" data-i="{i}">{gtxt(h1.get("financial_grade"))}</span></div>' if big else ""))
        tiles += (f'<div class="hm-tile" data-i="{i}" data-name="{e(h1["name"])}" data-w="{e(h1.get("weight_pct"))}"'
                  f' data-fin="{gtxt(h1.get("financial_grade"))}" data-val="{gtxt(h1.get("valuation_grade"))}"'
                  f' data-finbg="{ffg[0]}" data-fintx="{ffg[1]}" data-valbg="{vfg[0]}" data-valtx="{vfg[1]}"'
                  f' style="position:absolute;left:{rx:.2f}%;top:{ry:.2f}%;width:{rw:.2f}%;height:{rh:.2f}%;'
                  f'background:{ffg[0]};color:{ffg[1]};padding:5px 6px;border:1.5px solid #fff;border-radius:6px;'
                  f'overflow:hidden;cursor:pointer;">{label}</div>')
    legend = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:10px;color:#5B6570;font-weight:600;">'
        f'<span style="width:10px;height:10px;border-radius:3px;background:{c};"></span>{lab}</span>'
        for c, lab in [("#0F7A54", "A favourable"), ("#3B63D6", "B sound"),
                       ("#C98A2B", "C check needed"), ("#E5342A", "D/F caution"),
                       ("#C7CDD4", "analysis limited")])
    named = [h1 for h1 in heat if "Other" not in h1["name"] and "기타" not in h1["name"] and "unclassified" not in h1["name"]]
    table_rows = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #F5F7F9;">'
        f'<span style="flex:1;min-width:0;font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{e(h1["name"])}</span>'
        f'<span style="width:52px;text-align:right;font-size:11.5px;font-weight:700;color:#39414B;">{e(h1.get("weight_pct"))}%</span>'
        f'<span style="width:44px;text-align:center;">{grade_chip(h1.get("financial_grade"),11)}</span>'
        f'<span style="width:44px;text-align:center;">{grade_chip(h1.get("valuation_grade"),11)}</span></div>'
        for h1 in sorted(named, key=lambda x: -float(x.get("weight_pct") or 0))[:10])
    top_summary = (f'The top {min(10, len(named))} holdings account for {e(meta_hm.get("top10_weight_pct"))}% of the fund.'
                   if meta_hm.get("top10_weight_pct") is not None else "")
    heatmap_html = f"""
    <div style="{MUT}margin-bottom:8px;">Area is weight within the ETF; colour is the grade on the selected axis.</div>
    <div style="display:flex;gap:6px;margin-bottom:10px;">
      <button id="hm-tab-fin" onclick="hmMode('fin')" style="flex:1;padding:8px 0;border-radius:9px;border:1px solid #1D4ED8;background:#1D4ED8;color:#fff;font-size:12px;font-weight:800;cursor:pointer;">Financials</button>
      <button id="hm-tab-val" onclick="hmMode('val')" style="flex:1;padding:8px 0;border-radius:9px;border:1px solid #E4E9F2;background:#fff;color:#5B6570;font-size:12px;font-weight:800;cursor:pointer;">Valuation</button>
    </div>
    <div id="hm-map" style="position:relative;width:100%;height:240px;border-radius:10px;overflow:hidden;background:#EEF1F4;">{tiles}</div>
    <div id="hm-sel" style="display:flex;align-items:center;gap:8px;margin-top:10px;border:1px solid #EDF0F3;border-radius:10px;padding:9px 12px;">
      <span id="hm-sel-name" style="flex:1;font-size:12px;font-weight:800;">Tap a holding</span>
      <span id="hm-sel-w" style="{MUT}"></span>
      <span id="hm-sel-fin" style="font-size:11px;font-weight:800;"></span>
      <span id="hm-sel-val" style="font-size:11px;font-weight:800;"></span>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px 12px;margin-top:10px;">{legend}</div>
    <div style="font-size:11.5px;color:#39414B;font-weight:600;margin-top:10px;">{top_summary}</div>
    <details style="margin-top:8px;">
      <summary style="text-align:center;font-size:12px;font-weight:800;color:#1D4ED8;border:1px solid #E4E9F2;border-radius:10px;padding:9px 0;">Show constituent detail ▾</summary>
      <div style="margin-top:8px;">
        <div style="display:flex;gap:8px;padding-bottom:6px;border-bottom:1px solid #EDF0F3;">
          <span style="flex:1;{MUT}">Holding</span><span style="width:52px;text-align:right;{MUT}">Weight</span>
          <span style="width:44px;text-align:center;{MUT}">Fin</span><span style="width:44px;text-align:center;{MUT}">Val</span></div>
        {table_rows}
      </div>
    </details>
    <script>
    var hmM='fin';
    function hmMode(m){{hmM=m;
      document.getElementById('hm-tab-fin').style.background=m==='fin'?'#1D4ED8':'#fff';
      document.getElementById('hm-tab-fin').style.color=m==='fin'?'#fff':'#5B6570';
      document.getElementById('hm-tab-fin').style.borderColor=m==='fin'?'#1D4ED8':'#E4E9F2';
      document.getElementById('hm-tab-val').style.background=m==='val'?'#1D4ED8':'#fff';
      document.getElementById('hm-tab-val').style.color=m==='val'?'#fff':'#5B6570';
      document.getElementById('hm-tab-val').style.borderColor=m==='val'?'#1D4ED8':'#E4E9F2';
      document.querySelectorAll('.hm-tile').forEach(function(t){{
        t.style.background=t.dataset[m+'bg'];t.style.color=t.dataset[m+'tx'];
        var g=t.querySelector('.hm-g');if(g)g.textContent=t.dataset[m];}});}}
    document.querySelectorAll('.hm-tile').forEach(function(t){{t.addEventListener('click',function(){{
      document.getElementById('hm-sel-name').textContent=t.dataset.name;
      document.getElementById('hm-sel-w').textContent='Weight '+t.dataset.w+'%';
      document.getElementById('hm-sel-fin').textContent='Fin '+t.dataset.fin;
      document.getElementById('hm-sel-fin').style.color=t.dataset.finbg;
      document.getElementById('hm-sel-val').textContent='Val '+t.dataset.val;
      document.getElementById('hm-sel-val').style.color=t.dataset.valbg;}});}});
    </script>"""
    tops = "".join(
        f'<div style="display:flex;gap:9px;align-items:flex-start;padding:8px 0;border-bottom:1px solid #F5F7F9;">'
        f'<span style="flex:none;width:50px;font-size:11.5px;font-weight:800;color:#39414B;text-align:right;">{e(t.get("weight_pct"))}%</span>'
        f'<div style="flex:1;"><div style="font-size:12.5px;font-weight:700;">{e(t["name"])}</div>'
        f'<div style="font-size:11px;color:#8A929C;line-height:1.5;margin-top:1px;">{e(t.get("role") or "")}</div></div></div>'
        for t in pg.get("top_holdings", []))
    def detail_block(title, det):
        up = bullet_list(det.get("uplift", []), "#0F7A54")
        dn = bullet_list(det.get("drag", []), "#B7791F")
        return (f'<details style="margin-top:10px;border:1px solid #EDF0F3;border-radius:12px;padding:0 12px;">'
                f'<summary style="padding:11px 0;font-size:12px;font-weight:800;">{e(title)} detail ▾</summary>'
                f'<div style="padding-bottom:12px;"><div style="font-size:11.5px;color:#39414B;line-height:1.6;">{e(det.get("summary") or "")}</div>'
                + (f'<div style="{MUT}margin-top:8px;">What lifts it</div>{up}' if det.get("uplift") else "")
                + (f'<div style="{MUT}margin-top:8px;">What drags it</div>{dn}' if det.get("drag") else "")
                + '</div></details>')
    tk = pg.get("theme_key_point", {})
    fin_asof = P["meta"]["data_dates"].get("financial_asof", {}).get(tick)
    body = f"""
{header(pg["name"], f'{tick} · ETF · {e(pg["market"])}', "discovery_index.html")}
<div style="background:#fff;border-bottom:1px solid #EAEDF0;padding:8px 16px 10px;">
  <span style="font-size:12px;color:#8A929C;font-weight:600;">{price_note}</span>
</div>
<div style="padding:14px 0 8px;">
  <div style="{CARD}border-radius:18px;">
    <div style="{SEC_T}">{AI_CHIP}Analysis summary<span style="margin-left:auto;font-size:10px;color:#A6AEB8;font-weight:600;">{e(pg["theme"])}</span></div>
    <div style="display:flex;align-items:center;gap:8px;">{badge(pg["decision_state"], sfg, sbg, 12)}
    <span style="font-size:10.5px;color:#A6AEB8;">Theme purity {e(pg.get("purity_pct"))}%</span></div>
    <div style="font-size:13px;color:#39414B;line-height:1.65;margin-top:10px;">{e(pg["summary"])}</div>
    {ratings_bar(pg["ratings"], pg.get("ratings_meta", {}))}
  </div>
  <div style="{CARD}">
    <div style="{SEC_T}">Why this verdict</div>
    {bullet_list(pg.get("why_conditionally_considered", []))}
    <div style="{MUT}margin-top:10px;">What to verify</div>
    {bullet_list(pg.get("check_points", []))}
    <div style="{MUT}margin-top:10px;">Conditions to revisit</div>
    {bullet_list(pg.get("recheck_conditions", []))}
    <div style="font-size:10.5px;color:#A6AEB8;margin-top:10px;">Structure gate · {e(gate.get("status") or "-")} — {e("; ".join(gate.get("reasons") or []))}</div>
  </div>
  <div style="{CARD}">
    <div style="{SEC_T}">Theme key point<span style="margin-left:auto;">{grade_chip(tk.get("structure_grade"))}</span></div>
    <div style="font-size:13px;font-weight:800;">{e(tk.get("name") or pg["theme"])}</div>
    <div style="font-size:12px;color:#39414B;line-height:1.65;margin-top:6px;">{e(tk.get("main_point") or "")}</div>
    <div style="font-size:11.5px;color:#5B6570;line-height:1.6;margin-top:8px;padding-top:8px;border-top:1px solid #F5F7F9;">{e(tk.get("interpretation") or "")}</div>
  </div>
  <div style="{CARD}">
    <div style="{SEC_T}">Theme value chain</div>
    <div style="{MUT}margin-bottom:4px;">Tap a chain to open its evidence and risks.</div>
    {vc_rows}
  </div>
  <div style="{CARD}">
    <div style="{SEC_T}">Constituent score map</div>
    {heatmap_html}
    {detail_block("Financials", pg.get("financial_detail", {}))}
    {detail_block("Valuation", pg.get("valuation_detail", {}))}
  </div>
  <div style="{CARD}"><div style="{SEC_T}">Top holdings</div>{tops}</div>
  {warn_card(pg.get("data_warnings", []))}
</div>"""
    dates = [("As-of date", P["meta"]["as_of_date"]), ("Holdings as of", P["meta"]["data_dates"].get("holdings")), ("Price as of", P["meta"]["data_dates"].get("price")),
             ("Financials as of", fin_asof), ("Analysis updated", P["meta"]["data_dates"].get("analysis_updated"))]
    open(os.path.join(OUT, f"etf_{tick}.html"), "w", encoding="utf-8").write(
        page_shell(f'{pg["name"]} analysis', body, dates))

# ---------------- compare ----------------
def compare_card(r):
    sfg, sbg = state_col(r["decision_state"])
    detail_tickers = {p["ticker"] for p in P["etf_pages"]}
    arrow = ('<span style="font-size:13px;color:#B4BBC4;">›</span>'
             if r["ticker"] in detail_tickers else '')
    head = (f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="flex:1;"><div style="font-size:13.5px;font-weight:800;">{e(r["name"])}</div>'
            f'<div style="font-size:10.5px;color:#8A929C;">{e(r["ticker"])} · {e(r["theme"])}'
            + (f' · {e(r["section"])}' if r.get("section") else '') + '</div></div>'
            f'{badge(r["decision_state"], sfg, sbg)}{arrow}</div>')
    if r["ticker"] in detail_tickers:
        head = f'<a href="etf_{r["ticker"]}.html">{head}</a>'
    return (f'<div style="{CARD}">{head}'
            f'<div style="display:flex;gap:6px;margin-top:10px;">'
            f'<div style="flex:1;text-align:center;border:1px solid #EDF0F3;border-radius:10px;padding:8px 0;"><div style="{MUT}">Theme</div><div style="margin-top:4px;">{grade_chip(r.get("theme_structure"),13)}</div></div>'
            f'<div style="flex:1;text-align:center;border:1px solid #EDF0F3;border-radius:10px;padding:8px 0;"><div style="{MUT}">Financials</div><div style="margin-top:4px;">{grade_chip(r.get("financial"),13)}</div></div>'
            f'<div style="flex:1;text-align:center;border:1px solid #EDF0F3;border-radius:10px;padding:8px 0;"><div style="{MUT}">Valuation</div><div style="margin-top:4px;">{grade_chip(r.get("valuation"),13)}</div></div></div>'
            f'<div style="font-size:10.5px;color:#A6AEB8;margin-top:8px;">Structure gate · {e(r.get("structure_gate") or "-")}</div>'
            f'<div style="{MUT}margin-top:8px;">Why it remained</div>{bullet_list(r.get("why_remained", []))}'
            f'<div style="{MUT}margin-top:8px;">What to verify</div>{bullet_list(r.get("check_points", []))}</div>')

def render_compare():
    rows = "".join(compare_card(r) for r in P["compare_page"]["rows"])
    reverify = ""
    rrows = P["compare_page"].get("reverify_rows") or []
    if rrows:
        reverify = (f'<div style="margin:18px 14px 8px;"><div style="font-size:13px;font-weight:800;">Re-verification track — runner-up theme</div>'
                    f'<div style="font-size:11px;color:#8A929C;line-height:1.5;margin-top:3px;">The theme was not selected in this run, so these are not final candidates — the re-evaluation is recorded for reference only.</div></div>'
                    + "".join(compare_card(r) for r in rrows))
    body = f"""
{header("Candidate comparison", f'{e(P["meta"]["run_date"])} · {len(P["compare_page"]["rows"])} candidates + {len(rrows)} re-verified · by verdict', "discovery_index.html")}
<div style="padding:14px 0 8px;">{rows}{reverify}</div>"""
    dates = [("As-of date", P["meta"]["as_of_date"]), ("Holdings as of", P["meta"]["data_dates"].get("holdings")), ("Analysis updated", P["meta"]["data_dates"].get("analysis_updated"))]
    open(os.path.join(OUT, "compare.html"), "w", encoding="utf-8").write(
        page_shell("Candidate comparison", body, dates))

def render_report():
    """Single-document print version — PDF/DOCX source. Same blocks, no links."""
    m = P["meta"]
    dates = [("As-of date", m.get("as_of_date")), ("Run date", m.get("run_date")),
             ("Holdings as of", m["data_dates"].get("holdings")),
             ("Price as of", m["data_dates"].get("price"))]
    foot = "".join(f'<div style="display:flex;justify-content:space-between;padding:3px 0;">'
                   f'<span style="{MUT}">{e(k)}</span>'
                   f'<span style="font-size:11px;color:#39414B;font-weight:600;">{e(v)}</span></div>'
                   for k, v in dates if v)
    # the heatmap widget uses fixed element ids; concatenating pages would
    # collide them, so give each section its own namespace
    sections = "".join(
        f'<section style="break-before:page;page-break-before:always;">'
        f'{b.replace("hm-", f"hm{i}-")}</section>'
        for i, (_, b) in enumerate(BODIES))
    open(os.path.join(OUT, "report.html"), "w", encoding="utf-8").write(f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>{e(m.get("run_date", ""))} ETF Discovery Report</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; -webkit-font-smoothing:antialiased; }}
  body {{ background:#F4F6F8; color:#1A1D21;
         font-family:Pretendard,-apple-system,'Apple SD Gothic Neo','Noto Sans KR',sans-serif; }}
  .doc {{ max-width:760px; margin:0 auto; background:#F4F6F8; }}
  a {{ text-decoration:none; color:inherit; pointer-events:none; }}
  details {{ open:true; }} details summary {{ list-style:none; }}
  details[open] > summary ~ * {{ display:block; }}
  section:first-of-type {{ break-before:auto; page-break-before:auto; }}
  @media print {{
    body {{ background:#fff; }}
    .doc {{ max-width:none; }}
    @page {{ margin:14mm; }}
  }}
</style></head>
<body><div class="doc">
<div style="padding:20px 14px 8px;">
  <div style="font-size:20px;font-weight:800;">ETF Discovery Report</div>
  <div style="{MUT}margin-top:4px;">{e(m.get("run_date", ""))} · single document for print</div>
</div>
{sections}
<div style="{CARD}break-inside:avoid;">
  <div style="{SEC_T}">Data basis</div>{foot}
  <div style="{MUT}margin-top:10px;line-height:1.6;">{e(m.get("disclaimer", ""))}</div>
</div>
<div style="height:24px;"></div>
</div></body></html>""")


render_index()
for pg in P["etf_pages"]:
    render_etf(pg)
render_compare()
render_report()
print("generated:", sorted(os.listdir(OUT)))
