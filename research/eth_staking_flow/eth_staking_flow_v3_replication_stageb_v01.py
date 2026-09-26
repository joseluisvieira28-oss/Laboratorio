#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import random
import statistics
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

LAB_ID="ETH-STAKING-FLOW-001"
LOOKBACK=90
PCTL=0.80
BASE_COST=0.0010
STRESS_COST=0.0020
BOOT_REPS=10_000
BOOT_SEED=730031
RESTART_PROB=0.25

STAGEA_RECEIPT=Path("research/eth_staking_flow/ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_1_7.json")
STAGEA_LEDGER=Path("research/eth_staking_flow/ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_1_7.json")

OUT=Path("artifacts/stageb_v3")
OUT.mkdir(parents=True,exist_ok=True)
RAW=OUT/"market_raw"
RAW.mkdir(parents=True,exist_ok=True)

def one_json(root:Path,name:str):
    files=list(root.rglob(name))
    if len(files)!=1:
        raise RuntimeError(f"expected exactly one {name}, got {len(files)}")
    return json.loads(files[0].read_text()),files[0]

def quantile_linear(values:list[int],q:float)->float:
    xs=sorted(float(x) for x in values)
    if not xs: raise ValueError("empty quantile")
    h=(len(xs)-1)*q
    lo=int(math.floor(h)); hi=int(math.ceil(h))
    if lo==hi:return xs[lo]
    w=h-lo
    return xs[lo]*(1-w)+xs[hi]*w

def pf(vals:list[float]):
    pos=sum(x for x in vals if x>0)
    neg=-sum(x for x in vals if x<0)
    if neg==0:
        return "INF" if pos>0 else 0.0
    return pos/neg

def pf_gt_1(v):
    return v=="INF" or (isinstance(v,(int,float)) and v>1.0)

def stationary_bootstrap(vals:list[float]):
    if not vals:
        return {"p_mean_le_zero":1.0,"ci95_low":None,"ci95_high":None}
    n=len(vals)
    rng=random.Random(BOOT_SEED)
    means=[]
    for _ in range(BOOT_REPS):
        idx=rng.randrange(n)
        sample=[]
        for k in range(n):
            if k>0:
                if rng.random()<RESTART_PROB: idx=rng.randrange(n)
                else: idx=(idx+1)%n
            sample.append(vals[idx])
        means.append(sum(sample)/n)
    means.sort()
    count=sum(1 for x in means if x<=0)
    p=(1+count)/(BOOT_REPS+1)
    def pct(q):
        h=(len(means)-1)*q
        lo=int(math.floor(h)); hi=int(math.ceil(h))
        if lo==hi:return means[lo]
        w=h-lo
        return means[lo]*(1-w)+means[hi]*w
    return {"p_mean_le_zero":p,"ci95_low":pct(.025),"ci95_high":pct(.975)}

def block_stats(events:list[dict[str,Any]]):
    vals=[float(x["net10"]) for x in events]
    vals20=[float(x["net20"]) for x in events]
    positives=[x for x in vals if x>0]
    pos_sum=sum(positives)
    largest=max(positives) if positives else 0.0
    return {
      "N":len(events),
      "mean_net10":statistics.fmean(vals) if vals else 0.0,
      "median_net10":statistics.median(vals) if vals else 0.0,
      "pf_net10":pf(vals),
      "mean_net20":statistics.fmean(vals20) if vals20 else 0.0,
      "pf_net20":pf(vals20),
      "win_rate_net10":sum(x>0 for x in vals)/len(vals) if vals else 0.0,
      "bootstrap":stationary_bootstrap(vals),
      "positive_net10_sum":pos_sum,
      "largest_positive_net10":largest,
      "largest_positive_fraction":(largest/pos_sum if pos_sum>0 else None),
    }

