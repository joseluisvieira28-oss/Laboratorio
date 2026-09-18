from __future__ import annotations
import csv, hashlib, io, urllib.request, zipfile
from typing import Any

BASE="https://data.binance.vision/data/futures/um/monthly/fundingRate"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")

class BinanceMonthlyFundingError(RuntimeError):
    pass

def _read(url:str,timeout:int=30)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-edge-radar/0.9 dh03-monthly-funding"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            if r.status!=200:
                raise BinanceMonthlyFundingError(f"HTTP {r.status}:{url}")
            return r.read()
    except Exception as exc:
        if isinstance(exc,BinanceMonthlyFundingError):
            raise
        raise BinanceMonthlyFundingError(f"monthly funding unavailable:{type(exc).__name__}:{exc}") from exc

def load_verified_monthly_funding(symbol:str,ym:str,timeout:int=30)->dict[str,Any]:
    symbol=symbol.upper()
    if symbol not in SYMBOLS:
        raise BinanceMonthlyFundingError("symbol outside frozen universe")
    if len(ym)!=7 or ym[4]!="-":
        raise BinanceMonthlyFundingError("invalid YYYY-MM")
    name=f"{symbol}-fundingRate-{ym}.zip"
    url=f"{BASE}/{symbol}/{name}"
    raw=_read(url,timeout)
    check=_read(url+".CHECKSUM",timeout).decode("utf-8").strip().split()
    if not check:
        raise BinanceMonthlyFundingError("empty checksum")
    expected=check[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected:
        raise BinanceMonthlyFundingError("checksum mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:
            raise BinanceMonthlyFundingError("unexpected ZIP members")
        rows=list(csv.reader(io.TextIOWrapper(zf.open(names[0]),encoding="utf-8")))
    if not rows:
        raise BinanceMonthlyFundingError("empty funding CSV")
    hdr=[x.strip().lower() for x in rows[0]]
    data=rows[1:]
    def ix(cands):
        for c in cands:
            if c in hdr:return hdr.index(c)
        return None
    ti=ix(("calc_time","fundingtime","funding_time","funding time"))
    ri=ix(("last_funding_rate","fundingrate","funding_rate","funding rate"))
    if ti is None or ri is None:
        raise BinanceMonthlyFundingError(f"unknown schema:{hdr}")
    events=[]
    for row in data:
        if not row:continue
        events.append((int(float(row[ti])),float(row[ri])))
    if not events:
        raise BinanceMonthlyFundingError("no funding events")
    if any(events[i][0]<=events[i-1][0] for i in range(1,len(events))):
        raise BinanceMonthlyFundingError("nonmonotonic events")
    return {
        "symbol":symbol,"month":ym,
        "events":[{"funding_time_ms":t,"funding_rate":r} for t,r in events],
        "event_count":len(events),"sha256":actual,"checksum_verified":True,
        "authenticated_api_used":False,"used_as_forward_evidence":False
    }

def source_probe(ym:str)->dict[str,Any]:
    rows={s:load_verified_monthly_funding(s,ym) for s in SYMBOLS}
    return {
        "status":"PASS_MONTHLY_FUNDING_SOURCE",
        "month":ym,"symbols":rows,
        "total_events":sum(x["event_count"] for x in rows.values()),
        "checksum_verified_all":all(x["checksum_verified"] for x in rows.values()),
        "used_as_forward_evidence":False,
        "authenticated_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False
    }
