"""Measure what the indicators can and cannot do.

Every figure in docs/EVENT_STRUCTURE.md comes out of this script.

    python3 tools/eventstudy.py ic          # does the score forecast returns?
    python3 tools/eventstudy.py shock       # do indicators separate outcomes after a shock?
    python3 tools/eventstudy.py rate        # does structure foretell event frequency?
    python3 tools/eventstudy.py shift       # how does an event move the score?
    python3 tools/eventstudy.py all

An "event" here is a day whose return exceeds twice the trailing 60-day standard
deviation. That catches the move *after* the price has already gone, so it is a
marker, not a leading signal. Once a news log exists this should be redefined on
publication time (see "Limits" in EVENT_STRUCTURE.md).
"""
from __future__ import annotations

import argparse
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data
import score

# A default universe spread across sectors and themes. Measure semiconductors alone
# and you mistake one cycle for a general law.
UNIVERSE = ["SOXX", "SMH", "XLK", "QQQ", "XLE", "XLF", "XLV", "XLU", "IWM", "LIT",
            "KBE", "KRE", "XBI", "ITA", "URA", "TAN", "GLW", "XLRE", "XLP", "XLI"]
BENCH = "SPY"

# The five indicators of the one-month profile that can be reconstructed from price
# alone. Macro and valuation are hand-supplied, so no past date can be recovered;
# they are dropped and the remaining weights renormalised.
W = {"trend": 25, "momentum": 20, "position": 20, "rs": 15, "flow": 5}
WTOT = sum(W.values())
SHOCK_SIGMA = 2.0
FWD = 20


def corr(a, b):
    if len(a) < 2:
        return float("nan")
    ma, mb = st.mean(a), st.mean(b)
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / den if den else 0.0


def load(tickers, days=1300):
    out = {}
    for t in tickers:
        try:
            rows = data.prices(t, days)
        except Exception as e:                       # too short a history, or outside coverage
            print(f"  skipped {t}: {str(e)[:50]}", file=sys.stderr)
            continue
        if len(rows) > 260:
            out[t] = rows
    return out


def tech_at(rows, i):
    """Rebuild the indicators as of rows[i]. rows[0] is the latest bar, so rows[i:]
    holds only that day's past — no future data can leak in."""
    c = [r["close"] for r in rows[i:]]
    h = [r["high"] for r in rows[i:]]
    lo = [r["low"] for r in rows[i:]]
    v = [r["volume"] for r in rows[i:]]
    if len(c) < 210:
        return None
    rng = max(h[:60]) - min(lo[:60])
    span = max(c[:260]) - min(c[:260])
    if rng <= 0 or span <= 0:
        return None
    n200 = min(200, len(c))
    return {
        "d20": 100 * (c[0] / c[20] - 1),
        "m120": 100 * (c[0] / c[120] - 1),
        "ma20": sum(c[:20]) / 20, "ma60": sum(c[:60]) / 60,
        "ma200": sum(c[:n200]) / n200, "close": c[0],
        "pos60": 100 * (c[0] - min(lo[:60])) / rng,
        "range_all": 100 * (c[0] - min(c[:260])) / span,
        "from_high": 100 * (c[0] / max(h[:60]) - 1),
        "vol_ratio": (sum(v[:20]) / 20) / ((sum(v[20:60]) / 40) or 1),
        "ma200_gap": 100 * (c[0] / (sum(c[:n200]) / n200) - 1),
    }


def chart_score(t, bench_d20):
    t = dict(t)
    t["rs"] = t["d20"] - bench_d20
    parts = {
        "trend": score.score_trend(t),
        "momentum": score.score_momentum(t),
        "position": score.score_position(t, "swing"),
        "rs": score.score_rs(t),
        "flow": score.score_flow(t),
    }
    return sum(parts[k] * W[k] for k in W) / WTOT, parts


