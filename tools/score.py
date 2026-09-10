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
import unicodedata
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

# A weight that moves with the state instead of staying constant. One case so
# far: valuation matters little while a company earns and a great deal once it
# stops. 30 is the smallest weight that keeps a loss-making name out of the 🟠
# band on a perfect chart — a name scoring 80 on everything else lands at 58.9.
# Any lower and "profitable" and "loss-making" read alike.
#
# Read it as a condition, not a curve. Every added condition costs
# explainability, and a rule nobody can state in one sentence is overfitting in
# a good suit. One condition, plainly stated, is the budget.
LOSS_VALUE_WEIGHT = 30


def light(v):
    return next(sym for lo, sym in BANDS if v >= lo)


def pad(s, width):
    """Pad to a terminal *column* count. CJK characters occupy two columns, so an
    f-string width leaves any table containing them ragged."""
    w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)
    return s + " " * max(0, width - w)


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
    """Volume trend: last 20 sessions against the 40 before them.

    Five bands like every other indicator. It used to have one threshold and
    two outcomes, which meant it returned the same value for six funds whose
    ratios ran from 0.55 to 1.00 — a whole indicator saying nothing.

    This is a weak proxy for flows either way: it sees participation, not who
    is buying. Where put/call or investor-type data exists, quote that in the
    judgment and say the score rests on the proxy.
    """
    r = t["vol_ratio"]
    return 100 if r > 1.3 else 75 if r > 1.05 else 50 if r > 0.85 else 25 if r > 0.65 else 0


def score_value(symbol, sub_sector=None):
    """P/E against its sub-sector band. Returns None when not judgeable."""
    band = PE_BANDS.get(sub_sector) if sub_sector else None
    if sub_sector == "miner":
        return 50  # cyclical: P/E is misleading, judge on P/B and cost curve
    try:
        pe = ratios_pe(symbol)
    except Exception:
        return None
    # No P/E data is not the same as a bad P/E. FMP's ratios-ttm returns an
    # empty object for every ETF, so scoring that 0 silently docked every fund
    # 15 points at the long horizon. Missing stays missing.
    if pe is None:
        return None
    if pe < 0:
        return 0        # genuinely lossmaking — a real signal, not a gap
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


def dynamic_weights(parts, w):
    """Adjust weights for the state before scoring. Returns (weights, note)."""
    if parts.get("value") != 0 or not w.get("value"):
        return w, None
    rest = sum(v for k, v in w.items() if k != "value")
    if not rest:
        return w, None
    keep = sum(w.values()) - LOSS_VALUE_WEIGHT
    scale = keep / rest
    w = {k: (LOSS_VALUE_WEIGHT if k == "value" else v * scale) for k, v in w.items()}
    return w, (f"loss-making: valuation weighted {LOSS_VALUE_WEIGHT}%, "
               f"the rest scaled down to match")


def score_holding(symbol, horizon, bench_20d, sub_sector=None):
    """Score one constituent the same way the fund itself is scored, minus macro.

    Macro is the one hand-supplied input and there is no way to enter one per
    holding, so it is dropped and the rest renormalised. Valuation stays in: it
    comes from the provider, and leaving it out is what let a loss-making name
    show a top-band colour on chart strength alone.

    Returns (total, parts, technicals, coverage%) or None when the symbol has no
    price history — cash, T-bills and swap legs all appear in ETF holdings.
    """
    t = technicals(symbol, bench_20d, 65)
    parts = {
        "value": score_value(symbol, sub_sector),
        "trend": score_trend(t),
        "momentum": score_momentum(t),
        "position": score_position(t, horizon),
        "rs": score_rs(t),
        "flow": score_flow(t),
    }
    w, _ = dynamic_weights(parts, {k: v for k, v in WEIGHTS[horizon].items()
                                   if k != "macro"})
    have = [k for k in w if w[k] and parts[k] is not None]
    cov = sum(w[k] for k in have)
    total = sum(parts[k] * w[k] for k in have) / cov if cov else None
    return total, parts, t, round(100 * cov / sum(w.values()))


