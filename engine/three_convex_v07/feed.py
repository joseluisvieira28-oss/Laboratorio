"""Continuous Binance USD-M PUBLIC 5m V5 signal collector with local cache.

Not MEXC orders. Does not open protected 2026 historical holdout:
it reads only contemporary recent public completed bars to derive new signals.
Historical archive-vs-REST feed parity is NOT independently established.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import time
from urllib.parse import urlencode,urlparse
from urllib.request import Request,urlopen

from engine.three_convex_v05.signals import (
    Bar, Halt, MS5, closed_signal_decisions,
)

SYMBOLS={"SOL_USDT":"SOLUSDT","BNB_USDT":"BNBUSDT"}
LOOKBACK=48*260+96
HOST="https://fapi.binance.com"
BAR_LIMIT=1500


class FeedHalt(ValueError):
    pass


def get_public(path,params=None,*,opener=urlopen):
    if path not in ("/fapi/v1/time","/fapi/v1/klines"):
        raise FeedHalt("NON_ALLOWLISTED_BINANCE_PATH")
    url=HOST+path+("?" + urlencode(params) if params else "")
    req=Request(url,headers={"User-Agent":"CryptoLab-Convex-V07-Public/1.0"})
    try:
        with opener(req,timeout=12) as res:
            actual=res.geturl() if hasattr(res,"geturl") else url
            p=urlparse(actual)
            if getattr(res,"status",200)!=200 or p.scheme!="https" or p.hostname!="fapi.binance.com":
                raise FeedHalt("BAD_PUBLIC_DATA_ORIGIN")
            raw=res.read(1_400_000)
    except Exception:
        raise FeedHalt("BINANCE_PUBLIC_SOURCE_UNAVAILABLE") from None
    if len(raw)>=1_400_000:
        raise FeedHalt("PUBLIC_RESPONSE_OVERSIZED")
    try:
        return json.loads(raw)
    except (ValueError,UnicodeDecodeError):
        raise FeedHalt("PUBLIC_SOURCE_BAD_JSON")


def clock_ms(*,public=get_public,clock=lambda:int(time.time()*1000)):
    data=public("/fapi/v1/time")
    if not isinstance(data,dict) or type(data.get("serverTime")) is not int:
        raise FeedHalt("BINANCE_CLOCK_UNAVAILABLE")
    now=clock()
    if abs(now-data["serverTime"])>5_000:
        raise FeedHalt("WINDOWS_CLOCK_OFFSET_EXCESSIVE")
    return data["serverTime"]


def _save_json_atomic(path,object):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    with temp.open("x",encoding="utf-8") as f:
        json.dump(object,f,sort_keys=True,separators=(",",":"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp,path)


def _clean_cache(path,symbol,start,final):
    if not path.exists():return []
    if path.stat().st_size>4_000_000:
        raise FeedHalt("PUBLIC_CACHE_SIZE_EXCEEDED")
    try:
        saved=json.loads(path.read_text(encoding="utf-8"))
    except (ValueError,UnicodeError,OSError):
        raise FeedHalt("CORRUPT_PUBLIC_CACHE")
    if (not isinstance(saved,dict) or saved.get("symbol")!=symbol or
        saved.get("source")!="BINANCE_USDM_5M_PUBLIC"):
        raise FeedHalt("PUBLIC_CACHE_IDENTITY_MISMATCH")
    cached=saved.get("bars")
    if not isinstance(cached,list):
        raise FeedHalt("PUBLIC_CACHE_ROWS_MISSING")
    valid=[]
    for row in cached:
        if not isinstance(row,list) or len(row)!=6 or type(row[0]) is not int:
            raise FeedHalt("PUBLIC_CACHE_ROW_MALFORMED")
        try:
            bar=Bar(*row).validate()
        except (Halt,TypeError,ValueError):
            raise FeedHalt("PUBLIC_CACHE_UNTRUSTED_OHLC")
        valid.append(bar)
    for i,b in enumerate(valid):
        if i and b.t!=valid[i-1].t+MS5:
            raise FeedHalt("PUBLIC_CACHE_DISCONTINUITY")
    retained=[b for b in valid if start<=b.t<=final]
    if retained and retained[0].t!=start:
        return []  # cache older history no longer sufficient: reacquire all
    return retained


def fetch_complete(symbol,now_ms,cache_dir,*,public=get_public):
    if symbol not in SYMBOLS or type(now_ms) is not int:
        raise FeedHalt("INVALID_SYMBOL_OR_TIMESTAMP")
    boundary=(now_ms//MS5)*MS5
    final=boundary-MS5
    if now_ms-boundary<2_000:
        final-=MS5
    start=final-(LOOKBACK-1)*MS5
    if start<=0:
        raise FeedHalt("BAD_HISTORY_WINDOW")
    path=Path(cache_dir)/(symbol+"_binance_5m.json")
    results=_clean_cache(path,symbol,start,final)
    cursor=results[-1].t+MS5 if results else start
    while cursor<=final:
        count=min(BAR_LIMIT,(final-cursor)//MS5+1)
        rows=public("/fapi/v1/klines",{
            "symbol":SYMBOLS[symbol],"interval":"5m",
            "startTime":cursor,"endTime":final+MS5-1,
            "limit":count,
        })
        if not isinstance(rows,list) or len(rows)!=count:
            raise FeedHalt("MISSING_PUBLIC_5M_PAGE")
        for item in rows:
            if not isinstance(item,list) or len(item)<7:
                raise FeedHalt("MALFORMED_PUBLIC_OHLCV")
            if type(item[0]) is not int or item[0]!=cursor or item[6]!=cursor+MS5-1:
                raise FeedHalt("CANDLE_SOURCE_GAP_OR_CLOSE_TIMESTAMP")
            try:
                b=Bar(item[0],float(item[1]),float(item[2]),float(item[3]),
                      float(item[4]),float(item[5])).validate()
            except (ValueError,TypeError,Halt):
                raise FeedHalt("MALFORMED_CANDLE_CONTENT") from None
            results.append(b)
            cursor+=MS5
    if len(results)!=LOOKBACK or results[0].t!=start or results[-1].t!=final:
        raise FeedHalt("INCOMPLETE_CANONICAL_5M_HISTORY")
    _save_json_atomic(path,{"symbol":symbol,"source":"BINANCE_USDM_5M_PUBLIC",
                             "bars":[[b.t,b.open,b.high,b.low,b.close,b.volume]
                                     for b in results]})
    return results


def fresh_signals(symbol,bars,now_ms,activation_ms):
    if type(activation_ms) is not int or activation_ms<0:
        raise FeedHalt("INVALID_ACTIVATION")
    try:
        flags=closed_signal_decisions(symbol,bars,now_ms)
    except Halt as exc:
        raise FeedHalt("PARENT_V5_CAUSAL_SIGNAL_SOURCE_REJECTED") from exc
    out=[]
    for s in flags:
        close=s["signal_close_ms"]
        if close>=activation_ms and 1_000<=now_ms-close<=180_000:
            out.append(s)
    return out
