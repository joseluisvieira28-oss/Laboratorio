#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, io, json, math, time, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random
from statistics import mean, median
from typing import Any

LAB="ETH-BLOCKSPACE-DEMAND-001"
CANDIDATE="EBD-BURN80-UTIL50-LONG-H24-001"
SOURCE_DAILY_SHA="1fffaf5dde2a1cff10356333536a6660a22f35e56210f376081738ea394bc928"
DISC_SIGNAL_SHA="b655923a78696538decbeb261734c003d868704c7ac3e7dd3017d5c8734100db"
HOLDOUT_SIGNAL_SHA="241807d84dca3826dfba5d77d3f0b51f63ce88d3a8c34a1f2d7352b2af277191"
MONTHS=tuple([f"2022-{m:02d}" for m in range(1,13)]+[f"2023-{m:02d}" for m in range(1,13)])
BASE_URL="https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d"
DAY_MS=86_400_000
BASE_COST=20.0
STRESS_COST=30.0
BOOT_REPS=10_000
BOOT_SEED=20260919

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def get(url:str,retries:int=5)->bytes:
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":f"{LAB}/discovery-v0.1"})
            with urllib.request.urlopen(req,timeout=60) as r:
                if r.status!=200: raise RuntimeError(f"HTTP_{r.status}")
                return r.read()
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(min(1.0*(2**i),8.0))
    raise RuntimeError(f"download failed {url}: {last}")

def qlinear(vals:list[float],p:float)->float:
    x=sorted(vals)
    if not x: raise ValueError("empty percentile input")
    pos=(len(x)-1)*p
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return x[lo]
    f=pos-lo
    return x[lo]*(1-f)+x[hi]*f

def pf(vals:list[float])->float|None:
    pos=sum(x for x in vals if x>0)
    neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else None

def max_drawdown(vals:list[float])->float|None:
    if not vals:return None
    eq=0.0; peak=0.0; dd=0.0
    for x in vals:
        eq+=x
        peak=max(peak,eq)
        dd=min(dd,eq-peak)
    return dd

def metrics(events:list[dict[str,Any]],key:str="base_net_bps")->dict[str,Any]:
    vals=[float(e[key]) for e in events]
    pos=[x for x in vals if x>0]
    return {
        "n":len(vals),
        "mean":mean(vals) if vals else None,
        "median":median(vals) if vals else None,
        "pf":pf(vals),
        "positive_fraction":sum(x>0 for x in vals)/len(vals) if vals else None,
        "cumulative_bps":sum(vals),
        "max_additive_drawdown_bps":max_drawdown(vals),
        "largest_single_positive_event_share":(max(pos)/sum(pos) if pos and sum(pos)>0 else None),
    }

def load_source(source_dir:Path):
    p=source_dir/"ETH_BLOCKSPACE_DEMAND_001_DAILY_SOURCE_SERIES_V0_2C.csv"
    if not p.is_file(): raise RuntimeError(f"missing canonical source daily file: {p}")
    if sha256_file(p)!=SOURCE_DAILY_SHA: raise RuntimeError("canonical source daily SHA mismatch")
    rows=[]
    with p.open("r",encoding="utf-8",newline="") as f:
        r=csv.DictReader(f)
        need={"date","mean_gas_utilization","mean_sample_block_base_fee_burn_eth"}
        if not need.issubset(set(r.fieldnames or [])): raise RuntimeError("source daily schema mismatch")
        for x in r:
            rows.append({
                "date":x["date"],
                "util":float(x["mean_gas_utilization"]),
                "burn":float(x["mean_sample_block_base_fee_burn_eth"]),
            })
    if len(rows)!=1235 or rows[0]["date"]!="2021-08-11" or rows[-1]["date"]!="2024-12-27":
        raise RuntimeError("canonical source daily identity mismatch")
    return rows

def build_signals(rows):
    disc=[]; hold=[]
    for i,x in enumerate(rows):
        if i<90: continue
        prior=rows[i-90:i]
        burn80=qlinear([z["burn"] for z in prior],0.80)
        util50=median([z["util"] for z in prior])
        is_signal=x["burn"]>=burn80 and x["util"]>=util50
        if not is_signal: continue
        rec={"signal_date":x["date"],"burn":x["burn"],"util":x["util"],"prior90_burn_p80":burn80,"prior90_util_median":util50}
        if "2022-01-01"<=x["date"]<="2023-12-29": disc.append(rec)
        elif "2024-01-01"<=x["date"]<="2024-12-27": hold.append(rec)
    disc_text="".join(x["signal_date"]+"\n" for x in disc).encode()
    hold_text="".join(x["signal_date"]+"\n" for x in hold).encode()
    if len(disc)!=112 or sha256_bytes(disc_text)!=DISC_SIGNAL_SHA:
        raise RuntimeError("Discovery source signal census mismatch")
    if len(hold)!=43 or sha256_bytes(hold_text)!=HOLDOUT_SIGNAL_SHA:
        raise RuntimeError("2024 source-only holdout signal census mismatch")
    return disc,hold

