from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from statistics import mean
from typing import Iterable

MINUTE_MS=60_000
FIFTEEN_MIN_MS=15*MINUTE_MS
TWELVE_H_MS=12*60*60*1000
LOOKBACK=40
ATR_LEN=28
TARGET_R=3.0
STOP_ATR_MULT=0.25
MAX_HOLD_BARS=80
MAX_HOLD_MS=MAX_HOLD_BARS*TWELVE_H_MS
BASE_COST=0.002
STRESS_COST=0.003
FREEZE_MS=1789712813000  # 2026-09-18T06:26:53Z


@dataclass(frozen=True)
class Bar:
    open_time:int
    open:float
    high:float
    low:float
    close:float
    volume:float=0.0


@dataclass(frozen=True)
class SignalCandidate:
    symbol:str
    signal_open_time:int
    signal_close_time:int
    signal_low:float
    atr:float
    prior_high:float


@dataclass(frozen=True)
class Signal:
    symbol:str
    signal_open_time:int
    signal_close_time:int
    entry_open_time:int
    entry:float
    stop:float
    target:float
    initial_risk_fraction:float
    fingerprint:str


@dataclass(frozen=True)
class MinuteOutcome:
    resolved:bool
    exit_time:int|None
    exit_price:float|None
    exit_reason:str|None
    price_gross_return:float|None
    funding_return:float|None
    funding_event_count:int
    economic_gross_return:float|None
    base_net_r:float|None
    stress_net_r:float|None


def canonical_hash(payload:dict)->str:
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def _validate_bar(b:Bar)->None:
    if b.open_time<0 or b.open_time%FIFTEEN_MIN_MS!=0:
        raise ValueError("15m bar timestamp misaligned")
    if not all(isfinite(x) for x in (b.open,b.high,b.low,b.close,b.volume)):
        raise ValueError("non-finite bar")
    if min(b.open,b.high,b.low,b.close)<=0 or b.volume<0:
        raise ValueError("invalid bar values")
    if b.high<max(b.open,b.close,b.low) or b.low>min(b.open,b.close,b.high):
        raise ValueError("invalid OHLC geometry")


def aggregate_12h(candles:Iterable[Bar])->tuple[list[Bar],int]:
    buckets:dict[int,list[Bar]]={}
    for c in candles:
        _validate_bar(c)
        bucket=c.open_time-(c.open_time%TWELVE_H_MS)
        buckets.setdefault(bucket,[]).append(c)
    out:list[Bar]=[]
    incomplete=0
    expected_n=TWELVE_H_MS//FIFTEEN_MIN_MS
    for bucket in sorted(buckets):
        rows=sorted(buckets[bucket],key=lambda x:x.open_time)
        expected=[bucket+i*FIFTEEN_MIN_MS for i in range(expected_n)]
        if len(rows)!=expected_n or [x.open_time for x in rows]!=expected:
            incomplete+=1
            continue
        out.append(Bar(
            bucket,
            rows[0].open,
            max(x.high for x in rows),
            min(x.low for x in rows),
            rows[-1].close,
            sum(x.volume for x in rows),
        ))
    return out,incomplete


def split_contiguous_12h(bars:list[Bar])->list[list[Bar]]:
    if not bars:
        return []
    ordered=sorted(bars,key=lambda x:x.open_time)
    segments=[[ordered[0]]]
    for b in ordered[1:]:
        if b.open_time-segments[-1][-1].open_time==TWELVE_H_MS:
            segments[-1].append(b)
        else:
            segments.append([b])
    return segments


def atr_series(bars:list[Bar],length:int=ATR_LEN)->list[float|None]:
    out:[float|None]=[None]*len(bars)
    if len(bars)<=length:
        return out
    trs:list[float|None]=[None]
    for i in range(1,len(bars)):
        c,p=bars[i],bars[i-1]
        trs.append(max(c.high-c.low,abs(c.high-p.close),abs(c.low-p.close)))
    seed=[float(x) for x in trs[1:length+1] if x is not None]
    if len(seed)!=length:
        return out
    value=mean(seed)
    out[length]=value
    for i in range(length+1,len(bars)):
        value=((value*(length-1))+float(trs[i]))/length
        out[i]=value
    return out


def latest_signal_candidate(symbol:str,bars:list[Bar])->SignalCandidate|None:
    if not bars:
        return None
    seg=split_contiguous_12h(bars)[-1]
    if len(seg)<=max(LOOKBACK,ATR_LEN):
        return None
    atr=atr_series(seg,ATR_LEN)
    i=len(seg)-1
    if atr[i] is None:
        return None
    s=seg[i]
    prior_high=max(x.high for x in seg[i-LOOKBACK:i])
    if not s.close>prior_high:
        return None
    signal_close=s.open_time+TWELVE_H_MS
    if signal_close<=FREEZE_MS:
        return None
    return SignalCandidate(
        symbol=symbol,
        signal_open_time=s.open_time,
        signal_close_time=signal_close,
        signal_low=s.low,
        atr=float(atr[i]),
        prior_high=prior_high,
    )


