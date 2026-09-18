from __future__ import annotations

import csv
import hashlib
import io
import urllib.request
import zipfile
from datetime import date
from typing import Any

BASE="https://data.binance.vision/data/futures/um/daily/klines"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")


class BinanceArchiveError(RuntimeError):
    pass


def _url(symbol:str,day:date,suffix:str,interval:str="1m")->str:
    if interval not in {"1m","15m"}:
        raise BinanceArchiveError("interval outside frozen warmup allowlist")
    stamp=day.isoformat()
    name=f"{symbol}-{interval}-{stamp}.zip"
    base=f"{BASE}/{symbol}/{interval}/{name}"
    return base+suffix


def _read_url(url:str,timeout:int=20)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-edge-radar/0.9 dh03-warmup"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            if r.status!=200:
                raise BinanceArchiveError(f"HTTP {r.status}:{url}")
            return r.read()
    except Exception as exc:
        if isinstance(exc,BinanceArchiveError):
            raise
        raise BinanceArchiveError(f"archive unavailable:{type(exc).__name__}:{exc}") from exc


def load_verified_daily_1m(symbol:str,day:date,timeout:int=20)->dict[str,Any]:
    symbol=symbol.upper()
    if symbol not in SYMBOLS:
        raise BinanceArchiveError("symbol outside frozen universe")
    zip_url=_url(symbol,day,"",interval="1m")
    checksum_url=_url(symbol,day,".CHECKSUM",interval="1m")
    raw=_read_url(zip_url,timeout)
    check=_read_url(checksum_url,timeout).decode("utf-8").strip().split()
    if not check:
        raise BinanceArchiveError("empty checksum receipt")
    expected=check[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if expected!=actual:
        raise BinanceArchiveError(f"checksum mismatch:{symbol}:{day}")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:
            raise BinanceArchiveError("unexpected ZIP members")
        rows=list(csv.reader(io.TextIOWrapper(zf.open(names[0]),encoding="utf-8")))
    if rows and rows[0] and str(rows[0][0]).strip().lower() in {"open_time","open time"}:
        rows=rows[1:]
    if len(rows)!=1440:
        raise BinanceArchiveError(f"expected 1440 one-minute rows, got {len(rows)}")
    opens=[]
    for row in rows:
        if len(row)<7:
            raise BinanceArchiveError("malformed kline row")
        opens.append(int(row[0]))
    if any(opens[i]-opens[i-1]!=60_000 for i in range(1,len(opens))):
        raise BinanceArchiveError("one-minute continuity gap")
    return {
        "symbol":symbol,
        "day":day.isoformat(),
        "rows":len(rows),
        "first_open_ms":opens[0],
        "last_open_ms":opens[-1],
        "sha256":actual,
        "checksum_verified":True,
        "used_as_forward_evidence":False,
    }


def warmup_source_probe(day:date)->dict[str,Any]:
    results={s:load_verified_daily_1m(s,day) for s in SYMBOLS}
    return {
        "status":"PASS_ARCHIVE_WARMUP_SOURCE",
        "day":day.isoformat(),
        "symbols":results,
        "checksum_verified_all":all(x["checksum_verified"] for x in results.values()),
        "used_as_forward_evidence":False,
        "authenticated_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
    }


def load_verified_daily_1m_rows(symbol:str,day:date,timeout:int=20)->dict[str,Any]:
    """Checksum-verified full 1m day for deterministic shadow reconstruction."""
    symbol=symbol.upper()
    if symbol not in SYMBOLS:
        raise BinanceArchiveError("symbol outside frozen universe")
    zip_url=_url(symbol,day,"",interval="1m")
    checksum_url=_url(symbol,day,".CHECKSUM",interval="1m")
    raw=_read_url(zip_url,timeout)
    check=_read_url(checksum_url,timeout).decode("utf-8").strip().split()
    if not check:
        raise BinanceArchiveError("empty checksum receipt")
    expected=check[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if expected!=actual:
        raise BinanceArchiveError(f"checksum mismatch:{symbol}:{day}")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:
            raise BinanceArchiveError("unexpected ZIP members")
        rows=list(csv.reader(io.TextIOWrapper(zf.open(names[0]),encoding="utf-8")))
    if rows and rows[0] and str(rows[0][0]).strip().lower() in {"open_time","open time"}:
        rows=rows[1:]
    if len(rows)!=1440:
        raise BinanceArchiveError(f"expected 1440 one-minute rows, got {len(rows)}")
    parsed=[]
    prev=None
    for row in rows:
        if len(row)<7:
            raise BinanceArchiveError("malformed kline row")
        t=int(row[0]); o=float(row[1]); h=float(row[2]); l=float(row[3]); close=float(row[4])
        if prev is not None and t!=prev+60_000:
            raise BinanceArchiveError("one-minute continuity gap")
        if min(o,h,l,close)<=0 or h<max(o,close,l) or l>min(o,close,h):
            raise BinanceArchiveError("invalid OHLC")
        prev=t
        parsed.append((t,o,h,l,close))
    return {
        "symbol":symbol,
        "day":day.isoformat(),
        "sha256":actual,
        "checksum_verified":True,
        "rows":parsed,
    }


def load_verified_daily_interval_rows(
    symbol:str, day:date, interval:str="15m", timeout:int=20
)->dict[str,Any]:
    """Checksum-verified Binance USD-M daily archive rows for frozen warmup intervals."""
    symbol=symbol.upper()
    if symbol not in SYMBOLS:
        raise BinanceArchiveError("symbol outside frozen universe")
    if interval not in {"1m","15m"}:
        raise BinanceArchiveError("interval outside frozen warmup allowlist")
    step_ms=60_000 if interval=="1m" else 15*60_000
    expected_rows=1440 if interval=="1m" else 96
    zip_url=_url(symbol,day,"",interval=interval)
    checksum_url=_url(symbol,day,".CHECKSUM",interval=interval)
    raw=_read_url(zip_url,timeout)
    check=_read_url(checksum_url,timeout).decode("utf-8").strip().split()
    if not check:
        raise BinanceArchiveError("empty checksum receipt")
    expected=check[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if expected!=actual:
        raise BinanceArchiveError(f"checksum mismatch:{symbol}:{day}:{interval}")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:
            raise BinanceArchiveError("unexpected ZIP members")
        rows=list(csv.reader(io.TextIOWrapper(zf.open(names[0]),encoding="utf-8")))
    if rows and rows[0] and str(rows[0][0]).strip().lower() in {"open_time","open time"}:
        rows=rows[1:]
    if len(rows)!=expected_rows:
        raise BinanceArchiveError(
            f"expected {expected_rows} {interval} rows, got {len(rows)}"
        )
    parsed=[]
    prev=None
    for row in rows:
        if len(row)<7:
            raise BinanceArchiveError("malformed kline row")
        t=int(row[0]); o=float(row[1]); h=float(row[2]); l=float(row[3]); close=float(row[4]); v=float(row[5])
        if prev is not None and t!=prev+step_ms:
            raise BinanceArchiveError(f"{interval} continuity gap")
        if min(o,h,l,close)<=0 or v<0 or h<max(o,close,l) or l>min(o,close,h):
            raise BinanceArchiveError("invalid OHLCV")
        prev=t
        parsed.append((t,o,h,l,close,v))
    return {
        "symbol":symbol,
        "day":day.isoformat(),
        "interval":interval,
        "sha256":actual,
        "checksum_verified":True,
        "rows":parsed,
        "used_as_forward_evidence":False,
    }
