"""Seven-indicator scoring for an ETF or stock, across three time horizons.

Every indicator is scored 0-100 on its own, then weighted. The same seven
indicators are used for all horizons; only the weights and the measurement
windows change. That way two horizons are directly comparable and you can see
*which* indicator makes them disagree.

    python3 tools/score.py SOXX --horizon swing
    python3 tools/score.py LIT --holdings
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data

# weight profiles ------------------------------------------------------------
WEIGHTS = {
    # long: "is this worth owning at all"      (rebalance weekly)
    "long":  {"macro": 40, "value": 15, "trend": 15, "momentum": 5,
              "position": 15, "rs": 5, "flow": 5},
    # swing: "which way over the next month"   (the default)
    "swing": {"macro": 10, "value": 5, "trend": 25, "momentum": 20,
              "position": 20, "rs": 15, "flow": 5},
    # short: "leveraged ETF, 3-10 sessions"
    "short": {"macro": 5, "value": 0, "trend": 25, "momentum": 25,
              "position": 20, "rs": 15, "flow": 10},
}

# Sub-sector P/E bands. A single "tech is 20-40x" rule misprices half the
# sector, so bands are per sub-industry. Miners are excluded on purpose:
# for cyclicals the P/E is *lowest* at the earnings peak.
PE_BANDS = {
    "fabless": (20, 35), "foundry": (15, 25), "memory": (8, 15),
    "equipment": (25, 50), "utility": (15, 30), "ipp": (15, 30),
    "miner": None,
}

BANDS = [(80, "🔴"), (60, "🟠"), (40, "🟡"), (20, "🟢"), (0, "🔵")]


def light(v):
    return next(sym for lo, sym in BANDS if v >= lo)


def _sma(xs, n):
    return sum(xs[:n]) / n


def technicals(symbol, bench_20d, days=260):
    """Price-derived inputs shared by every indicator."""
    rows = data.prices(symbol, days)
    if len(rows) < 61:
        raise ValueError(f"{symbol}: only {len(rows)} sessions, need 61+")
    close = [r["close"] for r in rows]
    high = [r["high"] for r in rows]
    low = [r["low"] for r in rows]
    vol = [r["volume"] for r in rows]
    n200 = min(200, len(close))
    d20 = 100 * (close[0] / close[20] - 1)
    return {
        "date": rows[0]["date"], "close": close[0],
        "chg": 100 * (close[0] / close[1] - 1),
        "ma20": _sma(close, 20), "ma60": _sma(close, 60), "ma200": _sma(close, n200),
        "d20": d20, "rs": d20 - bench_20d,
        # where in the 60-day range we sit: low = more room above
        "pos60": 100 * (close[0] - min(low[:60])) / (max(high[:60]) - min(low[:60])),
        "range_all": 100 * (close[0] - min(close)) / (max(close) - min(close)),
        "from_high": 100 * (close[0] / max(high[:60]) - 1),
        # volume trend, not a single day: last 20 sessions vs the 40 before them
        "vol_ratio": (sum(vol[:20]) / 20) / (sum(vol[20:60]) / 40),
    }


def score_trend(t):
    if t["ma20"] > t["ma60"]:
        return 100 if t["close"] > t["ma20"] else 75
    return 25 if t["from_high"] > -30 else 0


def score_momentum(t):
    """Direction AND participation. Falling on rising volume is distribution."""
    if t["d20"] > 0:
        return 100 if t["vol_ratio"] > 1 else 75
    return 0 if t["vol_ratio"] > 1 else 40


def score_position(t, horizon):
    if horizon == "long":
        a = 100 if t["range_all"] <= 20 else 75 if t["range_all"] <= 40 else \
            50 if t["range_all"] <= 60 else 25 if t["range_all"] <= 80 else 0
        g = 100 * (t["close"] / t["ma200"] - 1)
        b = 100 if g <= -10 else 75 if g <= 0 else 50 if g <= 10 else 25 if g <= 25 else 0
        return (a + b) / 2
    p = t["pos60"]
    return 100 if p <= 25 else 75 if p <= 45 else 50 if p <= 65 else 25 if p <= 85 else 0


def score_rs(t):
    r = t["rs"]
    return 100 if r > 5 else 75 if r > 2 else 50 if r > -2 else 25 if r > -5 else 0


def score_flow(t):
    return 60 if t["vol_ratio"] > 0.9 else 40


def score_value(symbol, sub_sector=None):
    """P/E against its sub-sector band. Returns None when not judgeable."""
    band = PE_BANDS.get(sub_sector) if sub_sector else None
    if sub_sector == "miner":
        return 50  # cyclical: P/E is misleading, judge on P/B and cost curve
    try:
        pe = ratios_pe(symbol)
    except Exception:
        return None
    if pe is None or pe < 0:
        return 0
    if not band:
        return 75 if 15 <= pe <= 40 else 50 if pe <= 60 else 25 if pe <= 90 else 0
    lo, hi = band
    if pe < lo:
        return 100
    if pe <= hi:
        return 75
    return 50 if pe <= hi * 1.3 else 25 if pe <= hi * 2 else 0


def ratios_pe(symbol):
    r = data.ratios(symbol)
    pe = r.get("priceToEarningsRatioTTM")
    return float(pe) if pe is not None else None


def score(symbol, horizon="swing", macro=50, sub_sector=None, benchmark="SPY"):
    b = data.prices(benchmark, 30)
    bench_20d = 100 * (b[0]["close"] / b[20]["close"] - 1)
    t = technicals(symbol, bench_20d)
    v = score_value(symbol, sub_sector)
    parts = {
        "macro": macro,                      # supplied by the caller, see note
        "value": 50 if v is None else v,
        "trend": score_trend(t),
        "momentum": score_momentum(t),
        "position": score_position(t, horizon),
        "rs": score_rs(t),
        "flow": score_flow(t),
    }
    w = WEIGHTS[horizon]
    total = sum(parts[k] * w[k] for k in w) / 100
    return total, parts, w, t


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol")
    ap.add_argument("--horizon", default="swing", choices=list(WEIGHTS))
    ap.add_argument("--benchmark", default="SPY",
                    help="SPY for US, 069500.KS for Korea")
    ap.add_argument("--macro", type=int, default=50,
                    help="0-100, judged by hand. Same event flips sign by sector: "
                         "a rising oil price is negative for semis (via rates) "
                         "and positive for nuclear and lithium.")
    ap.add_argument("--sub-sector", choices=list(PE_BANDS), default=None)
    ap.add_argument("--holdings", action="store_true",
                    help="also score the ETF's top constituents")
    a = ap.parse_args()

    total, parts, w, t = score(a.symbol, a.horizon, a.macro, a.sub_sector, a.benchmark)
    print(f"\n{a.symbol}  {t['date']}  {t['close']:,.2f} ({t['chg']:+.2f}%)")
    print(f"{light(total)} {a.horizon} score {total:.1f}/100\n")
    for k in w:
        if w[k]:
            print(f"  {k:9} {parts[k]:>5.0f} pt  (weight {w[k]:>2}%) -> "
                  f"{parts[k]*w[k]/100:>5.2f}  {light(parts[k])}")
    print(f"\n  ma20 {t['ma20']:,.2f} / ma60 {t['ma60']:,.2f} / ma200 {t['ma200']:,.2f}")
    print(f"  20d {t['d20']:+.1f}%  rs {t['rs']:+.1f}pp  pos60 {t['pos60']:.0f}%  "
          f"from-high {t['from_high']:+.1f}%  vol {t['vol_ratio']:.2f}x")

    if a.holdings:
        hs = data.holdings(a.symbol)
        if not hs:
            print("\n  (no holdings from FMP — Korean ETFs are not covered; "
                  "pull the issuer's official PDF instead)")
            return
        print(f"\n  Top constituents ({len(hs)} total):")
        b = data.prices(a.benchmark, 30)
        bench_20d = 100 * (b[0]["close"] / b[20]["close"] - 1)
        rising = seen = 0
        for h in hs[:10]:
            sym = h.get("asset") or h.get("symbol")
            wt = h.get("weightPercentage") or 0
            try:
                ht = technicals(sym, bench_20d, 65)
            except Exception:
                print(f"    {str(sym):12}{wt:>6.2f}%   (no data)")
                continue
            up = ht["ma20"] > ht["ma60"]
            rising += up
            seen += 1
            print(f"    {str(sym):12}{wt:>6.2f}%  {ht['chg']:>+6.2f}%  "
                  f"20d {ht['d20']:>+6.1f}%  pos {ht['pos60']:>3.0f}%  "
                  f"{'up' if up else 'down':>4}")
            time.sleep(0.2)
        if seen:
            print(f"    -> {rising}/{seen} in an uptrend "
                  f"(breadth: this is what separates a real move from a bounce)")


if __name__ == "__main__":
    data.load_env()
    main()