def sigma_at(rows, i, n=60):
    c = [r["close"] for r in rows]
    if i + n + 1 >= len(c):
        return 0.0
    return st.pstdev([100 * (c[k] / c[k + 1] - 1) for k in range(i + 1, i + n + 1)])


def sigma_series(rows, n=60):
    """Trailing n-day standard deviation at every point, in one pass. Calling
    sigma_at inside a loop recomputes the same window dozens of times and the
    rate mode never finishes."""
    c = [r["close"] for r in rows]
    ret = [100 * (c[k] / c[k + 1] - 1) for k in range(len(c) - 1)]
    out = [0.0] * len(c)
    for i in range(len(c)):
        w = ret[i + 1:i + 1 + n]
        out[i] = st.pstdev(w) if len(w) == n else 0.0
    return ret, out


def bench_frames(rows):
    """Benchmark 20-day trailing return (for rs) and 20-day forward return (for excess)."""
    c = {r["date"]: r["close"] for r in rows}
    d = sorted(c)
    back = {d[i]: 100 * (c[d[i]] / c[d[i - 20]] - 1) for i in range(20, len(d))}
    fwd = {d[i]: 100 * (c[d[i + FWD]] / c[d[i]] - 1) for i in range(len(d) - FWD)}
    return back, fwd


def quantiles(rows, key, n=5):
    rows = sorted(rows, key=lambda r: r[key])
    m = len(rows) // n
    return [rows[q * m:(q + 1) * m] if q < n - 1 else rows[(n - 1) * m:] for q in range(n)]


def band(v):
    return next(s for lo, s in score.BANDS if v >= lo)


# -- Measurement 1: does the score forecast returns? -------------------------
def run_ic(D, back, fwd):
    recs = []
    for t, rows in D.items():
        for i in range(FWD, len(rows) - 210):
            d = rows[i]["date"]
            if d not in back or d not in fwd:
                continue
            tt = tech_at(rows, i)
            if not tt:
                continue
            s, parts = chart_score(tt, back[d])
            f = 100 * (rows[i - FWD]["close"] / rows[i]["close"] - 1)
            recs.append({"s": s, "p": parts, "f": f, "e": f - fwd[d], "raw": tt})
    print(f"{len(recs):,} observations\n")

    print("1. One-month score -> 20-session forward return")
    print(f"  {'band':<10}{'n':>7}{'mean':>9}{'median':>9}{'win':>8}")
    for lo, hi in ((80, 101), (60, 80), (40, 60), (20, 40), (0, 20)):
        g = [r["f"] for r in recs if lo <= r["s"] < hi]
        if not g:
            continue
        print(f"  {band(lo):<9}{len(g):>7,}{st.mean(g):>+9.2f}{st.median(g):>+9.2f}"
              f"{100 * sum(1 for x in g if x > 0) / len(g):>7.1f}%")
    allf = [r["f"] for r in recs]
    print(f"  {'all':<9}{len(allf):>7,}{st.mean(allf):>+9.2f}{st.median(allf):>+9.2f}"
          f"{100 * sum(1 for x in allf if x > 0) / len(allf):>7.1f}%")
    print(f"\n  IC (score vs forward return) = {corr([r['s'] for r in recs], [r['f'] for r in recs]):+.4f}")

    print("\n2. IC per indicator (against forward excess return)")
    for k in W:
        v = corr([r["p"][k] for r in recs], [r["e"] for r in recs])
        print(f"  {k:<12}{v:>+8.3f}")

    print("\n3. Raw momentum IC by lookback -- before banding")
    for k, nm in (("d20", "20-day return"), ("m120", "120-day return")):
        v = corr([r["raw"][k] for r in recs], [r["e"] for r in recs])
        print(f"  {nm:<12}{v:>+8.3f}")
    print("\n  -> banding costs signal: compare raw 20-day against the momentum score")


