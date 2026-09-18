from __future__ import annotations

import bisect
import hashlib
import json
from dataclasses import asdict, dataclass
from math import isfinite
from statistics import mean
from typing import Any

BAR_MS=43_200_000
MIN_MS=60_000
LOOKBACK=40
ATR_LEN=28
TARGET_R=3.0
MAX_HOLD_BARS=80
MAX_HOLD_MS=BAR_MS*MAX_HOLD_BARS
BASE_COST=0.002
STRESS_COST=0.003
FIRST_SIGNAL_BAR_OPEN_MS=1789732800000

@dataclass(frozen=True)
class MinuteBar:
    open_time:int
    open:float
    high:float
    low:float
    close:float

@dataclass(frozen=True)
class Bar12H:
    open_time:int
    open:float
    high:float
    low:float
    close:float

@dataclass(frozen=True)
class Signal:
    symbol:str
    signal_open_time:int
    entry_open_time:int
    entry:float
    stop:float
    target:float
    initial_risk_fraction:float
    fingerprint:str

@dataclass(frozen=True)
class Trade:
    symbol:str
    signal_open_time:int
    entry_time:int
    exit_time:int|None
    entry_price:float
    exit_price:float|None
    stop:float
    target:float
    initial_risk_fraction:float
    exit_reason:str
    price_gross_return:float|None
    funding_return:float|None
    funding_event_count:int
    economic_gross_return:float|None
    base_net_r:float|None
    stress_net_r:float|None
    execution_path_unresolved:bool

def canonical_hash(x:Any)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def aggregate_12h(minutes:list[MinuteBar])->tuple[list[Bar12H],int]:
    buckets:dict[int,list[MinuteBar]]={}
    for m in minutes:
        b=m.open_time-(m.open_time%BAR_MS)
        buckets.setdefault(b,[]).append(m)
    out=[]; incomplete=0
    for b in sorted(buckets):
        rows=sorted(buckets[b],key=lambda x:x.open_time)
        if len(rows)!=720 or any(rows[i].open_time!=b+i*MIN_MS for i in range(len(rows))):
            incomplete+=1
            continue
        out.append(Bar12H(b,rows[0].open,max(x.high for x in rows),min(x.low for x in rows),rows[-1].close))
    return out,incomplete

def atr_series(bars:list[Bar12H],length:int=ATR_LEN)->list[float|None]:
    out:[float|None]=[None]*len(bars)
    if len(bars)<=length:
        return out
    trs:[float|None]=[None]
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

def derive_signals(symbol:str,bars:list[Bar12H])->tuple[list[Signal],dict[str,int]]:
    atr=atr_series(bars,ATR_LEN)
    signals=[]; raw=cancelled=prefreeze=0
    for i in range(max(LOOKBACK,ATR_LEN),len(bars)-1):
        s=bars[i]
        if s.open_time<FIRST_SIGNAL_BAR_OPEN_MS:
            prefreeze+=1
            continue
        if atr[i] is None:
            continue
        prior_high=max(x.high for x in bars[i-LOOKBACK:i])
        if not s.close>prior_high:
            continue
        raw+=1
        stop=s.low-0.25*float(atr[i])
        entry=bars[i+1].open
        if stop<=0 or entry<=stop:
            cancelled+=1
            continue
        risk=(entry-stop)/entry
        if risk<=0 or not isfinite(risk):
            cancelled+=1
            continue
        target=entry+TARGET_R*(entry-stop)
        payload={"symbol":symbol,"signal_open_time":s.open_time,"entry_open_time":bars[i+1].open_time,"entry":entry,"stop":stop,"target":target,"risk":risk}
        signals.append(Signal(symbol,s.open_time,bars[i+1].open_time,entry,stop,target,risk,canonical_hash(payload)))
    return signals,{"raw_triggers":raw,"cancelled":cancelled,"prefreeze_or_crossing_bars_ignored":prefreeze}

def _funding_cashflow(times:list[int],rates:list[float],entry_t:int,exit_t:int)->tuple[float,int]:
    lo=bisect.bisect_right(times,entry_t)
    hi=bisect.bisect_left(times,exit_t)
    selected=rates[lo:hi]
    return -sum(selected),len(selected)

