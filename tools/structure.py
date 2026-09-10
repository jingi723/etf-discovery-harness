"""Industry structure -- putting an unresolved imbalance into numbers.

This is the layer between the score (a diagnosis) and the event. Structure sets an
event's **sign** (which way the imbalance points) and its **tension** (how soon it
must resolve). See the "Tension" section of docs/EVENT_STRUCTURE.md.

    python3 tools/structure.py MU ALB SQM        # structure per ticker
    python3 tools/structure.py --etf LIT         # an ETF's top holdings
    python3 tools/structure.py --fred            # capacity utilisation (free, no key)
    python3 tools/structure.py --eia             # US oil and gas inventories (primary source)
    python3 tools/structure.py --self-check

Only what financial statements report. Channel and customer inventories ("memory
is down to 10 days") and spot prices are not disclosed and will not appear here --
those come from earnings calls and broker notes, by hand. The two measure
**different layers and must not be mixed.**
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data
from score import pad

QUARTER_DAYS = 91.25

# Free, no API key. fredgraph.csv is a public endpoint.
FRED = {
    "CAPUTLG3344S": "semiconductor & electronics utilisation",
    "MCUMFN": "manufacturing utilisation",
    "IPG3344S": "semiconductor production index",
}


def fred(series):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    with urllib.request.urlopen(url, timeout=20) as r:
        rows = r.read().decode().strip().splitlines()[1:]
    out = []
    for ln in rows:
        d, v = ln.split(",", 1)
        try:
            out.append((d, float(v)))
        except ValueError:                       # FRED marks missing values with "."
            continue
    return out


# EIA weekly data, no API key. Check a commodity theme's buffer against the primary source.
EIA_PETROLEUM = "https://ir.eia.gov/wpsr/table4.csv"
EIA_DEMAND = "https://ir.eia.gov/wpsr/table9.csv"
EIA_DEMAND_ROWS = ["Total Product Supplied", "Finished Motor Gasoline",
                   "Distillate Fuel Oil", "Kerosene-Type Jet Fuel"]
EIA_CRUDE_PX = "https://ir.eia.gov/wpsr/table11.csv"
EIA_PROD_PX = "https://ir.eia.gov/wpsr/table12.csv"
EIA_GAS = "https://ir.eia.gov/ngs/wngsr.txt"
EIA_ROWS = ["Commercial (Excluding SPR)", "Cushing", "SPR",
            "Total Motor Gasoline", "Distillate Fuel Oil", "Kerosene-Type Jet Fuel"]

# Colours are set by a band, never chosen by eye. Korean market convention: red is
# the strong end. For inventories, a bigger year-on-year fall means tighter supply
# (better for the producer), so a fall reads red.
STOCK_BANDS = [(-15, "🔴"), (-8, "🟠"), (8, "🟡"), (15, "🟢"), (999, "🔵")]
# Crack: banded against a normal $20-40. This is a margin level, not a buy signal.
CRACK_BANDS = [(60, "🔴"), (40, "🟠"), (20, "🟡"), (10, "🟢"), (0, "🔵")]



def stock_light(pct):
    return next(s for lo, s in STOCK_BANDS if pct <= lo)


def crack_light(v):
    return next(s for lo, s in CRACK_BANDS if v >= lo)


def _eia_rows(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return [[x.strip('"') for x in ln.split('","')]
                for ln in r.read().decode("latin-1").strip().splitlines()]


def _daily(url, want):
    """Pull (dates, series) from the daily block at the foot of a table."""
    rs = _eia_rows(url)
    heads = [i for i, p in enumerate(rs) if p and p[0] == "STUB_1"]
    if len(heads) < 2:
        return [], {}
    i = heads[-1]
    dates = [d for d in rs[i][3:] if d.strip()]
    out = {}
    for p in rs[i + 1:]:
        if not p or p[0] == "STUB_1":
            break
        label = " ".join(x for x in p[:3] if x.strip())
        if not any(w in label for w in want):
            continue
        vals = []
        for v in p[3:3 + len(dates)]:
            try:
                vals.append(float(v))
            except ValueError:
                vals.append(None)
        out[label] = vals
    return dates, out


def crack():
    """3-2-1 crack spread -- the one number to watch on a refining theme.

    Three barrels of crude yield two of gasoline and one of distillate; this is the
    margin per barrel. Product prices are per gallon, hence the 42. A normal range
    is $20-40 per barrel.
    """
    # Labels are the three STUB columns joined by spaces, so match on a substring
    d1, crude = _daily(EIA_CRUDE_PX, ["WTI - Cushing"])
    _, prod = _daily(EIA_CRUDE_PX, ["Motor Gasoline"])
    _, dist = _daily(EIA_PROD_PX, ["Ultra-Low Sulfur"])
    pick = lambda d: next((v for k, v in d.items() if "Gulf Coast" in k), None)
    prod = {"gas": pick(prod)} if pick(prod) else {}
    dist = {"ulsd": pick(dist)} if pick(dist) else {}
    if not (crude and prod and dist):
        print("crack: series not found -- check whether the EIA table layout changed")
        return
    wti = list(crude.values())[0]
    gas = list(prod.values())[0]
    ulsd = list(dist.values())[0]
    print("\n[3-2-1 crack spread] Gulf Coast, per barrel -- normal range $20-40")
    print(f"     {'date':<10}{'WTI':>8}{'gasoline':>10}{'diesel':>9}{'crack':>9}{'chg':>8}")
    cracks = []
    n = min(len(wti), len(gas), len(ulsd), len(d1))
    shown = [i for i in range(n) if None not in (wti[i], gas[i], ulsd[i])]
    for i in shown[-8:]:
        c = (2 * gas[i] + ulsd[i]) * 42 / 3 - wti[i]
        prev = cracks[-1] if cracks else c
        cracks.append(c)
        print(f"  {crack_light(c)} {pad(d1[i], 10)}{wti[i]:>8.2f}"
              f"{gas[i]:>9.3f}{ulsd[i]:>8.3f}{c:>9.2f}{c - prev:>+8.2f}")


def demand():
    """US domestic petroleum demand -- EIA product supplied (thousand b/d).

    Domestic consumption, exports excluded. The weekly figure is a residual and
    jumps around, so read the **four-week average**. Inventories alone cannot tell
    you whether stocks are drawing because demand fell or because supply is short.
    """
    rs = _eia_rows(EIA_DEMAND)
    print("\n[US domestic demand] product supplied, thousand b/d -- exports excluded")
    print(f"     {'':26}{'week':>9}{'yr ago':>9}{'YoY':>8}   {'4wk avg':>9}{'yr ago':>9}{'YoY':>8}")
    for p in rs:
        if not p or "Product Supplied" not in p[0]:
            continue
        name = p[1].strip()
        if name not in EIA_DEMAND_ROWS:
            continue
        try:
            wk, wk_y = float(p[2].replace(",", "")), float(p[4].replace(",", ""))
            m4, m4_y = float(p[6].replace(",", "")), float(p[7].replace(",", ""))
        except (ValueError, IndexError):
            continue
        pct4 = 100 * (m4 / m4_y - 1)
        print(f"  {stock_light(pct4)} {pad(name, 26)}{wk:>9,.0f}{wk_y:>9,.0f}"
              f"{100*(wk/wk_y-1):>+7.1f}%   {m4:>9,.0f}{m4_y:>9,.0f}{pct4:>+7.1f}%")


def eia():
    """US petroleum inventories (weekly, million barrels) and gas storage (Bcf)."""
    with urllib.request.urlopen(EIA_PETROLEUM, timeout=20) as r:
        rows = [ln.split('","') for ln in r.read().decode().strip().splitlines()]
    hdr = [c.strip('"') for c in rows[0]]
    print(f"[US petroleum inventories] EIA weekly, week ending {hdr[1]}, million bbl")
    print(f"     {'':28}{'now':>10}{'wk chg':>9}{'yr ago':>10}{'YoY':>8}")
    for r0 in rows[1:]:
        name = r0[0].strip('"')
        if name not in EIA_ROWS:
            continue
        cur, prev, diff, yr, pct = (float(r0[i].strip('"')) for i in (1, 2, 3, 4, 5))
        print(f"  {stock_light(pct)} {pad(name, 28)}{cur:>10,.1f}"
              f"{diff:>+9.1f}{yr:>10,.1f}{pct:>+7.1f}%")
    with urllib.request.urlopen(EIA_GAS, timeout=20) as r:
        g = r.read().decode("utf-8-sig").strip().splitlines()
    print("\n[US natural gas storage] EIA weekly")
    for ln in g:
        if ln.strip():
            print(f"  {ln.strip()}")


def quarters(symbol, n=8):
    """Quarterly structure metrics. Empty list when no statements are available."""
    bs = data.fmp("balance-sheet-statement", symbol=symbol, period="quarter", limit=n)
    ins = data.fmp("income-statement", symbol=symbol, period="quarter", limit=n)
    if not bs or not ins:
        return []
    inc = {r["date"]: r for r in ins}
    out = []
    for b in bs:
        i = inc.get(b["date"])
        if not i:
            continue
        inv, cogs, rev = b.get("inventory"), i.get("costOfRevenue"), i.get("revenue")
        if not (inv and cogs and rev):
            continue
        out.append({
            "date": b["date"], "revenue": rev,
            "dio": inv / (cogs / QUARTER_DAYS),   # days inventory outstanding
            "turns": 365 / (inv / (cogs / QUARTER_DAYS)),
            "gm": 100 * (rev - cogs) / rev,
            "om": 100 * (i.get("operatingIncome") or 0) / rev,
        })
    return out


MARGIN_BAND = 5.0        # operating margin moving more than +/-5pp counts as expanding/shrinking


def tension(qs):
    """Tension -- read days-of-inventory together with margin expansion.

    Days of inventory alone flips sign during a price spike. Balance-sheet inventory
    is carried at cost, so a higher selling price inflates the same physical volume.
    In September 2026 memory, channel inventory was under 10 days (28-42 is normal)
    while Samsung's days-of-inventory *rose* from 87 to 125 -- and this tool called
    it "easing". Margin said the opposite: operating margin went 6.3% -> 52.2%,
    which is what happens when cost holds and price runs.

    So there are four states. When margin expands while days of inventory rise, the
    tool says the volume cannot be judged; it does not say easing.

    Returns dict(state, dio_per_q, margin_delta, quarters_left, floor, span)
      state — tight / passthrough / mixed / easing
    """
    if len(qs) < 5:
        return None
    cur, floor = qs[0]["dio"], min(q["dio"] for q in qs)
    dio_per_q = (qs[4]["dio"] - qs[0]["dio"]) / 4      # positive means falling
    margin_delta = qs[0]["om"] - qs[4]["om"]
    expanding = margin_delta > MARGIN_BAND
    shrinking = margin_delta < -MARGIN_BAND
    left = None
    if dio_per_q > 0:
        left = max(cur - floor, 0.0) / dio_per_q
        # Inventory falling without margin following may be weak demand rather than
        # tight supply. Genuine tightness lifts price, so margin expands with it.
        state = "tight" if expanding else "mixed"
    else:
        state = "passthrough" if expanding else "easing" if shrinking else "mixed"
    return {"state": state, "dio_per_q": dio_per_q, "margin_delta": margin_delta,
            "quarters_left": left, "floor": floor,
            "span": f"{qs[4]['date']} → {qs[0]['date']}"}


def show(symbol, label=None):
    try:
        qs = quarters(symbol)
    except Exception as e:
        print(f"\n[{label or symbol}]  failed: {str(e)[:50]}")
        return
    if not qs:
        print(f"\n[{label or symbol}]  no statements (Korean ETFs and some foreign names are uncovered)")
        return
    print(f"\n[{label or symbol}]")
    print(f"  {'quarter':<12}{'revenue':>10}{'YoY':>8}{'DIO':>7}{'gross':>9}{'op margin':>11}")
    for k, q in enumerate(qs[:6]):
        yoy = f"{100*(q['revenue']/qs[k+4]['revenue']-1):>+7.0f}%" if k + 4 < len(qs) else ""
        print(f"  {q['date']:<12}{q['revenue']/1e9:>9.2f}B{yoy:>8}"
              f"{q['dio']:>6.0f}d{q['gm']:>8.1f}%{q['om']:>10.1f}%")
    t = tension(qs)
    if t is None:
        print("  tension: not enough quarters")
        return
    m, d, span = t["margin_delta"], t["dio_per_q"], t["span"]
    if t["state"] == "tight":
        hot = "   <- high one-month hazard" if t["quarters_left"] <= 1.5 else ""
        print(f"  tension: TIGHT -- DIO falling {d:.0f}d per quarter, "
              f"{t['quarters_left']:.1f}q to the observed floor of {t['floor']:.0f}d. "
              f"Operating margin {m:+.1f}pp ({span}){hot}")
    elif t["state"] == "passthrough":
        print(f"  tension: UNDETERMINED -- operating margin {m:+.1f}pp while DIO "
              f"rises {-d:.0f}d per quarter ({span}).")
        print("        Inventory is carried at cost, so price masks volume. Check "
              "channel inventory separately   <- on margin alone, supplier's market")
    elif t["state"] == "easing":
        print(f"  tension: EASING -- DIO rising {-d:.0f}d per quarter, "
              f"operating margin {m:+.1f}pp ({span})")
    else:
        left = (f", {t['quarters_left']:.1f}q to the floor of {t['floor']:.0f}d"
                if t["quarters_left"] is not None else "")
        print(f"  tension: MIXED -- DIO {'-' if d > 0 else '+'}{abs(d):.0f}d/quarter{left}, "
              f"operating margin {m:+.1f}pp ({span})")
        if d > 0:
            print("        Inventory falls but margin does not follow -- weak demand "
                  "rather than tight supply")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbols", nargs="*")
    ap.add_argument("--etf", help="run over this ETF's top holdings")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--fred", action="store_true", help="industry capacity utilisation")
    ap.add_argument("--eia", action="store_true", help="US oil and gas inventories (primary source)")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()

    if a.self_check:
        return demo()

    data.load_env()
    if a.fred:
        for s, nm in FRED.items():
            try:
                rows = fred(s)
            except Exception as e:
                print(f"{nm:<22} failed: {str(e)[:40]}")
                continue
            last, prev = rows[-1], rows[-7] if len(rows) > 7 else rows[0]
            lo = min(v for _, v in rows[-60:])
            hi = max(v for _, v in rows[-60:])
            print(f"{pad(nm, 26)}{last[0]}  {last[1]:>7.1f}   "
                  f"6mo ago {prev[1]:>6.1f} ({last[1]-prev[1]:+.1f})   "
                  f"5y range {lo:.1f}-{hi:.1f}")
    if a.eia:
        eia()
        demand()
        crack()
    if a.etf:
        hs = data.holdings(a.etf) or []
        if not hs:
            print(f"{a.etf}: no holdings from FMP -- use the issuer PDF")
        for h in hs[:a.top]:
            sym = h.get("asset") or h.get("symbol")
            wt = h.get("weightPercentage") or 0
            show(sym, f"{sym}  ({wt:.2f}% weight)")
    for s in a.symbols:
        show(s)


def demo():
    """Self-check: each of the four states appears, and margin overrides DIO."""
    def mk(dios, oms=None):
        oms = oms or [10.0] * len(dios)
        return [{"date": f"q{i}", "revenue": 1e9, "dio": d, "turns": 365 / d,
                 "gm": 30.0, "om": o} for i, (d, o) in enumerate(zip(dios, oms))]

    # DIO falling + margin expanding = tight. Latest is first, so values grow backwards
    t = tension(mk([100, 110, 120, 130, 140], [60, 40, 30, 20, 10]))
    assert t["state"] == "tight", t
    assert t["dio_per_q"] == 10.0 and abs(t["quarters_left"]) < 1e-9, t

    # DIO rising + margin expanding = undetermined. September 2026 memory is this case
    t = tension(mk([125, 101, 93, 87, 95], [52, 43, 21, 14, 6]))
    assert t["state"] == "passthrough", t
    assert t["dio_per_q"] < 0 and t["margin_delta"] > MARGIN_BAND, t
    assert t["quarters_left"] is None, "undetermined must not report a quarter count"

    # DIO falling without margin following is not called tight
    t = tension(mk([100, 110, 120, 130, 140], [11, 10, 10, 10, 10]))
    assert t["state"] == "mixed", t
    assert t["quarters_left"] is not None, "mixed still computes the quarter count"

    # DIO rising + margin shrinking = easing
    assert tension(mk([120, 110, 105, 100, 95], [5, 10, 15, 20, 25]))["state"] == "easing"
    # margin inside the band folds into mixed
    assert tension(mk([120, 110, 105, 100, 95], [11, 10, 10, 10, 10]))["state"] == "mixed"
    assert tension(mk([100, 110])) is None                   # not enough quarters

    assert pad("\uac00\ub3d9\ub960", 10) == "\uac00\ub3d9\ub960" + " " * 4
    assert pad("a\uac00b", 10) == "a\uac00b" + " " * 6  # CJK counts as two columns
    assert stock_light(-20) == "🔴" and stock_light(0) == "🟡" and stock_light(20) == "🔵"
    assert crack_light(81) == "🔴" and crack_light(30) == "🟡" and crack_light(5) == "🔵"
    print("self-check ok")


if __name__ == "__main__":
    main()
