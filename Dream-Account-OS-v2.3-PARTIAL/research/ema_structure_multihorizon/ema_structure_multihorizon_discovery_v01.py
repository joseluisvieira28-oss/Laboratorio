from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from random import Random
from statistics import mean, median
from typing import Any

EXPERIMENT_ID = "EMA-STRUCTURE-MULTIHORIZON-001"
SYMBOLS = ("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
FIFTEEN_MIN_MS = 900_000
TIMEFRAMES = {
    "15m": 15*60_000,
    "30m": 30*60_000,
    "1H": 60*60_000,
    "2H": 2*60*60_000,
    "4H": 4*60*60_000,
    "6H": 6*60*60_000,
    "8H": 8*60*60_000,
    "12H": 12*60*60_000,
    "1D": 24*60*60_000,
    "2D": 2*24*60*60_000,
    "3D": 3*24*60*60_000,
}
PARENT_TF = {
    "15m":"1H","30m":"2H","1H":"4H","2H":"6H","4H":"12H","6H":"12H",
    "8H":"1D","12H":"1D","1D":"3D","2D":"3D","3D":None,
}
EMA_LENGTHS=(20,50,200)
ATR_LEN=14
SLOPE_LAG=5
PRIMARY_H=6
SECONDARY_H=(1,3,12)
BASE_COST_BPS=10.0
STRESS_COST_BPS=14.0
MIN_EVENTS=100
BOOT_REPS=3000
BOOT_SEED=20260919
Q_ALPHA=0.05

@dataclass(frozen=True)
class Bar:
    open_time:int
    open:float
    high:float
    low:float
    close:float
    volume:float
    close_time:int

@dataclass
class FeatureRow:
    bar:Bar
    ema20:float|None
    ema50:float|None
    ema200:float|None
    atr14:float|None
    width_atr:float|None
    slope20_atr:float|None
    slope50_atr:float|None
    stack_dir:int
    fast_mid_dir:int
    segment_id:int

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_15m(path:Path)->list[Bar]:
    out=[]
    with path.open("r",encoding="utf-8",newline="") as fh:
        r=csv.DictReader(fh)
        expected=("open_time","open","high","low","close","volume","minute_count")
        if tuple(r.fieldnames or ()) != expected:
            raise ValueError(f"schema mismatch {path}: {r.fieldnames}")
        prev=None
        for x in r:
            t=int(x["open_time"])
            if int(x["minute_count"])!=15 or t%FIFTEEN_MIN_MS:
                raise ValueError(f"noncanonical 15m row {path}:{t}")
            if prev is not None and t<=prev:
                raise ValueError(f"timestamps not strictly increasing {path}:{t}")
            prev=t
            o,h,l,c,v=map(float,(x["open"],x["high"],x["low"],x["close"],x["volume"]))
            if not(min(o,h,l,c)>0 and v>=0 and h>=max(o,c,l) and l<=min(o,c,h)):
                raise ValueError(f"invalid OHLC {path}:{t}")
            out.append(Bar(t,o,h,l,c,v,t+FIFTEEN_MIN_MS-1))
    return out

def aggregate(candles:list[Bar], bar_ms:int)->tuple[list[Bar],int]:
    if bar_ms==FIFTEEN_MIN_MS:
        return candles[:],0
    expected_n=bar_ms//FIFTEEN_MIN_MS
    buckets:dict[int,list[Bar]]=defaultdict(list)
    for c in candles:
        b=c.open_time-(c.open_time%bar_ms)
        buckets[b].append(c)
    out=[]; incomplete=0
    for b in sorted(buckets):
        rows=sorted(buckets[b],key=lambda x:x.open_time)
        expected=[b+i*FIFTEEN_MIN_MS for i in range(expected_n)]
        if len(rows)!=expected_n or [x.open_time for x in rows]!=expected:
            incomplete+=1
            continue
        out.append(Bar(b,rows[0].open,max(x.high for x in rows),min(x.low for x in rows),
                       rows[-1].close,sum(x.volume for x in rows),b+bar_ms-1))
    return out,incomplete

def split_segments(bars:list[Bar],bar_ms:int)->list[list[Bar]]:
    if not bars: return []
    segs=[[bars[0]]]
    for b in bars[1:]:
        if b.open_time-segs[-1][-1].open_time==bar_ms:
            segs[-1].append(b)
        else:
            segs.append([b])
    return segs

def ema(values:list[float],length:int)->list[float|None]:
    out=[None]*len(values)
    if len(values)<length:return out
    val=sum(values[:length])/length
    out[length-1]=val
    a=2.0/(length+1.0)
    for i in range(length,len(values)):
        val=a*values[i]+(1-a)*val
        out[i]=val
    return out

def atr(bars:list[Bar],length:int)->list[float|None]:
    out=[None]*len(bars)
    if len(bars)<=length:return out
    trs=[None]
    for i in range(1,len(bars)):
        b,p=bars[i],bars[i-1]
        trs.append(max(b.high-b.low,abs(b.high-p.close),abs(b.low-p.close)))
    val=sum(float(x) for x in trs[1:length+1])/length
    out[length]=val
    for i in range(length+1,len(bars)):
        val=((val*(length-1))+float(trs[i]))/length
        out[i]=val
    return out

def features_for_segment(seg:list[Bar], segment_id:int)->list[FeatureRow]:
    closes=[b.close for b in seg]
    e20,e50,e200=(ema(closes,n) for n in EMA_LENGTHS)
    a14=atr(seg,ATR_LEN)
    rows=[]
    for i,b in enumerate(seg):
        vals=(e20[i],e50[i],e200[i])
        at=a14[i]
        width=s20=s50=None
        stack=fastmid=0
        if e20[i] is not None and e50[i] is not None:
            fastmid=1 if e20[i]>e50[i] else (-1 if e20[i]<e50[i] else 0)
        if all(x is not None for x in vals):
            if e20[i]>e50[i]>e200[i]: stack=1
            elif e20[i]<e50[i]<e200[i]: stack=-1
            if at is not None and at>0:
                width=(max(float(x) for x in vals)-min(float(x) for x in vals))/at
                if i>=SLOPE_LAG and e20[i-SLOPE_LAG] is not None and e50[i-SLOPE_LAG] is not None:
                    s20=(float(e20[i])-float(e20[i-SLOPE_LAG]))/at
                    s50=(float(e50[i])-float(e50[i-SLOPE_LAG]))/at
        rows.append(FeatureRow(b,e20[i],e50[i],e200[i],at,width,s20,s50,stack,fastmid,segment_id))
    return rows

def build_features(source:dict[str,list[Bar]]):
    feat={}; meta={}
    for tf,ms in TIMEFRAMES.items():
        feat[tf]={}; meta[tf]={}
        for sym in SYMBOLS:
            bars,inc=aggregate(source[sym],ms)
            rows=[]
            segs=split_segments(bars,ms)
            for segment_id,seg in enumerate(segs):
                rows.extend(features_for_segment(seg,segment_id))
            rows.sort(key=lambda r:r.bar.open_time)
            feat[tf][sym]=rows
            meta[tf][sym]={"bars":len(rows),"incomplete_buckets":inc,"contiguous_segments":len(segs)}
    return feat,meta

def directional_forward(rows:list[FeatureRow], i:int, direction:int, h:int):
    entry_i=i+1
    exit_i=entry_i+h
    if direction not in (-1,1) or exit_i>=len(rows):
        return None
    segment_id=rows[i].segment_id
    if rows[entry_i].segment_id!=segment_id or rows[exit_i].segment_id!=segment_id:
        return None
    entry=rows[entry_i].bar.open
    exitp=rows[exit_i].bar.open
    gross=direction*(exitp/entry-1.0)*10_000
    return gross,gross-BASE_COST_BPS,gross-STRESS_COST_BPS

def parent_context(feat, tf:str, sym:str, signal_close:int, direction:int):
    ptf=PARENT_TF[tf]
    if ptf is None:
        return {"parent_tf":None,"parent_fast_mid_aligned":None,"parent_full_stack_aligned":None}
    rows=feat[ptf][sym]
    closes=[r.bar.close_time for r in rows]
    j=bisect.bisect_right(closes,signal_close)-1
    if j<0:
        return {"parent_tf":ptf,"parent_fast_mid_aligned":None,"parent_full_stack_aligned":None}
    r=rows[j]
    if signal_close-r.bar.close_time>=TIMEFRAMES[ptf]:
        return {"parent_tf":ptf,"parent_fast_mid_aligned":None,"parent_full_stack_aligned":None}
    return {"parent_tf":ptf,
            "parent_fast_mid_aligned":r.fast_mid_dir==direction,
            "parent_full_stack_aligned":r.stack_dir==direction}

def derive_events(feat):
    events=[]
    for tf in TIMEFRAMES:
        for sym in SYMBOLS:
            rows=feat[tf][sym]
            for i in range(1,len(rows)-1):
                r,p=rows[i],rows[i-1]
                if r.segment_id!=p.segment_id:
                    continue
                for pair,a_now,b_now,a_prev,b_prev in (
                    ("EMA20x50",r.ema20,r.ema50,p.ema20,p.ema50),
                    ("EMA50x200",r.ema50,r.ema200,p.ema50,p.ema200),
                ):
                    if None in (a_now,b_now,a_prev,b_prev):
                        continue
                    d0=float(a_prev)-float(b_prev); d1=float(a_now)-float(b_now)
                    direction=1 if d0<=0<d1 else (-1 if d0>=0>d1 else 0)
                    if direction:
                        rec={"family":"CROSSOVER","cell":f"{tf}:{pair}","timeframe":tf,"symbol":sym,
                             "event_open_time":r.bar.open_time,"signal_close_time":r.bar.close_time,
                             "direction":direction,"pair":pair}
                        rec.update(parent_context(feat,tf,sym,r.bar.close_time,direction))
                        for h in (PRIMARY_H,*SECONDARY_H):
                            o=directional_forward(rows,i,direction,h)
                            if o:
                                rec[f"h{h}_gross_bps"],rec[f"h{h}_net_bps"],rec[f"h{h}_stress_bps"]=o
                        events.append(rec)

                def geometry_ok(k:int)->bool:
                    if k<SLOPE_LAG: return False
                    x=rows[k]; old=rows[k-SLOPE_LAG]
                    if x.segment_id!=old.segment_id: return False
                    if x.stack_dir==0 or x.width_atr is None or old.width_atr is None or x.slope20_atr is None or x.slope50_atr is None:
                        return False
                    d=x.stack_dir
                    return d*x.slope20_atr>0 and d*x.slope50_atr>0 and x.width_atr>old.width_atr

                now=geometry_ok(i); prev=geometry_ok(i-1)
                if now and not prev:
                    direction=r.stack_dir
                    rec={"family":"GEOMETRY","cell":f"{tf}:ALIGNED_EXPANSION_ONSET","timeframe":tf,"symbol":sym,
                         "event_open_time":r.bar.open_time,"signal_close_time":r.bar.close_time,
                         "direction":direction,"pair":None,"width_atr":r.width_atr,
                         "slope20_atr":r.slope20_atr,"slope50_atr":r.slope50_atr}
                    rec.update(parent_context(feat,tf,sym,r.bar.close_time,direction))
                    for h in (PRIMARY_H,*SECONDARY_H):
                        o=directional_forward(rows,i,direction,h)
                        if o:
                            rec[f"h{h}_gross_bps"],rec[f"h{h}_net_bps"],rec[f"h{h}_stress_bps"]=o
                    events.append(rec)
    events.sort(key=lambda x:(x["event_open_time"],x["timeframe"],x["symbol"],x["family"],x["cell"]))
    return events

def percentile(xs:list[float],p:float)->float:
    xs=sorted(xs)
    if not xs:return float("nan")
    if p<=0:return xs[0]
    if p>=1:return xs[-1]
    pos=(len(xs)-1)*p; lo=int(pos); hi=min(lo+1,len(xs)-1); f=pos-lo
    return xs[lo]*(1-f)+xs[hi]*f

def bootstrap_by_day(events:list[dict[str,Any]], key:str):
    # Exact same UTC-day block bootstrap semantics as the freeze, implemented
    # through per-day sums/counts rather than repeatedly materializing event lists.
    # Sampling a day duplicates all observations in that day, so this is
    # mathematically identical while substantially reducing runtime.
    groups=defaultdict(list)
    for e in events:
        if key in e:
            day=e["event_open_time"]//86_400_000
            groups[day].append(float(e[key]))
    days=sorted(groups)
    vals=[v for d in days for v in groups[d]]
    if not vals:
        return {"n":0,"days":0,"mean":None,"median":None,"lower95":None,"upper95":None,"p_one_sided":None}
    day_sum={d:sum(groups[d]) for d in days}
    day_n={d:len(groups[d]) for d in days}
    rng=Random(BOOT_SEED)
    draws=[]
    nd=len(days)
    for _ in range(BOOT_REPS):
        total=0.0
        count=0
        for __ in range(nd):
            d=days[rng.randrange(nd)]
            total+=day_sum[d]
            count+=day_n[d]
        draws.append(total/count)
    p=(sum(x<=0 for x in draws)+1)/(len(draws)+1)
    return {"n":len(vals),"days":len(days),"mean":mean(vals),"median":median(vals),
            "lower95":percentile(draws,0.025),"upper95":percentile(draws,0.975),"p_one_sided":p}

def bh_qvalues(items:list[tuple[str,float]]):
    valid=sorted([(k,p) for k,p in items if p is not None and math.isfinite(p)],key=lambda z:z[1])
    m=len(valid); out={}
    if not m:return out
    raw=[min(1.0,p*m/(i+1)) for i,(k,p) in enumerate(valid)]
    for i in range(m-2,-1,-1):
        raw[i]=min(raw[i],raw[i+1])
    for (k,_),q in zip(valid,raw): out[k]=q
    return out

def descriptive_events(events:list[dict[str,Any]], key:str):
    vals=[float(e[key]) for e in events if key in e]
    days=len({e["event_open_time"]//86_400_000 for e in events if key in e})
    return {"n":len(vals),"days":days,"mean":mean(vals) if vals else None,"median":median(vals) if vals else None}

def summarize(events):
    cells=defaultdict(list)
    for e in events:
        cells[e["cell"]].append(e)
    summaries={}; pvals=[]
    for cell,evs in sorted(cells.items()):
        # Only the primary BASE series needs the frozen 3,000-draw UTC-day
        # block bootstrap because only its 95% lower bound and p-value feed
        # the scientific gate. Stress and all secondary diagnostics require
        # descriptive means only under the frozen contract.
        b=bootstrap_by_day(evs,f"h{PRIMARY_H}_net_bps")
        s=descriptive_events(evs,f"h{PRIMARY_H}_stress_bps")
        summaries[cell]={"family":evs[0]["family"],"timeframe":evs[0]["timeframe"],
                         "events_total":len(evs),"primary_horizon_bars":PRIMARY_H,
                         "base":b,"stress":s,
                         "parent_aligned_count":sum(1 for e in evs if e.get("parent_fast_mid_aligned") is True),
                         "parent_context_available_count":sum(1 for e in evs if e.get("parent_fast_mid_aligned") is not None)}
        if b["p_one_sided"] is not None:
            pvals.append((cell,float(b["p_one_sided"])))
    q=bh_qvalues(pvals)
    for cell,d in summaries.items():
        n=d["base"]["n"]; qv=q.get(cell); reasons=[]
        if n<MIN_EVENTS:
            classification="INSUFFICIENT_SAMPLE"; reasons.append("n_below_100")
        else:
            if d["base"]["mean"] is None or d["base"]["mean"]<=0: reasons.append("base_mean_not_positive")
            if d["base"]["lower95"] is None or d["base"]["lower95"]<=0: reasons.append("bootstrap_lower95_not_positive")
            if d["stress"]["mean"] is None or d["stress"]["mean"]<=0: reasons.append("stress_mean_not_positive")
            if qv is None or qv>Q_ALPHA: reasons.append("BH_FDR_q_above_0.05")
            classification="SURVIVES_DISCOVERY" if not reasons else "NO_EDGE"
        d["bh_fdr_q"]=qv
        d["classification"]=classification
        d["failed_conditions"]=reasons
        aligned=[e for e in cells[cell] if e.get("parent_fast_mid_aligned") is True]
        nonaligned=[e for e in cells[cell] if e.get("parent_fast_mid_aligned") is False]
        d["secondary_parent_alignment"]={
            "aligned":descriptive_events(aligned,f"h{PRIMARY_H}_net_bps"),
            "not_aligned":descriptive_events(nonaligned,f"h{PRIMARY_H}_net_bps"),
            "bootstrap_not_used_for_secondary_diagnostic":True,
            "rescue_authorized":False,
        }
        d["secondary_horizons"]={}
        for h in SECONDARY_H:
            d["secondary_horizons"][str(h)]=descriptive_events(cells[cell],f"h{h}_net_bps")
    return summaries

def verify_source(source_dir:Path, binding_path:Path):
    bind=json.loads(binding_path.read_text(encoding="utf-8"))
    rec=json.loads((source_dir/"HTF_DIAMOND_HUNT_001_SOURCE_GATE_V0.1.json").read_text(encoding="utf-8"))
    assert rec["status"]=="SOURCE_DATA_PASS"
    assert rec["source_fingerprint"]==bind["source_fingerprint"]=="08402ecb8931e42a0766370f55e46adc3de02474ce3a6128f4b2cdd89bb4ac78"
    assert bind["artifact_id"]==10434938955
    for y in (2023,2024,2025,2026):
        assert rec[f"access_{y}_performed"] is False
    source={}
    for sym in SYMBOLS:
        p=source_dir/"canonical_15m"/f"{sym}_15m.csv"
        assert p.is_file()
        assert sha256_file(p)==bind["canonical_15m"][sym]["sha256"]
        source[sym]=load_15m(p)
    return source,bind,rec

def self_test():
    vals=[1.0]*250
    e=ema(vals,20)
    assert e[-1]==1.0
    xs=[Bar(i*FIFTEEN_MIN_MS,100,101,99,100,1,(i+1)*FIFTEEN_MIN_MS-1) for i in range(8)]
    out,inc=aggregate(xs,30*60_000)
    assert len(out)==4 and inc==0
    broken=xs[:3]+xs[4:]
    out2,inc2=aggregate(broken,30*60_000)
    assert inc2>=1
    assert PARENT_TF["1H"]=="4H"
    print("SELF_TEST=PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dir",type=Path)
    ap.add_argument("--binding",type=Path)
    ap.add_argument("--output-dir",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not(args.source_dir and args.binding and args.output_dir):
        raise SystemExit("source-dir, binding, output-dir required")
    source,bind,rec=verify_source(args.source_dir,args.binding)
    feat,meta=build_features(source)
    events=derive_events(feat)
    summaries=summarize(events)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    ledger=args.output_dir/"EMA_STRUCTURE_MULTIHORIZON_001_EVENT_LEDGER_V0.1.csv"
    fields=sorted({k for e in events for k in e.keys()})
    with ledger.open("w",encoding="utf-8",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(events)
    result={
        "experiment_id":EXPERIMENT_ID,
        "status":"DISCOVERY_COMPLETE",
        "source":{"artifact_id":bind["artifact_id"],"artifact_digest":bind["artifact_digest"],
                  "source_fingerprint":bind["source_fingerprint"],"years":[2021,2022],"market":"Binance Spot"},
        "timeframes":list(TIMEFRAMES),
        "ema_lengths":list(EMA_LENGTHS),
        "atr_length":ATR_LEN,
        "slope_lag_bars":SLOPE_LAG,
        "primary_horizon_bars":PRIMARY_H,
        "secondary_horizons_bars":list(SECONDARY_H),
        "base_cost_bps":BASE_COST_BPS,
        "stress_cost_bps":STRESS_COST_BPS,
        "minimum_events":MIN_EVENTS,
        "bh_fdr_alpha":Q_ALPHA,
        "event_count":len(events),
        "continuity_enforcement":{"segment_id_propagated":True,"event_cross_gap_forbidden":True,"forward_window_cross_gap_forbidden":True,"stale_parent_context_forbidden":True,"technical_amendment":"TECHNICAL_AMENDMENT_03"},
        "derived_data_meta":meta,
        "cells":summaries,
        "governance":{"2023_access":False,"2024_access":False,"2025_access":False,"2026_access":False,
                      "live_trading":False,"exchange_mutation":False,"orders":False,"alerts_webhooks":False,
                      "merge_to_main":False,"post_outcome_tuning":False,
                      "parent_alignment_is_secondary_and_cannot_rescue":True},
    }
    out=args.output_dir/"EMA_STRUCTURE_MULTIHORIZON_001_DISCOVERY_RESULT_V0.1.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"status":result["status"],"event_count":len(events),
                      "classifications":{k:v["classification"] for k,v in summaries.items()}},indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
