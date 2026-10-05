#!/usr/bin/env python3
# BINANCE-LISTING-FIRST-SECONDS-CASCADE-002
# V0.1 2025 DEVELOPMENT — ONE SHOT
# 2025 is DEVELOPMENT ONLY. 2026 remains unopened.

import csv
import gzip
import io
import json
import statistics
import urllib.request
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

PARENT_FREEZE="5110f7ebda90809de56155b4605b9621bd8fb781"
IDENTITY_RESOLUTION="9744ce8e12b99e644a0f9bee55b1d89689a9b0dd"
METRIC_SPEC="c805e09e4ab879438b8ea98ca025a439cd22b22f"
ACTIVATION="45d82eebe301041bfc39bb51298095d58f8259e6"
LABEL_SPEC="12ef98b1f72ca0650a1f6e47e1c579b279c42637"
N_SPEC="0e6619b9e0fdb7066841f0fbf6c8379899795280"

EVENTS=[
    ("COOKIE","COOKIE_USDT",1736499327639),
    ("1000CHEEMS","CHEEMS_USDT",1739085031264),
    ("KMNO","KMNO_USDT",1746530720814),
    ("PUMP","PUMP_USDT",1757590673797),
    ("AVNT","AVNT_USDT",1757908021934),
    ("GIGGLE","GIGGLE_USDT",1761361338417),
    ("F","F_USDT",1761361338417),
    ("MET","MET_USDT",1763028026501),
]

HORIZONS_S=[1,5,10,30,60]
LATENCIES_MS=[250,500,1000,2000,5000,10000,30000,60000]
COSTS={"net20":0.0020,"net50":0.0050,"net100":0.0100}

def month(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).strftime("%Y%m")

def parse_ts_us(raw):
    try:
        return int(Decimal(raw.strip())*Decimal(1_000_000))
    except (InvalidOperation,ValueError):
        return None

def parse_dealid(raw, fallback):
    try:
        return (0,int(raw))
    except Exception:
        return (1,fallback)

def median_or_none(xs):
    xs=[x for x in xs if x is not None]
    return statistics.median(xs) if xs else None

def hit_rate(xs):
    xs=[x for x in xs if x is not None]
    return (sum(x>0 for x in xs)/len(xs)) if xs else None

def loo_positive(xs):
    xs=[x for x in xs if x is not None]
    if len(xs)<2:
        return False
    return all(statistics.median([v for j,v in enumerate(xs) if j!=i])>0 for i in range(len(xs)))

def positive_concentration(xs):
    xs=[x for x in xs if x is not None]
    pos=[max(0.0,x) for x in xs]
    s=sum(pos)
    return max(pos)/s if s>0 else 1.0

def net_return(entry,exit_,round_trip_cost):
    half=round_trip_cost/2.0
    return (exit_*(1-half))/(entry*(1+half))-1

def download_relevant(asset,market,t0_ms):
    ym=month(t0_ms)
    url=f"https://download.gatedata.org/spot/deals/{ym}/{market}-{ym}.csv.gz"
    t0_us=t0_ms*1000
    lo=t0_us-10*60*1_000_000
    hi=t0_us+60*1_000_000

    rows=[]
    req=urllib.request.Request(
        url,
        headers={"User-Agent":"Mozilla/5.0 CryptoLabFirstSecondsV01Development/1.0","Accept":"application/gzip,*/*"},
    )
    with urllib.request.urlopen(req,timeout=90) as resp:
        with gzip.GzipFile(fileobj=resp) as gz:
            txt=io.TextIOWrapper(gz,encoding="utf-8",errors="replace",newline="")
            for idx,row in enumerate(csv.reader(txt)):
                if len(row)<4:
                    continue
                ts=parse_ts_us(row[0])
                if ts is None or ts<lo or ts>hi:
                    continue
                try:
                    price=float(row[2])
                    amount=float(row[3])
                except (ValueError,TypeError):
                    continue
                dealid=parse_dealid(row[1],idx)
                rows.append((ts,dealid,idx,price,amount))
    rows.sort(key=lambda x:(x[0],x[1],x[2]))
    return rows

def last_trade_at_or_before(post, cutoff):
    xs=[x for x in post if x[0]<=cutoff]
    return xs[-1] if xs else None

def first_trade_at_or_after(post, threshold, upper):
    for x in post:
        if x[0]>=threshold and x[0]<=upper:
            return x
    return None