def bind_exact_entry(candidate:SignalCandidate,entry_open_time:int,entry_price:float)->Signal:
    if entry_open_time!=candidate.signal_close_time:
        raise ValueError("entry must equal next 12h open")
    if not isfinite(entry_price) or entry_price<=0:
        raise ValueError("invalid entry")
    stop=candidate.signal_low-STOP_ATR_MULT*candidate.atr
    if stop<=0 or entry_price<=stop:
        raise ValueError("pre-entry cancelled")
    risk=(entry_price-stop)/entry_price
    if risk<=0 or not isfinite(risk):
        raise ValueError("invalid initial risk")
    target=entry_price+TARGET_R*(entry_price-stop)
    payload={
        "cell_id":"DH03-12H-STANDALONE-FORWARD-V1",
        "symbol":candidate.symbol,
        "signal_open_time":candidate.signal_open_time,
        "entry_open_time":entry_open_time,
        "entry":entry_price,
        "stop":stop,
        "target":target,
        "risk":risk,
    }
    return Signal(
        symbol=candidate.symbol,
        signal_open_time=candidate.signal_open_time,
        signal_close_time=candidate.signal_close_time,
        entry_open_time=entry_open_time,
        entry=entry_price,
        stop=stop,
        target=target,
        initial_risk_fraction=risk,
        fingerprint=canonical_hash(payload),
    )


def funding_cashflow(
    funding_events:list[tuple[int,float]], entry_time:int, exit_time:int
)->tuple[float,int]:
    selected=[
        rate for ts,rate in funding_events
        if ts>entry_time and ts<exit_time
    ]
    if any(not isfinite(float(x)) for x in selected):
        raise ValueError("non-finite funding")
    return -sum(float(x) for x in selected),len(selected)


def resolve_minute_path(
    signal:Signal,
    minutes:list[tuple[int,float,float,float,float]],
    funding_events:list[tuple[int,float]],
)->MinuteOutcome:
    if not minutes:
        return MinuteOutcome(False,None,None,"EXECUTION_PATH_UNRESOLVED_END",None,None,0,None,None,None)
    deadline=signal.entry_open_time+MAX_HOLD_MS
    previous=None
    exit_t=None
    exit_px=None
    reason=None
    for t,o,hi,lo,c in minutes:
        if t<signal.entry_open_time:
            continue
        if t>deadline:
            break
        if previous is not None and t!=previous+MINUTE_MS:
            return MinuteOutcome(False,None,None,"EXECUTION_PATH_UNRESOLVED_GAP",None,None,0,None,None,None)
        previous=t
        if t==signal.entry_open_time and abs(o-signal.entry)>max(1e-10,abs(signal.entry)*1e-10):
            raise ValueError("entry price mismatch")
        if t==deadline:
            exit_t=t;exit_px=o;reason="TIME_EXIT_EXACT_MINUTE_OPEN";break
        if o<=signal.stop:
            exit_t=t;exit_px=o;reason="STOP_GAP_MINUTE_OPEN";break
        if o>=signal.target:
            exit_t=t;exit_px=signal.target;reason="TARGET_GAP_CAPPED_AT_TARGET";break
        stop_hit=lo<=signal.stop
        target_hit=hi>=signal.target
        if stop_hit and target_hit:
            exit_t=t;exit_px=signal.stop;reason="STOP_WINS_SAME_MINUTE_AMBIGUITY";break
        if stop_hit:
            exit_t=t;exit_px=signal.stop;reason="STOP";break
        if target_hit:
            exit_t=t;exit_px=signal.target;reason="TARGET";break
    if exit_t is None or exit_px is None:
        return MinuteOutcome(False,None,None,"EXECUTION_PATH_UNRESOLVED_END",None,None,0,None,None,None)
    price_gross=(exit_px-signal.entry)/signal.entry
    funding,nfund=funding_cashflow(funding_events,signal.entry_open_time,exit_t)
    economic=price_gross+funding
    base=(economic-BASE_COST)/(signal.initial_risk_fraction+BASE_COST)
    stress=(economic-STRESS_COST)/(signal.initial_risk_fraction+STRESS_COST)
    return MinuteOutcome(
        True,exit_t,exit_px,reason,price_gross,funding,nfund,economic,base,stress
    )