def simulate_signal(sig:Signal,minutes:list[MinuteBar],funding_times:list[int],funding_rates:list[float])->Trade:
    mtimes=[x.open_time for x in minutes]
    i=bisect.bisect_left(mtimes,sig.entry_open_time)
    if i>=len(minutes) or mtimes[i]!=sig.entry_open_time:
        return Trade(sig.symbol,sig.signal_open_time,sig.entry_open_time,None,sig.entry,None,sig.stop,sig.target,sig.initial_risk_fraction,"EXECUTION_PATH_UNRESOLVED_ENTRY",None,None,0,None,None,None,True)
    if abs(minutes[i].open-sig.entry)>max(1e-10,abs(sig.entry)*1e-10):
        raise RuntimeError("entry price mismatch")
    deadline=sig.entry_open_time+MAX_HOLD_MS
    prev_t=None; exit_t=None; px=None; reason=None
    for j in range(i,len(minutes)):
        b=minutes[j]
        if b.open_time>deadline:
            break
        if prev_t is not None and b.open_time!=prev_t+MIN_MS:
            return Trade(sig.symbol,sig.signal_open_time,sig.entry_open_time,None,sig.entry,None,sig.stop,sig.target,sig.initial_risk_fraction,"EXECUTION_PATH_UNRESOLVED_GAP",None,None,0,None,None,None,True)
        prev_t=b.open_time
        if b.open_time==deadline:
            px=b.open; reason="TIME_EXIT_EXACT_MINUTE_OPEN"; exit_t=b.open_time; break
        if b.open<=sig.stop:
            px=b.open; reason="STOP_GAP_MINUTE_OPEN"; exit_t=b.open_time; break
        if b.open>=sig.target:
            px=sig.target; reason="TARGET_GAP_CAPPED_AT_TARGET"; exit_t=b.open_time; break
        sh=b.low<=sig.stop
        th=b.high>=sig.target
        if sh and th:
            px=sig.stop; reason="STOP_WINS_SAME_MINUTE_AMBIGUITY"; exit_t=b.open_time; break
        if sh:
            px=sig.stop; reason="STOP"; exit_t=b.open_time; break
        if th:
            px=sig.target; reason="TARGET"; exit_t=b.open_time; break
    if exit_t is None or px is None or reason is None:
        return Trade(sig.symbol,sig.signal_open_time,sig.entry_open_time,None,sig.entry,None,sig.stop,sig.target,sig.initial_risk_fraction,"UNRESOLVED_END_OF_AVAILABLE_SOURCE",None,None,0,None,None,None,True)
    price_gross=(px-sig.entry)/sig.entry
    funding,nfund=_funding_cashflow(funding_times,funding_rates,sig.entry_open_time,exit_t)
    econ=price_gross+funding
    base=(econ-BASE_COST)/(sig.initial_risk_fraction+BASE_COST)
    stress=(econ-STRESS_COST)/(sig.initial_risk_fraction+STRESS_COST)
    return Trade(sig.symbol,sig.signal_open_time,sig.entry_open_time,exit_t,sig.entry,px,sig.stop,sig.target,sig.initial_risk_fraction,reason,price_gross,funding,nfund,econ,base,stress,False)

def evaluate_symbol(symbol:str,minutes:list[MinuteBar],funding_times:list[int],funding_rates:list[float])->dict[str,Any]:
    bars,incomplete=aggregate_12h(minutes)
    signals,diag=derive_signals(symbol,bars)
    rows=[]; overlap=0; active_until=None
    for sig in signals:
        if active_until is not None and sig.entry_open_time<=active_until:
            overlap+=1
            continue
        row=simulate_signal(sig,minutes,funding_times,funding_rates)
        rows.append(row)
        active_until=row.exit_time if row.exit_time is not None else sig.entry_open_time+MAX_HOLD_MS
    return {"symbol":symbol,"complete_12h_bars":len(bars),"incomplete_12h_buckets":incomplete,"signal_diagnostics":diag,"selected_trades":len(rows),"overlap_skipped":overlap,"resolved_trades":sum(not x.execution_path_unresolved for x in rows),"unresolved_trades":sum(x.execution_path_unresolved for x in rows),"trades":[asdict(x) for x in rows]}