def score(symbol, horizon="swing", macro=None, sub_sector=None, benchmark="SPY"):
    b = data.prices(benchmark, 30)
    bench_20d = 100 * (b[0]["close"] / b[20]["close"] - 1)
    t = technicals(symbol, bench_20d)
    parts = {
        # Supplied by the caller. None when nobody judged it, and then it is
        # excluded like any other gap rather than filled with a neutral 50 —
        # otherwise an unassessed macro reads as an assessed one.
        "macro": macro,
        "value": score_value(symbol, sub_sector),
        "trend": score_trend(t),
        "momentum": score_momentum(t),
        "position": score_position(t, horizon),
        "rs": score_rs(t),
        "flow": score_flow(t),
    }
    w, note = dynamic_weights(parts, WEIGHTS[horizon])
    # Renormalise over the indicators that actually have data, the way
    # weighted_grade.py does. Never substitute a number for a gap.
    have = [k for k in w if w[k] and parts[k] is not None]
    cov = sum(w[k] for k in have)
    total = sum(parts[k] * w[k] for k in have) / cov if cov else None
    return total, parts, w, t, round(cov), note


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol")
    ap.add_argument("--horizon", default="swing", choices=list(WEIGHTS))
    ap.add_argument("--benchmark", default="SPY",
                    help="SPY for US, 069500.KS for Korea")
    ap.add_argument("--macro", type=int, default=None,
                    help="0-100, judged by hand. Omit it and macro is EXCLUDED, not "
                         "assumed neutral — pass --macro 50 to say neutral on purpose. "
                         "The same event flips sign by sector: a rising oil price is "
                         "negative for semis (via rates) and positive for nuclear and "
                         "lithium. For a refiner the dominant variable is the crack "
                         "spread, which tools/structure.py --eia reports.")
    ap.add_argument("--sub-sector", choices=list(PE_BANDS), default=None)
    ap.add_argument("--holdings", action="store_true",
                    help="also score the ETF's top constituents")
    a = ap.parse_args()

    total, parts, w, t, cov, note = score(a.symbol, a.horizon, a.macro,
                                          a.sub_sector, a.benchmark)
    print(f"\n{a.symbol}  {t['date']}  {t['close']:,.2f} ({t['chg']:+.2f}%)")
    if total is None or cov < 60:
        print(f"⚪ {a.horizon} score suspended — only {cov}% of weight has data\n")
    else:
        cover = "" if cov == 100 else f"  ({cov}% of weight has data)"
        print(f"{light(total)} {a.horizon} score {total:.1f}/100{cover}\n")
        if note:
            print(f"  ! {note}\n")
    for k in w:
        if not w[k]:
            continue
        if parts[k] is None:
            print(f"  {k:9}   n/a  (weight {w[k]:>4.1f}%) -> excluded, renormalised")
        else:
            print(f"  {k:9} {parts[k]:>5.0f} pt  (weight {w[k]:>4.1f}%) -> "
                  f"{parts[k]*w[k]/cov*100/100:>5.2f}  {light(parts[k])}")
    if a.macro is None:
        print("\n  macro not assessed — excluded, not scored 50. Name the sector's "
              "dominant variable and pass --macro, or say so in the judgment.")
    print(f"\n  ma20 {t['ma20']:,.2f} / ma60 {t['ma60']:,.2f} / ma200 {t['ma200']:,.2f}")
    print(f"  20d {t['d20']:+.1f}%  rs {t['rs']:+.1f}pp  pos60 {t['pos60']:.0f}%  "
          f"from-high {t['from_high']:+.1f}%  vol {t['vol_ratio']:.2f}x")

    if a.holdings:
        hs = data.holdings(a.symbol)
        if not hs:
            print("\n  (no holdings from FMP — Korean ETFs are not covered; "
                  "pull the issuer's official PDF instead)")
            return
        print(f"\n  Top constituents ({len(hs)} total) — colour is the score, not a guess:")
        print(f"    {'weight':>7} {'':2} {'ticker':<12}{'today':>8}{'20d':>8}"
              f"{'pos':>6}{'trend':>7}{'score':>7}  note")
        b = data.prices(a.benchmark, 30)
        bench_20d = 100 * (b[0]["close"] / b[20]["close"] - 1)
        rising = seen = 0.0
        for h in hs[:10]:
            sym = str(h.get("asset") or h.get("symbol"))
            wt = h.get("weightPercentage") or 0
            try:
                total, parts, ht, cov = score_holding(sym, a.horizon, bench_20d,
                                                      a.sub_sector)
            except Exception:
                print(f"    {wt:>6.2f}% {'':2} {sym:<12}"
                      f"{'':>29}  no price history (cash, bond or swap leg)")
                continue
            up = ht["ma20"] > ht["ma60"]
            rising += wt * up
            seen += wt
            note = "loss-making" if parts["value"] == 0 else \
                   f"no P/E ({cov}% cov)" if parts["value"] is None else ""
            print(f"    {wt:>6.2f}% {light(total)} {sym:<12}{ht['chg']:>+7.2f}%"
                  f"{ht['d20']:>+7.1f}%{ht['pos60']:>5.0f}%"
                  f"{'up' if up else 'down':>7}{total:>7.0f}  {note}")
            time.sleep(0.2)
        if seen:
            print(f"    -> {rising:.1f}% of the weight is in an uptrend "
                  f"(breadth: this is what separates a real move from a bounce)")