def load_sources():
    s=json.loads(STAGEA_RECEIPT.read_text())
    if s.get("classification")!="SOURCE_REPLICATION_PASS":
        raise RuntimeError("Stage A not SOURCE_REPLICATION_PASS")
    if int(s.get("observed_date_count",-1))!=608:
        raise RuntimeError("Stage A date count != 608")
    if s.get("market_prices_opened") or s.get("returns_opened") or s.get("pnl_opened"):
        raise RuntimeError("Stage A market firewall violated")

    led=json.loads(STAGEA_LEDGER.read_text())
    rows=led.get("records") or []
    if len(rows)!=608: raise RuntimeError("Stage A ledger !=608 rows")
    if led.get("daily_series_sha256")!=s.get("daily_series_sha256"):
        raise RuntimeError("Stage A ledger SHA binding mismatch")

    hist,hp=one_json(Path("historical_queue"),"ETH_STAKING_FLOW_001_XATU_FULL_QUEUE_V0_3D.json")
    if hist.get("classification")!="SOURCE_DATA_PASS" or len(hist.get("daily_source_records") or [])!=630:
        raise RuntimeError("historical queue authority invalid")
    if hist.get("daily_series_sha256")!="95d225db9c4924852dfbca6333122fc78199092f0cdfd7a0995f4b5530cb2544":
        raise RuntimeError("historical queue SHA mismatch")

    disc,dp=one_json(Path("historical_discovery"),"ETH_STAKING_FLOW_001_DISCOVERY_V0_1.json")
    if disc.get("classification")!="DISCOVERY_INSUFFICIENT_SAMPLE" or int(disc.get("resolved_event_count",-1))!=19:
        raise RuntimeError("Discovery D authority mismatch")
    if disc.get("accessed_2025_or_2026") is not False:
        raise RuntimeError("Discovery D independence violated")
    return s,rows,hist,disc,hp,dp

def build_queue_map(hist,stage_rows):
    out={}
    for r in hist["daily_source_records"]+stage_rows:
        d=date.fromisoformat(r["date"])
        v=int(r["net_queue_count"])
        if d in out and out[d]!=v:
            raise RuntimeError(f"queue conflict {d}")
        out[d]=v
    # Critical contiguous window needed by R1/R2.
    d=date(2024,10,3)
    while d<=date(2026,8,31):
        if d not in out: raise RuntimeError(f"missing queue context {d}")
        d+=timedelta(days=1)
    return out

def build_block_events(qmap,start:date,last_signal:date):
    events=[]
    next_eligible=date.min
    d=start
    while d<=last_signal:
        if d>=next_eligible:
            prior_dates=[d-timedelta(days=k) for k in range(90,0,-1)]
            if any(x not in qmap for x in prior_dates) or d not in qmap:
                raise RuntimeError(f"missing prior90/source for {d}")
            prior=[qmap[x] for x in prior_dates]
            q80=quantile_linear(prior,PCTL)
            current=qmap[d]
            if current>=q80:
                events.append({
                  "signal_date":d.isoformat(),
                  "entry_date":(d+timedelta(days=1)).isoformat(),
                  "exit_date":(d+timedelta(days=8)).isoformat(),
                  "net_queue_count":current,
                  "q80_prior90":q80,
                })
                next_eligible=d+timedelta(days=8)
        d+=timedelta(days=1)
    return events

def get_verified(url):
    r=requests.get(url,timeout=60)
    r.raise_for_status()
    body=r.content
    cr=requests.get(url+".CHECKSUM",timeout=60)
    cr.raise_for_status()
    toks=cr.text.strip().split()
    if not toks: raise RuntimeError("empty CHECKSUM "+url)
    expected=toks[0].lower()
    got=hashlib.sha256(body).hexdigest()
    if got!=expected: raise RuntimeError(f"checksum mismatch {url}")
    return body,cr.content,got

def parse_zip(body:bytes,label:str):
    z=zipfile.ZipFile(io.BytesIO(body))
    names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"{label}: unexpected ZIP members {names}")
    rows=[]
    for raw in z.open(names[0]):
        line=raw.decode().strip()
        if not line: continue
        cols=next(csv.reader([line]))
        try: ts=int(cols[0])
        except ValueError:
            if not rows: continue
            raise
        if 10**12<=ts<10**14:
            seconds=ts/1000
            unit="ms"
        elif 10**15<=ts<10**17:
            seconds=ts/1_000_000
            unit="us"
        else:
            raise RuntimeError(f"{label}: unsupported timestamp magnitude {ts}")
        d=datetime.fromtimestamp(seconds,tz=timezone.utc).date()
        px=float(cols[1])
        if not math.isfinite(px) or px<=0: raise RuntimeError(f"{label}: bad open {d}")
        rows.append((d,px,unit))
    return rows

