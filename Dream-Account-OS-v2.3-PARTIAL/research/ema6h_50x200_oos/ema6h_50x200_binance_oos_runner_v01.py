from __future__ import annotations

import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from random import Random
from statistics import mean,median

EXPERIMENT_ID="EMA6H-50X200-BINANCE-OOS-2025_2026-001"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
STEP15=900_000
STEP6H=21_600_000
FAST=50;SLOW=200;H=6
BASE_COST=10.0;STRESS_COST=14.0
MIN_N=50;BOOT_REPS=10000;BOOT_SEED=20260919

@dataclass(frozen=True)
class Bar:
    t:int;o:float;h:float;l:float;c:float;v:float

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):h.update(ch)
    return h.hexdigest()

def load_source(root:Path,binding:dict):
    rec=json.loads((root/"EMA6H_50X200_BINANCE_OOS_2025_2026_001_SOURCE_GATE_V0.1.json").read_text())
    assert rec["status"]=="SOURCE_DATA_PASS"
    assert rec["archive_count"]==120
    assert rec["access_after_2026_08"] is False
    assert rec["outcome_evaluation_performed"] is False
    assert rec["signal_calculation_performed"] is False
    out={}
    for sym in SYMBOLS:
        p=root/"canonical_15m"/f"{sym}_15m.csv"
        assert p.is_file()
        assert sha256_file(p)==binding["canonical_sha256"][sym]
        rows=[]
        with p.open("r",encoding="utf-8",newline="") as fh:
            r=csv.DictReader(fh)
            assert tuple(r.fieldnames or ())==("open_time_ms","open","high","low","close","volume","close_time_ms")
            prev=None
            for x in r:
                t=int(x["open_time_ms"]);ct=int(x["close_time_ms"])
                assert t%STEP15==0 and ct==t+STEP15-1
                if prev is not None:assert t>prev
                prev=t
                o,hi,lo,c,v=map(float,(x["open"],x["high"],x["low"],x["close"],x["volume"]))
                rows.append(Bar(t,o,hi,lo,c,v))
        assert len(rows)==binding["row_count"][sym]
        out[sym]=rows
    return out,rec

def aggregate(xs:list[Bar]):
    buckets=defaultdict(list)
    for b in xs:buckets[b.t-(b.t%STEP6H)].append(b)
    out=[];inc=0
    for t in sorted(buckets):
        r=sorted(buckets[t],key=lambda z:z.t)
        exp=[t+i*STEP15 for i in range(24)]
        if len(r)!=24 or [z.t for z in r]!=exp:
            inc+=1;continue
        out.append(Bar(t,r[0].o,max(z.h for z in r),min(z.l for z in r),r[-1].c,sum(z.v for z in r)))
    return out,inc

def split_segments(bs:list[Bar]):
    if not bs:return []
    segs=[[bs[0]]]
    for b in bs[1:]:
        if b.t-segs[-1][-1].t==STEP6H:segs[-1].append(b)
        else:segs.append([b])
    return segs

def ema(vals:list[float],n:int):
    out=[None]*len(vals)
    if len(vals)<n:return out
    x=sum(vals[:n])/n;out[n-1]=x;a=2/(n+1)
    for i in range(n,len(vals)):
        x=a*vals[i]+(1-a)*x;out[i]=x
    return out

def derive(seg:list[Bar],sym:str):
    closes=[b.c for b in seg];ef=ema(closes,FAST);es=ema(closes,SLOW);out=[]
    for i in range(max(SLOW-1,1),len(seg)-1):
        if None in (ef[i-1],es[i-1],ef[i],es[i]):continue
        d0=float(ef[i-1])-float(es[i-1]);d1=float(ef[i])-float(es[i])
        direction=1 if d0<=0<d1 else (-1 if d0>=0>d1 else 0)
        if not direction:continue
        entry_i=i+1;exit_i=entry_i+H
        if exit_i>=len(seg):continue
        entry=seg[entry_i].o;exitp=seg[exit_i].o
        gross=direction*(exitp/entry-1)*10_000
        out.append({"symbol":sym,"direction":direction,"signal_open_time":seg[i].t,
                    "entry_open_time":seg[entry_i].t,"exit_open_time":seg[exit_i].t,
                    "entry":entry,"exit":exitp,"gross_bps":gross,
                    "base_net_bps":gross-BASE_COST,"stress_net_bps":gross-STRESS_COST})
    return out