def event_metrics(asset,market,t0_ms):
    t0=t0_ms*1000
    trades=download_relevant(asset,market,t0_ms)
    pre=[x for x in trades if t0-10*1_000_000<=x[0]<t0]
    post=[x for x in trades if t0<=x[0]<=t0+60*1_000_000]
    if not pre or not post:
        return {"asset":asset,"market":market,"status":"SOURCE_FAIL_AT_DEVELOPMENT"}

    p0trade=pre[-1]
    p0=p0trade[3]
    exit60=post[-1]
    exit60_price=exit60[3]

    r={}
    horizon_prices={}
    for h in HORIZONS_S:
        tr=last_trade_at_or_before(post,t0+h*1_000_000)
        rr=(tr[3]/p0-1) if tr is not None else None
        r[f"r{h}s"]=rr
        horizon_prices[h]=tr[3] if tr is not None else None

    # Fixed 5-second baseline blocks: [T0-10m,T0-1m), 540s / 5s = 108 blocks.
    baseline_start=t0-600*1_000_000
    baseline_end=t0-60*1_000_000
    n_blocks=108
    base_counts=[0]*n_blocks
    base_qv=[0.0]*n_blocks
    for tr in trades:
        if baseline_start<=tr[0]<baseline_end:
            i=(tr[0]-baseline_start)//(5*1_000_000)
            if 0<=i<n_blocks:
                i=int(i)
                base_counts[i]+=1
                base_qv[i]+=tr[3]*tr[4]

    base_med_count=statistics.median(base_counts)
    base_med_qv=statistics.median(base_qv)

    activity={}
    for h in HORIZONS_S:
        subset=[x for x in post if x[0]<=t0+h*1_000_000]
        cnt=len(subset)
        qv=sum(x[3]*x[4] for x in subset)
        expected_count=base_med_count*(h/5.0)
        expected_qv=base_med_qv*(h/5.0)
        activity[f"trades_0_{h}s"]=cnt
        activity[f"quote_volume_0_{h}s"]=qv
        activity[f"trade_count_shock_{h}s"]=(cnt/expected_count) if expected_count>0 else None
        activity[f"quote_volume_shock_{h}s"]=(qv/expected_qv) if expected_qv>0 else None

    r60=r["r60s"]
    reaction={}
    for h in [1,5,10,30]:
        rh=r[f"r{h}s"]
        same=False
        if rh is not None and r60 is not None and r60!=0:
            if r60>0 and rh>=0:
                same=True
            elif r60<0 and rh<=0:
                same=True
        reaction[f"fraction_r{h}s_of_r60"]=(rh/r60) if same else None

    for frac,label in [(0.5,"50"),(0.8,"80")]:
        latency=None
        if r60 is not None and r60!=0:
            target=p0*(1+frac*r60)
            for tr in post:
                if r60>0 and tr[3]>=target:
                    latency=(tr[0]-t0)/1000.0
                    break
                if r60<0 and tr[3]<=target:
                    latency=(tr[0]-t0)/1000.0
                    break
        reaction[f"time_to_{label}pct_r60_ms"]=latency

    latency={}
    for L in LATENCIES_MS:
        entry=first_trade_at_or_after(post,t0+L*1000,t0+60*1_000_000)
        key=f"{L}ms"
        if entry is None:
            latency[key]={
                "actual_entry_latency_ms":None,
                "gross_capture_to_60s":None,
                "net20":None,
                "net50":None,
                "net100":None,
            }
        else:
            gross=exit60_price/entry[3]-1
            latency[key]={
                "actual_entry_latency_ms":(entry[0]-t0)/1000.0,
                "gross_capture_to_60s":gross,
                "net20":net_return(entry[3],exit60_price,COSTS["net20"]),
                "net50":net_return(entry[3],exit60_price,COSTS["net50"]),
                "net100":net_return(entry[3],exit60_price,COSTS["net100"]),
            }

    out={
        "asset":asset,
        "market":market,
        "status":"VALID",
        "t0_ms":t0_ms,
        "p0_trade_latency_ms":(p0trade[0]-t0)/1000.0,
        "first_post_latency_ms":(post[0][0]-t0)/1000.0,
        "pre10s_trade_count":len(pre),
        "post60s_trade_count":len(post),
        "baseline_5s_blocks":n_blocks,
        "baseline_median_trade_count_5s":base_med_count,
        "baseline_median_quote_volume_5s":base_med_qv,
        **r,
        **activity,
        **reaction,
        "latency":latency,
    }
    return out

events=[]
for e in EVENTS:
    try:
        events.append(event_metrics(*e))
    except Exception as ex:
        events.append({"asset":e[0],"market":e[1],"status":"TECHNICAL_FAIL","error_type":type(ex).__name__})

valid=[x for x in events if x.get("status")=="VALID"]

latency_summary={}
actionable_buckets=[]
cost_robust_buckets=[]