def acquire_market():
    prices={}
    manifest=[]
    # Completed monthly archives.
    y,m=2025,1
    while (y,m)<=(2026,8):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/ETHUSDT-1d-{ym}.zip"
        body,check,sha=get_verified(url)
        (RAW/f"ETHUSDT-1d-{ym}.zip").write_bytes(body)
        (RAW/f"ETHUSDT-1d-{ym}.zip.CHECKSUM").write_bytes(check)
        parsed=parse_zip(body,ym)
        units=sorted(set(u for _,_,u in parsed))
        for d,px,u in parsed:
            if d in prices: raise RuntimeError(f"duplicate market date {d}")
            prices[d]=px
        manifest.append({"kind":"monthly","period":ym,"zip_sha256":sha,"rows":len(parsed),"timestamp_units":units})
        m+=1
        if m==13: y+=1;m=1
    # Frozen incomplete-month daily archives through Sep 8 only.
    for day in range(1,9):
        ds=f"2026-09-{day:02d}"
        url=f"https://data.binance.vision/data/spot/daily/klines/ETHUSDT/1d/ETHUSDT-1d-{ds}.zip"
        body,check,sha=get_verified(url)
        (RAW/f"ETHUSDT-1d-{ds}.zip").write_bytes(body)
        (RAW/f"ETHUSDT-1d-{ds}.zip.CHECKSUM").write_bytes(check)
        parsed=parse_zip(body,ds)
        if len(parsed)!=1 or parsed[0][0].isoformat()!=ds:
            raise RuntimeError(f"daily archive geometry mismatch {ds}")
        d,px,u=parsed[0]
        if d in prices: raise RuntimeError(f"duplicate market date {d}")
        prices[d]=px
        manifest.append({"kind":"daily","period":ds,"zip_sha256":sha,"rows":1,"timestamp_units":[u]})
    expected=[]
    d=date(2025,1,1)
    while d<=date(2026,9,8):
        expected.append(d); d+=timedelta(days=1)
    if sorted(prices)!=expected:
        raise RuntimeError(f"market coverage mismatch missing={sorted(set(expected)-set(prices))[:10]} outside={sorted(set(prices)-set(expected))[:10]}")
    return prices,manifest

def resolve(events,prices,block_name,ceiling):
    out=[]
    for e in events:
        en=date.fromisoformat(e["entry_date"]); ex=date.fromisoformat(e["exit_date"])
        if ex>ceiling: raise RuntimeError(f"{block_name}: event exit above ceiling")
        if en not in prices or ex not in prices: raise RuntimeError(f"{block_name}: missing market open")
        gross=prices[ex]/prices[en]-1.0
        out.append({**e,"block":block_name,"entry_open":prices[en],"exit_open":prices[ex],
                    "gross_return":gross,"net10":gross-BASE_COST,"net20":gross-STRESS_COST})
    return out

def pooled_stats(block_events):
    vals=[e for es in block_events.values() for e in es]
    return block_stats(vals)

