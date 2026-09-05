"""Market data providers.

Two optional backends, selected by which env vars are present:

  FMP_API_KEY                         -> Financial Modeling Prep (global)
  TOSS_CLIENT_ID / TOSS_CLIENT_SECRET -> Toss Securities Open API (KR flows)

FMP alone is enough for everything except Korean investor-flow and
short-selling data, which only Toss provides.
"""
from __future__ import annotations

import gzip
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

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
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers or {})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
            # some endpoints return gzip regardless of Accept-Encoding
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return json.loads(raw)
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
    return _get(url, headers={"Authorization": f"Bearer {tok}"})["result"]


def investor_trading(symbol, count=10):
    """Korean investor-type net buying (individual / foreign / 7 institution
    sub-types incl. pension funds). KR symbols only, e.g. "005930"."""
    return toss(f"stocks/{symbol}/investor-trading", count=count)["records"]


def short_selling(symbol, count=10):
    """Korean short-selling volume and its share of total volume."""
    return toss(f"stocks/{symbol}/short-selling", count=count)["records"]