# -- Measurement 2: do indicators separate outcomes after a shock? -----------
def collect_shocks(D, back, fwd):
    ev = []
    for t, rows in D.items():
        c = [r["close"] for r in rows]
        for i in range(FWD, len(rows) - 215):
            d = rows[i]["date"]
            if d not in back or d not in fwd:
                continue
            sig = sigma_at(rows, i)
            if sig == 0:
                continue
            r0 = 100 * (c[i] / c[i + 1] - 1)
            if abs(r0) < SHOCK_SIGMA * sig:
                continue
            pre = tech_at(rows, i + 1)                # state the day *before* the shock
            post = tech_at(rows, i)
            dpre = rows[i + 1]["date"]
            if not pre or not post or dpre not in back:
                continue
            s0, p0 = chart_score(pre, back[dpre])
            s1, p1 = chart_score(post, back[d])
            ev.append({"t": t, "d": d, "dir": 1 if r0 > 0 else -1, "shock": r0 / sig,
                       "s0": s0, "s1": s1, "p0": p0, "p1": p1,
                       "pos60": pre["pos60"], "m120": pre["m120"],
                       "e": 100 * (c[i - FWD] / c[i] - 1) - fwd[d]})
    return ev


def run_shock(ev):
    print(f"{len(ev):,} shocks (|daily return| > {SHOCK_SIGMA} sigma)\n")
    for dr, nm in ((1, "Up-shock"), (-1, "Down-shock")):
        g = [e for e in ev if e["dir"] == dr]
        v = [e["e"] for e in g]
        print(f"[{nm}]  n={len(g):,}  next-20d excess {st.mean(v):+.2f}pp  "
              f"win {100 * sum(1 for x in v if x > 0) / len(v):.0f}%")
        for key, label in (("m120", "120-day momentum before the shock"), ("pos60", "60-day range position before the shock")):
            qs = quantiles(g, key, 4)
            print(f"    {label}")
            for i, b in enumerate(qs):
                vv = [r["e"] for r in b]
                print(f"      Q{i + 1} ({b[0][key]:+7.1f}~{b[-1][key]:+7.1f})  n={len(vv):<4} "
                      f"excess {st.mean(vv):+6.2f}pp  win {100 * sum(1 for x in vv if x > 0) / len(vv):.0f}%")
            sp = st.mean([r["e"] for r in qs[-1]]) - st.mean([r["e"] for r in qs[0]])
            print(f"      Q4-Q1 spread {sp:+.2f}pp")
        print()


# -- Measurement 3: does structure foretell event frequency? -----------------
def run_rate(D, back):
    recs = []
    for t, rows in D.items():
        ret, sig = sigma_series(rows)
        for i in range(FWD + 1, len(rows) - 215):
            d = rows[i]["date"]
            if d not in back:
                continue
            tt = tech_at(rows, i)
            if not tt:
                continue
            up = dn = 0
            for k in range(i - FWD, i):               # the next 20 sessions
                if sig[k] == 0:
                    continue
                if ret[k] > SHOCK_SIGMA * sig[k]:
                    up += 1
                elif ret[k] < -SHOCK_SIGMA * sig[k]:
                    dn += 1
            recs.append({"up": up, "dn": dn, "net": up - dn, "tot": up + dn, **tt})
    print(f"{len(recs):,} observations")
    print(f"average shocks in the next 20 days: up {st.mean([r['up'] for r in recs]):.2f}  "
          f"down {st.mean([r['dn'] for r in recs]):.2f}\n")
    for key, label in (("m120", "120-day momentum"), ("pos60", "60-day range position"),
                       ("vol_ratio", "volume trend (20/40)"), ("ma200_gap", "gap to the 200-day")):
        print(f"■ {label}")
        print(f"  {'':22}{'up':>8}{'down':>8}{'net':>11}{'total':>8}")
        qs = quantiles(recs, key)
        for i, b in enumerate(qs):
            print(f"  Q{i + 1} ({b[0][key]:+7.1f}~{b[-1][key]:+7.1f}) "
                  f"{st.mean([r['up'] for r in b]):>7.2f}{st.mean([r['dn'] for r in b]):>8.2f}"
                  f"{st.mean([r['net'] for r in b]):>11.2f}{st.mean([r['tot'] for r in b]):>8.2f}")
        sp = st.mean([r["net"] for r in qs[-1]]) - st.mean([r["net"] for r in qs[0]])
        print(f"  Q5-Q1 net-shock spread {sp:+.2f}\n")