def parse_checksum(b:bytes)->str:
    parts=b.decode("utf-8").strip().replace("*"," ").split()
    if not parts or len(parts[0])!=64: raise RuntimeError("invalid Binance checksum payload")
    return parts[0].lower()

def load_market():
    market={}
    archives=[]
    for ym in MONTHS:
        name=f"ETHUSDT-1d-{ym}.zip"
        url=f"{BASE_URL}/{name}"
        z=get(url)
        expected=parse_checksum(get(url+".CHECKSUM"))
        actual=sha256_bytes(z)
        if actual!=expected: raise RuntimeError(f"Binance checksum mismatch {ym}")
        with zipfile.ZipFile(io.BytesIO(z)) as zf:
            members=[n for n in zf.namelist() if not n.endswith("/")]
            if len(members)!=1: raise RuntimeError(f"unexpected zip members {ym}")
            with zf.open(members[0]) as raw:
                rr=csv.reader(io.TextIOWrapper(raw,encoding="utf-8-sig"))
                month_rows=0
                for row in rr:
                    if not row: continue
                    try: ot=int(row[0])
                    except Exception:
                        if str(row[0]).strip().lower() in {"open_time","open time"}: continue
                        raise
                    if len(row)<7: raise RuntimeError(f"short Binance row {ym}")
                    if ot>=10**15: raise RuntimeError("unexpected microsecond timestamp in pre-2024 market corpus")
                    ct=int(row[6])
                    if ot%DAY_MS!=0 or ct!=ot+DAY_MS-1:
                        raise RuntimeError(f"daily timestamp alignment mismatch {ym} {ot} {ct}")
                    dt=datetime.fromtimestamp(ot/1000,tz=timezone.utc)
                    if dt.year not in (2022,2023):
                        raise RuntimeError(f"protected/unexpected market year {dt.year}")
                    ds=dt.date().isoformat()
                    if ds in market: raise RuntimeError(f"duplicate market date {ds}")
                    op=float(row[1])
                    if op<=0: raise RuntimeError(f"invalid ETH open {ds}")
                    market[ds]=op
                    month_rows+=1
        archives.append({"month":ym,"zip_sha256":actual,"rows":month_rows})
    dates=sorted(market)
    if len(dates)!=730 or dates[0]!="2022-01-01" or dates[-1]!="2023-12-31":
        raise RuntimeError(f"market corpus identity mismatch rows={len(dates)} first={dates[:1]} last={dates[-1:]}")
    d0=datetime(2022,1,1,tzinfo=timezone.utc).date()
    for i in range(730):
        ds=(d0+timedelta(days=i)).isoformat()
        if ds not in market: raise RuntimeError(f"missing ETH daily market date {ds}")
    return market,archives

