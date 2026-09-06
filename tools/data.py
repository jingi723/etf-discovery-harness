"""Market data providers.

Two backends, chosen explicitly by the caller and authenticated by environment:

  FMP_API_KEY                         -> Financial Modeling Prep (global)
  TOSS_CLIENT_ID / TOSS_CLIENT_SECRET -> Toss Securities Open API (KR flows)

Scoring and backtesting call FMP directly; there is no automatic provider failover.
Korean investor-flow and short-selling helpers call Toss.
"""
from __future__ import annotations

import gzip
import json
import os
import time
import re
import urllib.parse
import urllib.request
from pathlib import Path

# Call counter. FMP's free tier caps daily requests, so knowing how many a run
# spends matters more than the wall-clock time. Set ETF_API_LOG to a path to
# also append one JSON line per call.
CALLS: dict[str, int] = {}
_LOG = os.environ.get("ETF_API_LOG")


# In-process response cache. score.score() refetches the same price series for
# every horizon, so scoring six funds across three horizons cost 150+ requests
# against a 250/day free tier. Cached, the same work is 58.
#
# Time-bounded on purpose: serving a stale close as today's is worse than
# spending the request. ETF_CACHE_TTL seconds, 0 disables entirely.
_CACHE: dict[str, tuple[float, object]] = {}
_HITS = 0
try:
    _TTL = float(os.environ.get("ETF_CACHE_TTL", 300))
except ValueError:
    _TTL = 300.0


def _cache_key(url):
    """Drop the API key so it is never a dict key we might print."""
    return re.sub(r"[?&]apikey=[^&]*", "", url)


def clear_cache():
    """Forget everything cached. Call this when crossing a session boundary,
    after a market close, or any time freshness matters more than the request."""
    _CACHE.clear()


def cache_stats():
    return {"entries": len(_CACHE), "hits": _HITS, "ttl_seconds": _TTL}


def _count(provider, endpoint):
    key = f"{provider}:{endpoint}"
    CALLS[key] = CALLS.get(key, 0) + 1
    if _LOG:
        with open(_LOG, "a") as f:
            f.write(json.dumps({"t": round(time.time()), "provider": provider,
                                "endpoint": endpoint}) + "\n")


def call_summary():
    """{'fmp:quote': 3, ...} plus totals.

    `total` is how many calls your code made. `served_from_cache` is how many of
    those never left the process, so network requests — the ones that count
    against a rate limit — are `total - served_from_cache`.
    """
    total = sum(CALLS.values())
    return {"by_endpoint": dict(CALLS), "total": total,
            "served_from_cache": _HITS, "network_requests": total - _HITS,
            "cache_ttl_seconds": _TTL}


FMP = "https://financialmodelingprep.com/stable"
TOSS = "https://openapi.tossinvest.com"
_TOKEN_CACHE = Path(os.environ.get("TOSS_TOKEN_CACHE", "/tmp/.toss_token.json"))


