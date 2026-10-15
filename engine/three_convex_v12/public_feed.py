"""Strict Binance public USD-M 5m source for V12, DOGE included.

Separate cache from V07/V11. Never requests private Binance/MEXC data.
"""
from pathlib import Path
import json
import os
import tempfile
from engine.three_convex_v05.signals import Bar, MS5, Halt
from engine.three_convex_v07.feed import get_public, FeedHalt, _clean_cache

SYMBOLS={"SOL_USDT":"SOLUSDT","BNB_USDT":"BNBUSDT","DOGE_USDT":"DOGEUSDT"}
LOOKBACK=48*260+96  # >=260 full 4H candles + pad
MAX_PAGE=1500

def atomic_save(path, payload):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp_name=None
    try:
        with tempfile.NamedTemporaryFile("w",dir=path.parent,suffix=".tmp",prefix="v12-",delete=False,encoding="utf-8") as f:
            temp_name=f.name
            json.dump(payload,f,separators=(",",":"),sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name,path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)

def fetch(symbol, now_ms, folder, *, public=get_public):
    if symbol not in SYMBOLS or type(now_ms) is not int:
        raise FeedHalt("V12_SYMBOL_OR_CLOCK_BAD")
    boundary=(now_ms//MS5)*MS5
    final=boundary-MS5
    if now_ms-boundary<2000:
        final-=MS5
    start=final-(LOOKBACK-1)*MS5
    if start<=0:
        raise FeedHalt("V12_BAD_HISTORY_WINDOW")
    path=Path(folder)/(symbol+"_v12_5m.json")
    results=_clean_cache(path,symbol,start,final)
    cursor=results[-1].t+MS5 if results else start
    while cursor<=final:
        count=min(MAX_PAGE,(final-cursor)//MS5+1)
        rows=public("/fapi/v1/klines",{
            "symbol":SYMBOLS[symbol],"interval":"5m",
            "startTime":cursor,"endTime":final+MS5-1,"limit":count})
        if not isinstance(rows,list) or len(rows)!=count:
            raise FeedHalt("V12_INCOMPLETE_PUBLIC_PAGE")
        for raw in rows:
            if (not isinstance(raw,list) or len(raw)<7 or type(raw[0]) is not int
                or raw[0]!=cursor or raw[6]!=cursor+MS5-1):
                raise FeedHalt("V12_PUBLIC_PAGE_TIMESTAMP_MISMATCH")
            try:
                candle=Bar(cursor,float(raw[1]),float(raw[2]),float(raw[3]),
                           float(raw[4]),float(raw[5])).validate()
            except (Halt,ValueError,TypeError):
                raise FeedHalt("V12_PUBLIC_CANDLE_INVALID") from None
            results.append(candle)
            cursor+=MS5
    if len(results)!=LOOKBACK or results[0].t!=start or results[-1].t!=final:
        raise FeedHalt("V12_INCOMPLETE_CANONICAL_HISTORY")
    atomic_save(path,{"symbol":symbol,"source":"BINANCE_USDM_5M_PUBLIC",
        "bars":[[b.t,b.open,b.high,b.low,b.close,b.volume] for b in results]})
    return results