# -- Measurement 4: how does an event move the score? ------------------------
def run_shift(ev):
    up = [e for e in ev if e["dir"] == 1]
    print(f"{len(up):,} up-shocks\n")
    print(f"total score {st.mean([e['s0'] for e in up]):.1f} -> {st.mean([e['s1'] for e in up]):.1f}"
          f"   change {st.mean([e['s1'] - e['s0'] for e in up]):+.1f}")
    print(f"fell in {100 * sum(1 for e in up if e['s1'] < e['s0']) / len(up):.0f}% of cases\n")
    print("mean change per indicator:")
    for k in W:
        print(f"  {k:<10}{st.mean([e['p0'][k] for e in up]):>6.1f} → "
              f"{st.mean([e['p1'][k] for e in up]):>6.1f}"
              f"   {st.mean([e['p1'][k] - e['p0'][k] for e in up]):>+7.1f}")
    dn = [e for e in up if e["s1"] < e["s0"]]
    keep = [e for e in up if e["s1"] >= e["s0"]]
    print("\nwere the score drops actually worse? (next-20d excess return)")
    for g, nm in ((dn, "score fell"), (keep, "score held or rose")):
        v = [e["e"] for e in g]
        print(f"  {nm:<12} n={len(v):<5} {st.mean(v):+.2f}%p  "
              f"win {100 * sum(1 for x in v if x > 0) / len(v):.0f}%")


def demo():
    """Self-check: no future data leaks in, and the quantile split loses nothing."""
    rows = [{"date": f"d{i:04d}", "close": 100 + i, "high": 101 + i,
             "low": 99 + i, "volume": 1000} for i in range(300)][::-1]
    a = tech_at(rows, 50)
    rows[0]["close"] = 9e9                            # poisoning the latest bar
    assert tech_at(rows, 50) == a, "future data leaked into a past-dated indicator"
    qs = quantiles([{"x": i} for i in range(103)], "x", 5)
    assert sum(len(q) for q in qs) == 103, "the quantile split dropped observations"
    assert all(q[0]["x"] <= q[-1]["x"] for q in qs), "quantiles are not ordered"
    print("self-check ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["ic", "shock", "rate", "shift", "all", "self-check"])
    ap.add_argument("--tickers", help="comma separated; defaults to a 20-ticker mixed universe")
    args = ap.parse_args()

    if args.mode == "self-check":
        return demo()

    data.load_env()
    tick = args.tickers.split(",") if args.tickers else UNIVERSE
    D = load(tick)
    B = load([BENCH])[BENCH]
    back, fwd = bench_frames(B)
    print(f"universe {len(D)} tickers / benchmark {BENCH}\n")

    if args.mode in ("ic", "all"):
        print("═" * 62 + "\nDoes the score forecast returns?\n" + "═" * 62)
        run_ic(D, back, fwd)
    if args.mode in ("shock", "shift", "all"):
        ev = collect_shocks(D, back, fwd)
    if args.mode in ("shock", "all"):
        print("\n" + "═" * 62 + "\nDo indicators separate outcomes after a shock?\n" + "═" * 62)
        run_shock(ev)
    if args.mode in ("rate", "all"):
        print("\n" + "═" * 62 + "\nDoes structure foretell event frequency?\n" + "═" * 62)
        run_rate(D, back)
    if args.mode in ("shift", "all"):
        print("\n" + "═" * 62 + "\nHow does an event move the score?\n" + "═" * 62)
        run_shift(ev)


if __name__ == "__main__":
    main()
