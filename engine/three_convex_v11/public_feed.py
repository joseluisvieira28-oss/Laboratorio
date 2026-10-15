"""V11 public-only experimental feed. Does not alter the V07 module/global state."""
from engine.three_convex_v07 import feed as v07
from engine.three_convex_v05.signals import MS5, Bar
from pathlib import Path
from urllib.parse import urlencode

SYMBOLS = {"SOL_USDT": "SOLUSDT", "BNB_USDT": "BNBUSDT", "ETH_USDT": "ETHUSDT"}
LOOKBACK = 48*260+96

def fetch_experimental(symbol, now_ms, cache_dir, *, public=v07.get_public):
    if symbol not in SYMBOLS or type(now_ms) is not int:
        raise v07.FeedHalt("INVALID_EXP_SYMBOL")
    boundary=(now_ms//MS5)*MS5
    final=boundary-MS5
    if now_ms-boundary<2000: final-=MS5
    start=final-(LOOKBACK-1)*MS5
    if start<0:raise v07.FeedHalt("BAD_HISTORY_START")
    path=Path(cache_dir)/(symbol+"_v11_5m.json")
    results=v07._clean_cache(path,symbol,start,final)
    cursor=results[-1].t+MS5 if results else start
    while cursor<=final:
        count=min(1500,(final-cursor)//MS5+1)
        rows=public("/fapi/v1/klines",{
            "symbol":SYMBOLS[symbol],"interval":"5m",
            "startTime":cursor,"endTime":final+MS5-1,"limit":count})
        if not isinstance(rows,list) or len(rows)!=count:
            raise v07.FeedHalt("MISSING_PUBLIC_PAGE")
        for raw in rows:
            if not isinstance(raw,list) or len(raw)<7 or type(raw[0]) is not int or raw[0]!=cursor or raw[6]!=cursor+MS5-1:
                raise v07.FeedHalt("PUBLIC_BAR_TIMESTAMP_OR_SHAPE_BAD")
            try:
                b=Bar(cursor,float(raw[1]),float(raw[2]),float(raw[3]),float(raw[4]),float(raw[5])).validate()
            except (ValueError,TypeError,v07.Halt):
                raise v07.FeedHalt("PUBLIC_BAR_CONTENT_BAD") from None
            results.append(b)
            cursor+=MS5
    if len(results)!=LOOKBACK or results[0].t!=start or results[-1].t!=final:
        raise v07.FeedHalt("INCOMPLETE_EXP_HISTORY")
    v07._save_json_atomic(path,{"symbol":symbol,"source":"BINANCE_USDM_5M_PUBLIC",
                                  "bars":[[b.t,b.open,b.high,b.low,b.close,b.volume] for b in results]})
    return results
