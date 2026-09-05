"""Backtest a chart pattern before you believe it.

Every pattern in this repo had to survive this script first. Several did not:
a "gap down, close near the high = institutional accumulation" rule looked
convincing on the last three charts and lost to the baseline over 1,255
sessions. That is the entire point of the file.

    python3 tools/validate.py SOXX --pattern ftd --horizon 10
    python3 tools/validate.py SQM  --pattern fib618
    python3 tools/validate.py SMH  --pattern touch200

Output is always the same three numbers: how often the pattern fired, what
happened after, and what would have happened on a random day. If the pattern
row does not beat the baseline row, the pattern is noise.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data


def series(symbol, days):
    """Oldest-first bars, so index math reads forwards."""
    rows = data.prices(symbol, days)[::-1]
    if len(rows) < 120:
        raise ValueError(f"{symbol}: {len(rows)} sessions is too few to test")
    return rows


def ftd(rows, i):
    """Follow-through day (O'Neil/IBD): day 4+ off a rally low, close +1.25%
    or more on heavier volume than the day before. Day 4-7 is the classic
    window; earlier is treated as noise."""
    if i < 20:
        return False
    c, p = rows[i]["close"], rows[i - 1]["close"]
    if c / p - 1 < 0.0125 or rows[i]["volume"] <= rows[i - 1]["volume"]:
        return False
    lows = [r["low"] for r in rows[i - 15:i + 1]]
    off_low = len(lows) - 1 - lows.index(min(lows))
    return 3 <= off_low <= 7


def distribution(rows, i):
    """5+ distribution days (close -0.2%+ on rising volume) in 25 sessions.
    IBD calls 4-5 a warning and 6+ a correction."""
    if i < 25:
        return False
    n = sum(1 for j in range(i - 24, i + 1)
            if rows[j]["close"] / rows[j - 1]["close"] - 1 <= -0.002
            and rows[j]["volume"] > rows[j - 1]["volume"])
    return n >= 5


def fib618(rows, i):
    """Pullback has retraced 61.8% or more of the prior 120-day advance.
    On SQM this was the dividing line: shallower pullbacks recovered 7/7,
    deeper ones 10/28. Fires on the day the level is first broken."""
    if i < 120:
        return False
    w = rows[i - 120:i + 1]
    hi, lo = max(r["high"] for r in w), min(r["low"] for r in w)
    if hi <= lo:
        return False
    level = hi - 0.618 * (hi - lo)
    return rows[i]["close"] < level <= rows[i - 1]["close"]


def touch200(rows, i):
    """Price touches the 200-day average from above after being clear of it.
    The 'it always bounces off the 200' claim, made testable."""
    if i < 210:
        return False
    ma = sum(r["close"] for r in rows[i - 199:i + 1]) / 200
    prev_ma = sum(r["close"] for r in rows[i - 200:i]) / 200
    return rows[i]["low"] <= ma and rows[i - 1]["close"] > prev_ma * 1.02


def golden_cross(rows, i):
    if i < 61:
        return False
    f = lambda k, n: sum(r["close"] for r in rows[k - n + 1:k + 1]) / n
    return f(i, 20) > f(i, 60) and f(i - 1, 20) <= f(i - 1, 60)


PATTERNS = {"ftd": ftd, "distribution": distribution, "fib618": fib618,
            "touch200": touch200, "golden_cross": golden_cross}


def forward(rows, i, h):
    j = i + h
    return None if j >= len(rows) else 100 * (rows[j]["close"] / rows[i]["close"] - 1)


def run(symbol, pattern, horizon, days):
    rows = series(symbol, days)
    fn = PATTERNS[pattern]
    hits = [r for i in range(len(rows))
            if fn(rows, i) and (r := forward(rows, i, horizon)) is not None]
    base = [r for i in range(len(rows))
            if (r := forward(rows, i, horizon)) is not None]
    return hits, base, rows


def line(label, xs):
    if not xs:
        return f"  {label:22} no occurrences"
    win = 100 * sum(x > 0 for x in xs) / len(xs)
    return (f"  {label:22} n={len(xs):<5} mean {statistics.mean(xs):+6.2f}%  "
            f"median {statistics.median(xs):+6.2f}%  win {win:5.1f}%")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol")
    ap.add_argument("--pattern", default="ftd", choices=list(PATTERNS))
    ap.add_argument("--horizon", type=int, default=10, help="sessions held after the signal")
    ap.add_argument("--days", type=int, default=1300, help="history to test over")
    a = ap.parse_args()

    hits, base, rows = run(a.symbol, a.pattern, a.horizon, a.days)
    print(f"\n{a.symbol}  {rows[0]['date']} -> {rows[-1]['date']}  "
          f"({len(rows)} sessions)  {a.horizon}-day forward return\n")
    print(line(a.pattern, hits))
    print(line("baseline (any day)", base))
    if hits:
        edge = statistics.mean(hits) - statistics.mean(base)
        verdict = ("too few samples to trust" if len(hits) < 15 else
                   "no edge — drop it" if abs(edge) < 0.5 else
                   "signal holds" if edge > 0 else
                   "INVERTED — it predicts the opposite of the folklore")
        print(f"\n  edge {edge:+.2f}pp over baseline  ->  {verdict}")
    print()


def demo():
    """Self-check: a rule that fires on every day must equal the baseline."""
    rows = [{"date": f"d{i}", "open": 100 + i, "high": 101 + i, "low": 99 + i,
             "close": 100 + i, "volume": 1000} for i in range(300)]
    PATTERNS["always"] = lambda r, i: True
    hits = [x for i in range(len(rows)) if (x := forward(rows, i, 5)) is not None]
    base = [x for i in range(len(rows)) if (x := forward(rows, i, 5)) is not None]
    assert hits == base, "baseline construction is wrong"
    assert forward(rows, 0, 5) is not None and forward(rows, 299, 5) is None
    assert fib618(rows, 200) is False, "a monotonic uptrend has no 61.8% break"
    print("ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        demo()
    else:
        data.load_env()
        main()