def pf(vals):
    pos=sum(x for x in vals if x>0);neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else None

def maxdd(vals):
    equity=0.0;peak=0.0;dd=0.0
    for x in vals:
        equity+=x;peak=max(peak,equity);dd=min(dd,equity-peak)
    return dd

def metrics(evs,key="base_net_bps"):
    vals=[float(e[key]) for e in evs]
    pos=[x for x in vals if x>0]
    return {"n":len(vals),"mean":mean(vals) if vals else None,"median":median(vals) if vals else None,
            "pf":pf(vals),"positive_fraction":sum(x>0 for x in vals)/len(vals) if vals else None,
            "largest_positive_event_share":max(pos)/sum(pos) if pos and sum(pos)>0 else None,
            "cumulative_bps":sum(vals),"max_drawdown_bps":maxdd(vals) if vals else None}

def bootstrap(evs):
    groups=defaultdict(list)
    for e in evs:groups[e["entry_open_time"]//86_400_000].append(float(e["base_net_bps"]))
    days=sorted(groups);rng=Random(BOOT_SEED);draws=[]
    sums={d:sum(groups[d]) for d in days};ns={d:len(groups[d]) for d in days}
    for _ in range(BOOT_REPS):
        s=0.0;n=0
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))];s+=sums[d];n+=ns[d]
        draws.append(s/n)
    draws.sort()
    def pct(p):
        pos=(len(draws)-1)*p;lo=int(pos);hi=min(lo+1,len(draws)-1);f=pos-lo
        return draws[lo]*(1-f)+draws[hi]*f
    return {"days":len(days),"lower95":pct(.025),"upper95":pct(.975),
            "p_one_sided":(sum(x<=0 for x in draws)+1)/(len(draws)+1)}

def symbol_concentration(evs):
    pnl=defaultdict(float)
    for e in evs:
        if e["base_net_bps"]>0:pnl[e["symbol"]]+=float(e["base_net_bps"])
    total=sum(pnl.values())
    shares={s:(pnl[s]/total if total>0 else None) for s in SYMBOLS}
    return {"positive_pnl_bps_by_symbol":dict(sorted(pnl.items())),
            "positive_pnl_share_by_symbol":shares,
            "largest_symbol_positive_pnl_share":max((x for x in shares.values() if x is not None),default=None)}

def leave_one_symbol_out(evs):
    out={}
    for s in SYMBOLS:
        xs=[e for e in evs if e["symbol"]!=s]
        out[s]=metrics(xs)["mean"]
    return out

def temporal(evs):
    a=[];b=[]
    for e in evs:
        dt=datetime.fromtimestamp(e["entry_open_time"]/1000,tz=timezone.utc)
        (a if dt.year==2025 else b).append(e)
    return {"2025":metrics(a),"2026_JAN_AUG":metrics(b)}