def demo():
    """Self-check: a missing indicator must be excluded and renormalised,
    never substituted with a number."""
    w = WEIGHTS["long"]
    parts = {k: 50 for k in w}
    have = [k for k in w if w[k] and parts[k] is not None]
    assert sum(parts[k] * w[k] for k in have) / sum(w[k] for k in have) == 50

    parts["value"] = None                      # the ETF case
    have = [k for k in w if w[k] and parts[k] is not None]
    cov = sum(w[k] for k in have)
    assert cov == 85, cov
    # all remaining indicators are 50, so the renormalised total is still 50 —
    # a gap must not drag the score the way scoring it 0 used to
    assert sum(parts[k] * w[k] for k in have) / cov == 50

    assert score_value("X", "miner") == 50, "cyclicals skip the P/E"
    assert PE_BANDS["memory"] == (8, 15)

    # every indicator must be able to return more than two values, or it is
    # carrying weight while saying nothing
    flows = {score_flow({"vol_ratio": r}) for r in (0.4, 0.7, 0.9, 1.1, 1.5)}
    assert len(flows) == 5, flows
    # A constituent drops macro and renormalises over what is left. Valuation
    # stays in — excluding it is what let a loss-making name show a top band.
    w = {k: v for k, v in WEIGHTS["swing"].items() if k != "macro"}
    assert "macro" not in w and w["value"] == 5
    full = sum(w.values())
    assert round(100 * (full - w["value"]) / full) == 94, "coverage when P/E is missing"
    # A loss scores 0, which is a real signal; no data is excluded instead
    assert score_value("__nonexistent__") is None
    # An unassessed macro is excluded, never filled with a neutral 50
    w = WEIGHTS["swing"]
    parts = {k: 50 for k in w}
    parts["macro"] = None
    have = [k for k in w if w[k] and parts[k] is not None]
    assert sum(w[k] for k in have) == 90, "macro must drop out of the coverage"
    assert sum(parts[k] * w[k] for k in have) / 90 == 50
    # A loss lifts the valuation weight; the rest scale down to preserve the sum
    w2, note = dynamic_weights({"value": 0}, WEIGHTS["swing"])
    assert w2["value"] == LOSS_VALUE_WEIGHT and note
    assert abs(sum(w2.values()) - 100) < 1e-9, "weights must still sum to 100"
    # Perfect on everything else but loss-making must not reach the orange band
    p2 = {k: 100 for k in WEIGHTS["swing"]}
    p2["value"], p2["position"] = 0, 25
    w3, _ = dynamic_weights(p2, WEIGHTS["swing"])
    got = sum(p2[k] * w3[k] for k in w3) / sum(w3.values())
    assert 55 < got < 60, f"a loss-maker should land below orange, got {got:.1f}"
    assert dynamic_weights({"value": 75}, WEIGHTS["swing"])[1] is None
    print("ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        demo()
    else:
        data.load_env()
        main()
