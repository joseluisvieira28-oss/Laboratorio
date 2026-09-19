from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from math import isfinite
from statistics import mean
import time
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BINANCE_SPOT_BASE_URL = "https://data-api.binance.vision"
FROZEN_UNIVERSE = ("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
FIFTEEN_MIN_MS = 900_000
SIX_HOUR_MS = 21_600_000
DAY_MS = 86_400_000
EMA_FAST = 50
EMA_SLOW = 200
REGIME_SMA = 200
REGIME_SLOPE_LAG = 20
HOLD_BARS = 6
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 14.0
ACTIVATION_BOUNDARY_MS = int(datetime(2026,9,19,18,0,tzinfo=timezone.utc).timestamp()*1000)
FIRST_ELIGIBLE_SIGNAL_CLOSE_MS = int(datetime(2026,9,20,0,0,tzinfo=timezone.utc).timestamp()*1000)
WARMUP_15M_MS = 60 * DAY_MS
WARMUP_1D_MS = 240 * DAY_MS

class EMA6HRegimeSourceError(RuntimeError):
    pass

@dataclass(frozen=True)
class Candle:
    open_time:int
    open:float
    high:float
    low:float
    close:float
    volume:float
    close_time:int

@dataclass(frozen=True)
class CrossSignal:
    symbol:str
    direction:int
    signal_open_ms:int
    signal_close_ms:int
    ema50:float
    ema200:float
    prior_ema50:float
    prior_ema200:float

@dataclass(frozen=True)
class ForwardTrade:
    symbol:str
    direction:int
    signal_close_ms:int
    entry_open_ms:int
    entry:float
    exit_open_ms:int
    regime_state:str
    regime_bucket:str

@dataclass(frozen=True)
class ForwardOutcome:
    exit_open_ms:int
    exit_price:float
    gross_bps:float
    base_net_bps:float
    stress_net_bps:float

def utc_iso(ms:int)->str:
    return datetime.fromtimestamp(ms/1000.0,tz=timezone.utc).isoformat().replace("+00:00","Z")

def _duration_ms(interval:str)->int:
    if interval=="15m":return FIFTEEN_MIN_MS
    if interval=="1d":return DAY_MS
    raise EMA6HRegimeSourceError(f"unsupported interval {interval}")

def _validate_symbol(symbol:str)->str:
    s=symbol.upper()
    if s not in FROZEN_UNIVERSE:raise EMA6HRegimeSourceError(f"symbol outside frozen universe: {symbol}")
    return s

def _parse_kline(row:Any,interval:str)->Candle:
    if not isinstance(row,list) or len(row)<7:raise EMA6HRegimeSourceError("invalid Binance kline row")
    try:
        c=Candle(int(row[0]),float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),int(row[6]))
    except (TypeError,ValueError) as exc:
        raise EMA6HRegimeSourceError("invalid Binance kline values") from exc
    step=_duration_ms(interval)
    if c.open_time%step!=0 or c.close_time!=c.open_time+step-1:raise EMA6HRegimeSourceError("Binance timestamp/alignment violation")
    vals=(c.open,c.high,c.low,c.close,c.volume)
    if any(not isfinite(v) for v in vals):raise EMA6HRegimeSourceError("non-finite kline")
    if min(c.open,c.high,c.low,c.close)<=0 or c.volume<0:raise EMA6HRegimeSourceError("invalid OHLC/volume")
    if c.high<max(c.open,c.close,c.low) or c.low>min(c.open,c.close,c.high):raise EMA6HRegimeSourceError("OHLC ordering violation")
    return c