def bootstrap(events):
    groups=defaultdict(list)
    for e in events:
        dt=datetime.fromisoformat(e["entry_date"]).date()
        iso=dt.isocalendar()
        groups[(iso.year,iso.week)].append(float(e["base_net_bps"]))
    keys=sorted(groups)
    sums={k:sum(groups[k]) for k in keys}; ns={k:len(groups[k]) for k in keys}
    rng=Random(BOOT_SEED); draws=[]
    for _ in range(BOOT_REPS):
        s=0.0;n=0
        for __ in range(len(keys)):
            k=keys[rng.randrange(len(keys))]
            s+=sums[k]; n+=ns[k]
        draws.append(s/n)
    draws.sort()
    def pct(p):
        pos=(len(draws)-1)*p
        lo=int(math.floor(pos)); hi=int(math.ceil(pos))
        if lo==hi:return draws[lo]
        f=pos-lo
        return draws[lo]*(1-f)+draws[hi]*f
    return {
        "event_bearing_weeks":len(keys),
        "repetitions":BOOT_REPS,
        "seed":BOOT_SEED,
        "lower95":pct(0.025),
        "upper95":pct(0.975),
        "p_one_sided":(sum(x<=0 for x in draws)+1)/(BOOT_REPS+1),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dir",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()

    source=load_source(a.source_dir)
    signals,holdout_source_only=build_signals(source)

    # This is the first market-outcome access in this experiment.
    market,archives=load_market()

    events=[]
    for s in signals:
        t=datetime.fromisoformat(s["signal_date"]).date()
        entry=(t+timedelta(days=1)).isoformat()
        exitd=(t+timedelta(days=2)).isoformat()
        if entry not in market or exitd not in market:
            raise RuntimeError(f"unresolved frozen event {s['signal_date']}")
        en=market[entry]; ex=market[exitd]
        gross=(ex/en-1.0)*10_000.0
        events.append({
            **s,
            "entry_date":entry,
            "exit_date":exitd,
            "entry_open":en,
            "exit_open":ex,
            "gross_bps":gross,
            "base_net_bps":gross-BASE_COST,
            "stress_net_bps":gross-STRESS_COST,
        })
    events.sort(key=lambda x:(x["entry_date"],x["signal_date"]))
    if len(events)!=112: raise RuntimeError(f"resolved event count mismatch {len(events)}")

    base=metrics(events)
    stress=metrics(events,"stress_net_bps")
    years={}
    for y in ("2022","2023"):
        xs=[e for e in events if e["signal_date"].startswith(y+"-")]
        years[y]={"base":metrics(xs),"stress":metrics(xs,"stress_net_bps")}
    boot=bootstrap(events)
    gates={
        "n_ge_100":base["n"]>=100,
        "base_mean_positive":base["mean"] is not None and base["mean"]>0,
        "base_pf_gt_1":base["pf"] is not None and base["pf"]>1,
        "stress_mean_positive":stress["mean"] is not None and stress["mean"]>0,
        "bootstrap_lower95_positive":boot["lower95"]>0,
        "bootstrap_p_le_0_05":boot["p_one_sided"]<=0.05,
        "2022_base_mean_positive":years["2022"]["base"]["mean"] is not None and years["2022"]["base"]["mean"]>0,
        "2023_base_mean_positive":years["2023"]["base"]["mean"] is not None and years["2023"]["base"]["mean"]>0,
        "largest_positive_event_share_le_0_20":base["largest_single_positive_event_share"] is not None and base["largest_single_positive_event_share"]<=0.20,
    }
    if base["n"]<100:
        classification="INSUFFICIENT_SAMPLE"
    elif all(gates.values()):
        classification="DISCOVERY_SURVIVES"
    else:
        classification="DISCOVERY_NO_EDGE"

    result={
        "lab_id":LAB,
        "candidate_id":CANDIDATE,
        "status":"DISCOVERY_COMPLETE",
        "classification":classification,
        "source_binding":{
            "run_id":35446488521,
            "artifact_id":10585049563,
            "artifact_digest":"sha256:6bd5b8970a07fa022d91710b956a0ed80468fee3417c16d02746be6eb1e71114",
            "daily_series_sha256":SOURCE_DAILY_SHA,
            "discovery_signal_count":len(signals),
            "discovery_signal_dates_sha256":DISC_SIGNAL_SHA,
            "holdout_2024_source_only_signal_count":len(holdout_source_only),
            "holdout_2024_source_only_signal_dates_sha256":HOLDOUT_SIGNAL_SHA,
        },
        "market_source":{
            "provider":"Binance Data Vision",
            "market":"Spot",
            "symbol":"ETHUSDT",
            "interval":"1d",
            "months":list(MONTHS),
            "archive_count":len(archives),
            "archive_checksums_verified":len(archives),
            "daily_rows":len(market),
            "archives":archives,
            "market_2024_accessed":False,
            "market_2025_accessed":False,
            "market_2026_accessed":False,
        },
        "costs":{"base_round_trip_bps":BASE_COST,"stress_round_trip_bps":STRESS_COST},
        "base":base,
        "stress":stress,
        "by_signal_year":years,
        "bootstrap":boot,
        "gates":gates,
        "governance":{
            "2024_market_outcomes_locked":True,
            "2025_market_outcomes_locked":True,
            "2026_market_outcomes_locked":True,
            "post_outcome_tuning":False,
            "live_trading":False,
            "orders":False,
            "wallets":False,
            "exchange_mutation":False,
            "alerts_webhooks":False,
            "render_deploy":False,
            "merge_main":False,
        },
    }
    a.output_dir.mkdir(parents=True,exist_ok=True)
    rp=a.output_dir/"ETH_BLOCKSPACE_DEMAND_001_DISCOVERY_RESULT_V0_1.json"
    rp.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    lp=a.output_dir/"ETH_BLOCKSPACE_DEMAND_001_DISCOVERY_EVENT_LEDGER_V0_1.csv"
    fields=list(events[0].keys())
    with lp.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(events)
    print(json.dumps({
        "classification":classification,
        "n":base["n"],
        "base_mean_bps":base["mean"],
        "base_pf":base["pf"],
        "stress_mean_bps":stress["mean"],
        "stress_pf":stress["pf"],
        "bootstrap_lower95":boot["lower95"],
        "bootstrap_upper95":boot["upper95"],
        "bootstrap_p_one_sided":boot["p_one_sided"],
        "year_2022_mean":years["2022"]["base"]["mean"],
        "year_2023_mean":years["2023"]["base"]["mean"],
        "largest_positive_event_share":base["largest_single_positive_event_share"],
        "gates":gates,
        "market_2024_accessed":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