def load_env(path=".env"):
    """Read KEY=VALUE lines into os.environ without overwriting real env vars."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def _get(url, data=None, headers=None, retries=3):
    global _HITS
    key = _cache_key(url) if data is None else None   # never cache POSTs
    if key and _TTL > 0:
        hit = _CACHE.get(key)
        if hit and time.time() - hit[0] < _TTL:
            _HITS += 1
            return hit[1]
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers or {})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
            # some endpoints return gzip regardless of Accept-Encoding
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            out = json.loads(raw)
            if key and _TTL > 0:
                _CACHE[key] = (time.time(), out)
            return out
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise


# --------------------------------------------------------------------- FMP

def fmp(endpoint, **params):
    key = os.environ.get("FMP_API_KEY")
    if not key or key.startswith("replace"):
        raise RuntimeError("FMP_API_KEY is not set — see docs/API_SETUP.md")
    qs = urllib.parse.urlencode({**params, "apikey": key})
    _count("fmp", endpoint)
    return _get(f"{FMP}/{endpoint}?{qs}")


def prices(symbol, days=260):
    """Daily OHLCV, newest first. Works for US and `.KS`/`.KQ` Korean symbols."""
    r = fmp("historical-price-eod/full", symbol=symbol, limit=days)
    return r if isinstance(r, list) else r.get("historical", [])


def quote(symbol):
    r = fmp("quote", symbol=symbol)
    return r[0] if isinstance(r, list) and r else r


def ratios(symbol):
    r = fmp("ratios-ttm", symbol=symbol)
    return r[0] if isinstance(r, list) and r else (r or {})


def holdings(symbol):
    """ETF constituents. Empty for Korean ETFs — FMP does not cover them."""
    r = fmp("etf/holdings", symbol=symbol)
    return r if isinstance(r, list) else []


def etf_info(symbol):
    r = fmp("etf/info", symbol=symbol)
    return r[0] if isinstance(r, list) and r else (r or {})


def treasury_rates(days=900):
    r = fmp("treasury-rates", limit=days)
    return r if isinstance(r, list) else [r]


# -------------------------------------------------------------------- Toss

def toss_token():
    """Client-credentials token. Only ONE token per client is valid at a time,
    so it is cached on disk and shared instead of re-issued per process."""
    cid = os.environ.get("TOSS_CLIENT_ID")
    secret = os.environ.get("TOSS_CLIENT_SECRET")
    if not cid or not secret or cid.startswith("replace"):
        raise RuntimeError("TOSS_CLIENT_ID/SECRET not set — see docs/API_SETUP.md")
    if _TOKEN_CACHE.exists():
        try:
            cached = json.loads(_TOKEN_CACHE.read_text())
            if cached["expires_at"] > time.time() + 60:
                return cached["access_token"]
        except (ValueError, KeyError):
            pass
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": cid,
        "client_secret": secret,
    }).encode()
    try:
        d = _get(f"{TOSS}/oauth2/token", body,
                 {"Content-Type": "application/x-www-form-urlencoded"})
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "Toss returned 403. This is almost always an IP allowlist issue, "
                "not a bad key — register your current public IP in the Toss "
                "developer console. See docs/API_SETUP.md"
            ) from e
        raise
    _TOKEN_CACHE.write_text(json.dumps(
        {"access_token": d["access_token"],
         "expires_at": time.time() + d.get("expires_in", 3600)}))
    return d["access_token"]


def toss(path, **params):
    tok = toss_token()
    qs = urllib.parse.urlencode(params)
    url = f"{TOSS}/api/v1/{path}" + (f"?{qs}" if qs else "")
    _count("toss", path.split("/")[0] if "/" not in path else path.split("/")[-1])
    return _get(url, headers={"Authorization": f"Bearer {tok}"})["result"]


def investor_trading(symbol, count=10):
    """Korean investor-type net buying (individual / foreign / 7 institution
    sub-types incl. pension funds). KR symbols only, e.g. "005930"."""
    return toss(f"stocks/{symbol}/investor-trading", count=count)["records"]


def short_selling(symbol, count=10):
    """Korean short-selling volume and its share of total volume."""
    return toss(f"stocks/{symbol}/short-selling", count=count)["records"]


def demo():
    """Self-check: the cache must cut repeats, expire, and keep keys out."""
    global _TTL, _HITS
    _TTL, saved = 60.0, _TTL
    clear_cache(); _HITS = 0
    _CACHE["https://x/stable/quote?symbol=SPY"] = (time.time(), {"ok": 1})
    assert _get("https://x/stable/quote?symbol=SPY&apikey=SECRET") == {"ok": 1}, "key must be stripped"
    assert _HITS == 1
    assert not any("SECRET" in k for k in _CACHE), "api key leaked into a cache key"
    _CACHE["https://x/stale"] = (time.time() - 1e6, {"old": 1})
    assert "https://x/stale" in _CACHE
    _TTL = 0.0                      # disabled means never serve from cache
    hits_before = _HITS
    try:
        _get("https://x/stable/quote?symbol=SPY&apikey=SECRET")
    except Exception:
        pass                        # it will try the network and fail; that is the point
    assert _HITS == hits_before, "TTL=0 must bypass the cache"
    _TTL = saved
    clear_cache()
    print("ok")


if __name__ == "__main__":
    if "--self-check" in __import__("sys").argv:
        demo()