class BinanceSpotKlineFeed:
    provider="BINANCE_SPOT_PUBLIC"
    path="/api/v3/klines"
    base_url=BINANCE_SPOT_BASE_URL

    def __init__(self,timeout:int=10,*,max_attempts:int=3,retry_backoff_seconds:float=0.5)->None:
        self.timeout=timeout;self.max_attempts=max_attempts;self.retry_backoff_seconds=retry_backoff_seconds
        if max_attempts<1:raise ValueError("max_attempts must be >=1")

    def _get_json(self,query:dict[str,Any])->Any:
        url=f"{self.base_url}{self.path}?{urlencode(query)}"
        req=Request(url,method="GET",headers={"User-Agent":"crypto-edge-radar/ema6h-regime-forward"})
        last=None
        for attempt in range(1,self.max_attempts+1):
            try:
                with urlopen(req,timeout=self.timeout) as response:
                    if response.status!=200:raise EMA6HRegimeSourceError(f"Binance spot HTTP {response.status}")
                    return json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                if isinstance(exc,EMA6HRegimeSourceError):raise
                last=exc
                if attempt<self.max_attempts and self.retry_backoff_seconds:time.sleep(self.retry_backoff_seconds*attempt)
        raise EMA6HRegimeSourceError(f"Binance source unavailable: {type(last).__name__}: {last}") from last

    def klines(self,symbol:str,interval:str,*,start_ms:int,end_ms:int,now_ms:int)->list[Candle]:
        symbol=_validate_symbol(symbol);step=_duration_ms(interval)
        if start_ms>=end_ms:raise EMA6HRegimeSourceError("invalid kline range")
        cursor=start_ms-(start_ms%step);end_exclusive=end_ms-(end_ms%step)
        if end_exclusive<=cursor:return []
        rows={}
        while cursor<end_exclusive:
            payload=self._get_json({"symbol":symbol,"interval":interval,"startTime":cursor,"endTime":end_exclusive-1,"limit":1000})
            if not isinstance(payload,list):raise EMA6HRegimeSourceError("payload is not list")
            if not payload:break
            parsed=[_parse_kline(x,interval) for x in payload]
            for c in parsed:
                if start_ms<=c.open_time<end_exclusive and c.close_time<now_ms:rows[c.open_time]=c
            last_open=max(c.open_time for c in parsed);next_cursor=last_open+step
            if next_cursor<=cursor:raise EMA6HRegimeSourceError("pagination did not advance")
            cursor=next_cursor
        return [rows[t] for t in sorted(rows)]

def validate_regular(candles:Iterable[Candle],step:int)->list[Candle]:
    rows=sorted(candles,key=lambda c:c.open_time)
    for i,c in enumerate(rows):
        if c.open_time%step!=0 or c.close_time!=c.open_time+step-1:raise EMA6HRegimeSourceError("candle alignment violation")
        if i and c.open_time-rows[i-1].open_time!=step:raise EMA6HRegimeSourceError("candle gap")
    return rows

def aggregate_15m_to_6h(candles:Iterable[Candle])->tuple[list[Candle],int]:
    rows=sorted(candles,key=lambda c:c.open_time);buckets={}
    for c in rows:
        if c.open_time%FIFTEEN_MIN_MS!=0 or c.close_time!=c.open_time+FIFTEEN_MIN_MS-1:raise EMA6HRegimeSourceError("15m alignment violation")
        b=c.open_time-(c.open_time%SIX_HOUR_MS);buckets.setdefault(b,[]).append(c)
    out=[];incomplete=0
    for b in sorted(buckets):
        xs=sorted(buckets[b],key=lambda c:c.open_time);exp=[b+i*FIFTEEN_MIN_MS for i in range(24)]
        if len(xs)!=24 or [x.open_time for x in xs]!=exp:
            incomplete+=1;continue
        out.append(Candle(b,xs[0].open,max(x.high for x in xs),min(x.low for x in xs),xs[-1].close,sum(x.volume for x in xs),b+SIX_HOUR_MS-1))
    return out,incomplete

def ema_series(values:list[float],length:int)->list[float|None]:
    out=[None]*len(values)
    if len(values)<length:return out
    value=sum(values[:length])/length;out[length-1]=value;a=2.0/(length+1.0)
    for i in range(length,len(values)):
        value=a*values[i]+(1-a)*value;out[i]=value
    return out

def regime_state(daily_btc:list[Candle],*,signal_close_ms:int)->dict[str,Any]:
    rows=[c for c in daily_btc if c.close_time<signal_close_ms]
    if len(rows)<REGIME_SMA+REGIME_SLOPE_LAG:return {"state":"MISSING","reason":"insufficient_daily_history"}
    tail=validate_regular(rows[-(REGIME_SMA+REGIME_SLOPE_LAG):],DAY_MS)
    sma_now=mean(c.close for c in tail[-REGIME_SMA:])
    sma_old=mean(c.close for c in tail[:REGIME_SMA])
    close=tail[-1].close
    if close>sma_now and sma_now>sma_old:state="BULL_TREND"
    elif close<sma_now and sma_now<sma_old:state="BEAR_TREND"
    else:state="TRANSITION_CHOP"
    return {"state":state,"btc_close":close,"sma200":sma_now,"sma200_20d_ago":sma_old,"snapshot_daily_open_ms":tail[-1].open_time}