def run(source:Path,binding_path:Path,outdir:Path):
    binding=json.loads(binding_path.read_text())
    assert binding["experiment_id"]==EXPERIMENT_ID and binding["status"]=="FROZEN_SOURCE_BINDING"
    raw,rec=load_source(source,binding)
    evs=[];derived={}
    for sym in SYMBOLS:
        bars,inc=aggregate(raw[sym]);segs=split_segments(bars);xs=[]
        for seg in segs:xs.extend(derive(seg,sym))
        evs.extend(xs)
        derived[sym]={"complete_6h_bars":len(bars),"incomplete_buckets_dropped":inc,"contiguous_segments":len(segs),"events":len(xs)}
    evs.sort(key=lambda e:(e["entry_open_time"],e["symbol"]))
    base=metrics(evs);stress=metrics(evs,"stress_net_bps");boot=bootstrap(evs);conc=symbol_concentration(evs);loo=leave_one_symbol_out(evs);temp=temporal(evs)
    gates={
      "n_ge_50":base["n"]>=MIN_N,
      "base_mean_positive":base["mean"] is not None and base["mean"]>0,
      "base_pf_gt_1":base["pf"] is not None and base["pf"]>1,
      "bootstrap_p_le_0_10":boot["p_one_sided"]<=0.10,
      "single_event_share_le_0_40":base["largest_positive_event_share"] is not None and base["largest_positive_event_share"]<=0.40,
      "symbol_share_le_0_40":conc["largest_symbol_positive_pnl_share"] is not None and conc["largest_symbol_positive_pnl_share"]<=0.40,
      "all_leave_one_symbol_out_positive":all(v is not None and v>0 for v in loo.values()),
      "2025_mean_positive":temp["2025"]["mean"] is not None and temp["2025"]["mean"]>0,
      "2026_jan_aug_mean_positive":temp["2026_JAN_AUG"]["mean"] is not None and temp["2026_JAN_AUG"]["mean"]>0,
    }
    if base["n"]<MIN_N:classification="INSUFFICIENT_SAMPLE"
    elif all(gates.values()):classification="TIER2_PROMOTED_CANDIDATE__QUASE_DIAMANTE"
    elif base["mean"] is not None and base["mean"]<0 and base["pf"] is not None and base["pf"]<1:classification="TIER4_REJECTED_EXACT_CANDIDATE"
    else:classification="TIER3_WATCHLIST"
    result={"experiment_id":EXPERIMENT_ID,"status":"OOS_COMPLETE","classification":classification,
            "base":base,"stress":stress,"bootstrap":boot,"symbol_concentration":conc,
            "leave_one_symbol_out_mean_bps":loo,"temporal_blocks":temp,"gates":gates,
            "derived_data_audit":derived,"event_count":len(evs),
            "source_binding":{"artifact_id":binding["artifact_id"],"artifact_digest":binding["artifact_digest"],
                              "source_run_id":binding["source_run_id"]},
            "governance":{"access_after_2026_08":False,"live_trading":False,"exchange_mutation":False,
                          "orders":False,"merge_to_main":False,"post_outcome_tuning":False}}
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"EMA6H_50X200_BINANCE_OOS_2025_2026_001_RESULT_V0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    fields=sorted({k for e in evs for k in e})
    with (outdir/"EMA6H_50X200_BINANCE_OOS_2025_2026_001_EVENT_LEDGER_V0.1.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(evs)
    print(json.dumps({"classification":classification,"event_count":len(evs),"base":base,"stress_mean":stress["mean"],
                      "bootstrap":boot,"gates":gates,"temporal":{k:{"n":v["n"],"mean":v["mean"],"pf":v["pf"]} for k,v in temp.items()}},indent=2,sort_keys=True))

def selftest():
    vals=[1.0]*250;e=ema(vals,50);assert e[-1]==1.0
    xs=[Bar(i*STEP15,100,101,99,100,1) for i in range(48)];b,inc=aggregate(xs);assert len(b)==2 and inc==0
    print("SELF_TEST=PASS")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source-dir",type=Path);ap.add_argument("--binding",type=Path);ap.add_argument("--output-dir",type=Path);ap.add_argument("--self-test",action="store_true");a=ap.parse_args()
    if a.self_test:selftest();return
    if not(a.source_dir and a.binding and a.output_dir):raise SystemExit("source-dir binding output-dir required")
    run(a.source_dir,a.binding,a.output_dir)
if __name__=="__main__":main()