for L in LATENCIES_MS:
    k=f"{L}ms"
    gross=[x["latency"][k]["gross_capture_to_60s"] for x in valid if x["latency"][k]["gross_capture_to_60s"] is not None]
    n20=[x["latency"][k]["net20"] for x in valid if x["latency"][k]["net20"] is not None]
    n50=[x["latency"][k]["net50"] for x in valid if x["latency"][k]["net50"] is not None]
    n100=[x["latency"][k]["net100"] for x in valid if x["latency"][k]["net100"] is not None]
    actual=[x["latency"][k]["actual_entry_latency_ms"] for x in valid if x["latency"][k]["actual_entry_latency_ms"] is not None]

    gross_med=median_or_none(gross)
    gross_hit=hit_rate(gross)
    gross_loo=loo_positive(gross) if len(gross)>=2 else False
    gross_conc=positive_concentration(gross) if gross else 1.0

    net50_med=median_or_none(n50)
    net50_hit=hit_rate(n50)
    net50_loo=loo_positive(n50) if len(n50)>=2 else False
    net50_conc=positive_concentration(n50) if n50 else 1.0

    actionable=bool(
        L>=1000
        and len(gross)==8
        and gross_med is not None and gross_med>0
        and gross_hit is not None and gross_hit>=0.60
        and gross_loo
        and gross_conc<=0.35
    )
    cost_robust=bool(
        L>=1000
        and len(n50)==8
        and net50_med is not None and net50_med>0
        and net50_hit is not None and net50_hit>=0.60
        and net50_loo
        and net50_conc<=0.35
    )
    if actionable:
        actionable_buckets.append(L)
    if cost_robust:
        cost_robust_buckets.append(L)

    latency_summary[k]={
        "valid_n":len(gross),
        "median_actual_entry_latency_ms":median_or_none(actual),
        "median_gross_capture_to_60s":gross_med,
        "gross_positive_hit_rate":gross_hit,
        "gross_loo_median_positive":gross_loo,
        "gross_positive_concentration":gross_conc,
        "median_net20":median_or_none(n20),
        "median_net50":net50_med,
        "median_net100":median_or_none(n100),
        "net50_positive_hit_rate":net50_hit,
        "net50_loo_median_positive":net50_loo,
        "net50_positive_concentration":net50_conc,
        "actionable_gross_filter_pass":actionable,
        "cost_robust_50bps":cost_robust,
    }

r60s=[x["r60s"] for x in valid if x.get("r60s") is not None]
median_r60=median_or_none(r60s)
hit_r60=hit_rate(r60s)

horizon_summary={}
for h in HORIZONS_S:
    vals=[x[f"r{h}s"] for x in valid if x.get(f"r{h}s") is not None]
    horizon_summary[f"{h}s"]={
        "valid_n":len(vals),
        "median_return":median_or_none(vals),
        "positive_hit_rate":hit_rate(vals),
    }

reaction_summary={}
for h in [1,5,10,30]:
    vals=[x[f"fraction_r{h}s_of_r60"] for x in valid if x.get(f"fraction_r{h}s_of_r60") is not None]
    reaction_summary[f"fraction_r{h}s_of_r60"]={
        "valid_n":len(vals),
        "median":median_or_none(vals),
    }
for pct in ["50","80"]:
    vals=[x[f"time_to_{pct}pct_r60_ms"] for x in valid if x.get(f"time_to_{pct}pct_r60_ms") is not None]
    reaction_summary[f"time_to_{pct}pct_r60_ms"]={
        "valid_n":len(vals),
        "median":median_or_none(vals),
    }

activity_summary={}
for h in HORIZONS_S:
    for metric in ["trade_count_shock","quote_volume_shock"]:
        key=f"{metric}_{h}s"
        vals=[x[key] for x in valid if x.get(key) is not None]
        activity_summary[key]={"valid_n":len(vals),"median":median_or_none(vals)}

if actionable_buckets:
    label="ACTIONABLE_WINDOW_CANDIDATE"
elif median_r60 is not None and median_r60>0 and hit_r60 is not None and hit_r60>=0.60:
    label="HFT_ONLY_OR_TOO_FAST"
else:
    label="NO_CONSISTENT_FIRST_SECONDS_EFFECT"

summary={
    "parent_freeze":PARENT_FREEZE,
    "identity_resolution":IDENTITY_RESOLUTION,
    "metric_spec":METRIC_SPEC,
    "activation_receipt":ACTIVATION,
    "label_spec":LABEL_SPEC,
    "latency_n_spec":N_SPEC,
    "development_only":True,
    "confirmatory_claim":False,
    "source_sample_n":8,
    "valid_event_n":len(valid),
    "horizon_summary":horizon_summary,
    "reaction_summary":reaction_summary,
    "activity_summary":activity_summary,
    "latency_summary":latency_summary,
    "median_r60":median_r60,
    "r60_positive_hit_rate":hit_r60,
    "actionable_latency_buckets_ms":actionable_buckets,
    "cost_robust_50bps_buckets_ms":cost_robust_buckets,
    "development_label":label,
    "2026_status":"UNOPENED",
}

print("FIRST_SECONDS_V01_2025_DEVELOPMENT_SUMMARY_BEGIN")
print(json.dumps(summary,indent=2,sort_keys=True))
print("FIRST_SECONDS_V01_2025_DEVELOPMENT_SUMMARY_END")
print("FIRST_SECONDS_V01_2025_DEVELOPMENT_EVENTS_BEGIN")
print(json.dumps(events,indent=2,sort_keys=True))
print("FIRST_SECONDS_V01_2025_DEVELOPMENT_EVENTS_END")

# technical trigger after workflow registration; scientific logic unchanged