def regime_bucket(state:str,direction:int)->str:
    if state=="BULL_TREND":return "TREND_ALIGNED" if direction==1 else "COUNTER_REGIME"
    if state=="BEAR_TREND":return "TREND_ALIGNED" if direction==-1 else "COUNTER_REGIME"
    if state=="TRANSITION_CHOP":return "TRANSITION_CHOP"
    return "MISSING"

def detect_cross(symbol:str,bars_6h:list[Candle],*,signal_close_ms:int)->CrossSignal|None:
    symbol=_validate_symbol(symbol)
    rows=sorted(bars_6h,key=lambda c:c.open_time)
    idx=next((i for i,c in enumerate(rows) if c.open_time+SIX_HOUR_MS==signal_close_ms),None)
    if idx is None:raise EMA6HRegimeSourceError("required signal 6H bar unavailable")
    if signal_close_ms<FIRST_ELIGIBLE_SIGNAL_CLOSE_MS:return None
    if idx<EMA_SLOW:raise EMA6HRegimeSourceError("insufficient 6H EMA warmup")
    validate_regular(rows[max(0,idx-EMA_SLOW-2):idx+1],SIX_HOUR_MS)
    closes=[c.close for c in rows]
    e50=ema_series(closes,EMA_FAST);e200=ema_series(closes,EMA_SLOW)
    if None in (e50[idx-1],e200[idx-1],e50[idx],e200[idx]):raise EMA6HRegimeSourceError("EMA unavailable")
    d0=float(e50[idx-1])-float(e200[idx-1]);d1=float(e50[idx])-float(e200[idx])
    direction=1 if d0<=0<d1 else (-1 if d0>=0>d1 else 0)
    if direction==0:return None
    return CrossSignal(symbol,direction,rows[idx].open_time,signal_close_ms,float(e50[idx]),float(e200[idx]),float(e50[idx-1]),float(e200[idx-1]))

def materialize_trade(signal:CrossSignal,source_15m:list[Candle],regime:dict[str,Any])->ForwardTrade|None:
    entry_bar=next((c for c in source_15m if c.open_time==signal.signal_close_ms),None)
    if entry_bar is None:return None
    state=str(regime.get("state") or "MISSING")
    return ForwardTrade(signal.symbol,signal.direction,signal.signal_close_ms,signal.signal_close_ms,entry_bar.open,signal.signal_close_ms+HOLD_BARS*SIX_HOUR_MS,state,regime_bucket(state,signal.direction))

def resolve_trade(trade:ForwardTrade,source_15m:list[Candle])->ForwardOutcome|None:
    exit_bar=next((c for c in source_15m if c.open_time==trade.exit_open_ms),None)
    if exit_bar is None:return None
    gross=trade.direction*(exit_bar.open/trade.entry-1.0)*10_000.0
    return ForwardOutcome(trade.exit_open_ms,exit_bar.open,gross,gross-BASE_COST_BPS,gross-STRESS_COST_BPS)

def latest_certifiable_signal_close_ms(now_ms:int)->int|None:
    boundary=now_ms-(now_ms%SIX_HOUR_MS)
    if now_ms<boundary+FIFTEEN_MIN_MS:boundary-=SIX_HOUR_MS
    return boundary if boundary>=FIRST_ELIGIBLE_SIGNAL_CLOSE_MS else None

def latest_certifiable_exit_open_ms(now_ms:int)->int|None:
    boundary=now_ms-(now_ms%SIX_HOUR_MS)
    if now_ms<boundary+FIFTEEN_MIN_MS:boundary-=SIX_HOUR_MS
    return boundary if boundary>=FIRST_ELIGIBLE_SIGNAL_CLOSE_MS+HOLD_BARS*SIX_HOUR_MS else None