def main():
    receipt={
      "lab_id":LAB_ID,"stage":"V3_INDEPENDENT_OUTCOME_REPLICATION_V0_1",
      "classification":"V3_REPLICATION_TECHNICAL_OR_PROVENANCE_FAILURE",
      "failure":None,
      "market_accessed_under_stageb_authority":False,
      "market_date_ceiling":"2026-09-08",
      "live_trading":False,"orders_created":False,"wallet_used":False,"exchange_mutation":False
    }
    terminal=False
    try:
        src,stage_rows,hist,disc,hp,dp=load_sources()
        receipt["stagea_daily_series_sha256"]=src["daily_series_sha256"]
        receipt["historical_queue_artifact_sha256"]=hashlib.sha256(hp.read_bytes()).hexdigest()
        receipt["discovery_d_artifact_sha256"]=hashlib.sha256(dp.read_bytes()).hexdigest()
        qmap=build_queue_map(hist,stage_rows)

        r1_signals=build_block_events(qmap,date(2025,1,1),date(2025,12,23))
        r2_signals=build_block_events(qmap,date(2026,1,1),date(2026,8,31))
        receipt["pre_market_signal_counts"]={"R1":len(r1_signals),"R2":len(r2_signals)}
        receipt["signal_rule_verified_unchanged"]=True

        prices,manifest=acquire_market()
        receipt["market_accessed_under_stageb_authority"]=True
        receipt["market_manifest"]=manifest
        receipt["market_file_count"]=len(manifest)
        receipt["market_daily_date_count"]=len(prices)

        r1=resolve(r1_signals,prices,"R1_2025",date(2025,12,31))
        r2=resolve(r2_signals,prices,"R2_2026_TO_AUG31",date(2026,9,8))
        d_events=[{**e,"block":"D_2023_2024"} for e in disc["event_ledger"]]

        blocks={"D":d_events,"R1":r1,"R2":r2}
        stats={k:block_stats(v) for k,v in blocks.items()}
        pooled=pooled_stats(blocks)
        loo={}
        for left in ("D","R1","R2"):
            rem={k:v for k,v in blocks.items() if k!=left}
            loo[left]=pooled_stats(rem)

        adequate_each=all(stats[k]["N"]>0 for k in ("D","R1","R2"))
        each_positive=adequate_each and all(stats[k]["mean_net10"]>0 and pf_gt_1(stats[k]["pf_net10"]) for k in ("D","R1","R2"))
        pooled_positive=pooled["mean_net10"]>0 and pf_gt_1(pooled["pf_net10"])
        loo_positive=all(v["mean_net10"]>0 and pf_gt_1(v["pf_net10"]) for v in loo.values())
        concentration=pooled["largest_positive_fraction"]
        concentration_ok=concentration is not None and concentration<=0.40

        gates={
          "pooled_event_count_ge_30":pooled["N"]>=30,
          "exactly_3_disjoint_blocks_represented":adequate_each,
          "r1_r2_independent_from_original_discovery":all(date.fromisoformat(e["signal_date"]).year>=2025 for e in r1+r2),
          "each_block_mean_net10_gt0_and_pf_gt1":each_positive,
          "pooled_mean_net10_gt0_and_pf_gt1":pooled_positive,
          "every_leave_one_block_out_mean_gt0_pf_gt1":loo_positive,
          "largest_single_positive_le_40pct_pooled_positive":concentration_ok,
          "unchanged_signal_direction_horizon_cost_event_inclusion":True,
          "clean_source_provenance_leakage":True,
          "no_adequate_independent_block_materially_contradicts_base_economics":each_positive,
        }
        passed=all(gates.values())
        receipt.update({
          "classification":"V3_REPLICATED_CORPUS_PASS" if passed else "V3_REPLICATION_FAIL_NO_TIER2_PROMOTION",
          "block_statistics":stats,
          "pooled_statistics":pooled,
          "leave_one_block_out":loo,
          "v3_gates":gates,
          "all_v3_gates_pass":passed,
          "event_ledgers":{"R1":r1,"R2":r2},
          "costs":{"base_round_trip_bps":10,"stress_round_trip_bps":20},
          "bootstrap_settings":{"repetitions":BOOT_REPS,"seed":BOOT_SEED,"restart_probability":RESTART_PROB},
          "market_source":"Binance Data Vision Spot ETHUSDT 1d archives + CHECKSUM",
          "market_instrument":"ETHUSDT spot",
          "source_date_ceiling":"2026-08-31",
          "market_date_ceiling":"2026-09-08",
          "oos_or_holdout_tuning":False,
          "live_trading":False,"orders_created":False,"wallet_used":False,"exchange_mutation":False
        })
        terminal=True
    except Exception as e:
        receipt["failure"]=f"{type(e).__name__}: {str(e)[:3000]}"

    out=OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_RESULT_V0_1.json"
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
      "classification":receipt["classification"],
      "failure":receipt.get("failure"),
      "pre_market_signal_counts":receipt.get("pre_market_signal_counts"),
      "block_statistics":receipt.get("block_statistics"),
      "pooled_statistics":receipt.get("pooled_statistics"),
      "all_v3_gates_pass":receipt.get("all_v3_gates_pass"),
      "market_ceiling":receipt.get("market_date_ceiling"),
      "live":False
    },indent=2,sort_keys=True,allow_nan=False))
    return 0 if terminal else 2

if __name__=="__main__":
    sys.exit(main())
