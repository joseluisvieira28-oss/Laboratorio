from __future__ import annotations

import csv
import hashlib
import io
import urllib.request
import zipfile
from datetime import date
from typing import Any

BASE="https://data.binance.vision/data/futures/um/daily/fundingRate"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")


class BinanceFundingArchiveError(RuntimeError):
    pass


def _read(url:str,timeout:int=20)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-edge-radar/0.9 dh03-funding"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            if r.status!=200:
                raise BinanceFundingArchiveError(f"HTTP {r.status}:{url}")
            return r.read()
    except Exception as exc:
        if isinstance(exc,BinanceFundingArchiveError):
            raise
        raise BinanceFundingArchiveError(f"funding archive unavailable:{type(exc).__name__}:{exc}") from exc


def load_verified_daily_funding(symbol:str,day:date,timeout:int=20)->dict[str,Any]:
    symbol=symbol.upper()
    if symbol not in SYMBOLS:
        raise BinanceFundingArchiveError("symbol outside frozen universe")
    stamp=day.isoformat()
    name=f"{symbol}-fundingRate-{stamp}.zip"
    url=f"{BASE}/{symbol}/{name}"
    raw=_read(url,timeout)
    checksum=_read(url+".CHECKSUM",timeout).decode("utf-8").strip().split()
    if not checksum:
        raise BinanceFundingArchiveError("empty checksum")
    expected=checksum[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected:
        raise BinanceFundingArchiveError("checksum mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:
            raise BinanceFundingArchiveError("unexpected ZIP members")
        rows=list(csv.reader(io.TextIOWrapper(zf.open(names[0]),encoding="utf-8")))
    if not rows:
        raise BinanceFundingArchiveError("empty funding CSV")
    hdr=[x.strip().lower() for x in rows[0]]
    data=rows[1:]
    def ix(cands):
        for c in cands:
            if c in hdr:
                return hdr.index(c)
        return None
    ti=ix(("calc_time","fundingtime","funding_time","funding time"))
    ri=ix(("last_funding_rate","fundingrate","funding_rate","funding rate"))
    if ti is None or ri is None:
        raise BinanceFundingArchiveError(f"unknown funding schema:{hdr}")
    events=[]
    for row in data:
        if not row:
            continue
        events.append((int(float(row[ti])),float(row[ri])))
    if not events:
        raise BinanceFundingArchiveError("no funding events")
    if any(events[i][0]<=events[i-1][0] for i in range(1,len(events))):
        raise BinanceFundingArchiveError("nonmonotonic funding events")
    return {
        "symbol":symbol,
        "day":stamp,
        "events":[{"funding_time_ms":t,"funding_rate":r} for t,r in events],
        "event_count":len(events),
        "sha256":actual,
        "checksum_verified":True,
        "used_as_forward_evidence":False,
    }


def funding_source_probe(day:date)->dict[str,Any]:
    rows={s:load_verified_daily_funding(s,day) for s in SYMBOLS}
    return {
        "status":"PASS_DAILY_FUNDING_ARCHIVE",
        "day":day.isoformat(),
        "symbols":rows,
        "total_events":sum(x["event_count"] for x in rows.values()),
        "checksum_verified_all":all(x["checksum_verified"] for x in rows.values()),
        "used_as_forward_evidence":False,
        "authenticated_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
    }
