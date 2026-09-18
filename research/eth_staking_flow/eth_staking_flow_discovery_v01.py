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
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

LAB_ID="ETH-STAKING-FLOW-001"
MVE_ID="ESF-NETQUEUE-XATU-7D-003"
QUEUE_RUN_ID=35384444641
QUEUE_SERIES_SHA="95d225db9c4924852dfbca6333122fc78199092f0cdfd7a0995f4b5530cb2544"
EXPECTED_QUEUE_DATES=630
LOOKBACK=90
PCTL=0.80
LAST_SIGNAL=date(2024,12,23)
MARKET_START=date(2023,7,1)
MARKET_END=date(2024,12,31)
BASE_COST=0.0010
STRESS_COST=0.0020
BOOT_REPS=10_000
BOOT_SEED=730031
RESTART_PROB=0.25

def load_queue_receipt()->tuple[dict[str,Any],Path]:
    files=list(Path("downloaded_queue_source").rglob("*.json"))
    if len(files)!=1:
        raise RuntimeError(f"expected exactly one queue receipt, got {len(files)}")
    p=files[0]
    obj=json.loads(p.read_text(encoding="utf-8"))
    if obj.get("lab_id")!=LAB_ID or obj.get("mve_id")!=MVE_ID:
        raise RuntimeError("queue receipt identity mismatch")
    if obj.get("classification")!="SOURCE_DATA_PASS":
        raise RuntimeError(f"queue source not PASS: {obj.get('classification')}")
    if int(obj.get("observed_date_count",-1))!=EXPECTED_QUEUE_DATES:
        raise RuntimeError("queue observed date count mismatch")
    if obj.get("daily_series_sha256")!=QUEUE_SERIES_SHA:
        raise RuntimeError("queue series SHA mismatch")
    if obj.get("market_prices_opened") or obj.get("returns_opened") or obj.get("pnl_opened") or obj.get("accessed_2025_or_2026"):
        raise RuntimeError("upstream source safety receipt violated")
    rows=obj.get("daily_source_records") or []
    if len(rows)!=EXPECTED_QUEUE_DATES:
        raise RuntimeError("queue daily source record count mismatch")
    return obj,p

def quantile_linear(values:list[int],q:float)->float:
    xs=sorted(float(x) for x in values)
    if not xs:
        raise ValueError("empty quantile")
    h=(len(xs)-1)*q
    lo=int(math.floor(h)); hi=int(math.ceil(h))
    if lo==hi:
        return xs[lo]
    w=h-lo
    return xs[lo]*(1.0-w)+xs[hi]*w

def build_events(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    ordered=sorted(rows,key=lambda r:r["date"])
    dates=[date.fromisoformat(r["date"]) for r in ordered]
    expected=[]
    d=date(2023,4,12)
    while d<=date(2024,12,31):
        expected.append(d); d+=timedelta(days=1)
    if dates!=expected:
        raise RuntimeError("queue date sequence is not exact 630-day daily calendar")
    events=[]
    next_eligible=date.min
    for i in range(LOOKBACK,len(ordered)):
        t=dates[i]
        if t>LAST_SIGNAL:
            break
        if t<next_eligible:
            continue
        prior=[int(ordered[j]["net_queue_count"]) for j in range(i-LOOKBACK,i)]
        q80=quantile_linear(prior,PCTL)
        current=int(ordered[i]["net_queue_count"])
        if current>=q80:
            events.append({
                "signal_date":t.isoformat(),
                "entry_date":(t+timedelta(days=1)).isoformat(),
                "exit_date":(t+timedelta(days=8)).isoformat(),
                "net_queue_count":current,
                "q80_prior90":q80,
            })
            next_eligible=t+timedelta(days=8)
    return events

def month_iter(start:date,end:date):
    y,m=start.year,start.month
    while (y,m)<=(end.year,end.month):
        yield y,m
        m+=1
        if m==13:
            y+=1;m=1

def guarded_get(url:str,timeout:int=60)->bytes:
    if "2025" in url or "2026" in url:
        raise RuntimeError("PROTECTED_PERIOD_URL_REJECTED")
    r=requests.get(url,timeout=timeout)
    r.raise_for_status()
    return r.content

def acquire_market_prices(outdir:Path)->tuple[dict[date,float],list[dict[str,Any]]]:
    rawdir=outdir/"market_raw"
    rawdir.mkdir(parents=True,exist_ok=True)
    prices={}
    manifest=[]
    for y,m in month_iter(MARKET_START,MARKET_END):
        ym=f"{y:04d}-{m:02d}"
        base=f"https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/ETHUSDT-1d-{ym}.zip"
        zip_bytes=guarded_get(base)
        checksum_bytes=guarded_get(base+".CHECKSUM")
        sidecar=checksum_bytes.decode("utf-8").strip().split()
        if not sidecar:
            raise RuntimeError(f"empty CHECKSUM {ym}")
        provider_sha=sidecar[0].lower()
        got_sha=hashlib.sha256(zip_bytes).hexdigest()
        if got_sha!=provider_sha:
            raise RuntimeError(f"checksum mismatch {ym}: {got_sha} != {provider_sha}")
        (rawdir/f"ETHUSDT-1d-{ym}.zip").write_bytes(zip_bytes)
        (rawdir/f"ETHUSDT-1d-{ym}.zip.CHECKSUM").write_bytes(checksum_bytes)
        z=zipfile.ZipFile(io.BytesIO(zip_bytes))
        names=z.namelist()
        if len(names)!=1:
            raise RuntimeError(f"unexpected ZIP members {ym}: {names}")
        row_count=0
        for raw in z.open(names[0]):
            line=raw.decode("utf-8").strip()
            if not line:
                continue
            cols=next(csv.reader([line]))
            try:
                ts=int(cols[0])
            except ValueError:
                if row_count==0:
                    continue
                raise
            if not (1_000_000_000_000 <= ts < 10_000_000_000_000):
                raise RuntimeError(f"unexpected pre-2025 timestamp unit {ym}: {ts}")
            d=datetime.fromtimestamp(ts/1000,tz=timezone.utc).date()
            open_px=float(cols[1])
            if not math.isfinite(open_px) or open_px<=0:
                raise RuntimeError(f"invalid open price {d}")
            if d in prices:
                raise RuntimeError(f"duplicate ETHUSDT daily date {d}")
            prices[d]=open_px
            row_count+=1
        manifest.append({"month":ym,"zip_sha256":got_sha,"provider_sha256":provider_sha,"rows":row_count})
    expected=[]
    d=MARKET_START
    while d<=MARKET_END:
        expected.append(d); d+=timedelta(days=1)
    if sorted(prices)!=expected:
        missing=sorted(set(expected)-set(prices))
        outside=sorted(set(prices)-set(expected))
        raise RuntimeError(f"market daily coverage mismatch missing={missing[:5]} outside={outside[:5]}")
    return prices,manifest

def pf(vals:list[float])->float:
    pos=sum(x for x in vals if x>0)
    neg=-sum(x for x in vals if x<0)
    if neg==0:
        return math.inf if pos>0 else 0.0
    return pos/neg

def stationary_bootstrap(vals:list[float])->dict[str,float]:
    n=len(vals)
    rng=random.Random(BOOT_SEED)
    means=[]
    for _ in range(BOOT_REPS):
        idx=rng.randrange(n)
        sample=[]
        for k in range(n):
            if k>0:
                if rng.random()<RESTART_PROB:
                    idx=rng.randrange(n)
                else:
                    idx=(idx+1)%n
            sample.append(vals[idx])
        means.append(sum(sample)/n)
    means.sort()
    count=sum(1 for x in means if x<=0)
    p=(1+count)/(BOOT_REPS+1)
    def pct(q:float):
        h=(len(means)-1)*q
        lo=int(math.floor(h)); hi=int(math.ceil(h))
        if lo==hi:return means[lo]
        w=h-lo
        return means[lo]*(1-w)+means[hi]*w
    return {"p_mean_le_zero":p,"ci95_low":pct(0.025),"ci95_high":pct(0.975)}

def main()->int:
    out=Path("eth_staking_flow_discovery_output")
    out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_DISCOVERY_V0_1.json"
    receipt={
        "lab_id":LAB_ID,
        "mve_id":MVE_ID,
        "phase":"ONE_SHOT_DISCOVERY_V0_1",
        "classification":None,
        "failure":None,
        "protected_2025_2026_opened":False,
        "live_trading":False,
        "exchange_mutation":False,
    }
    valid_terminal=False
    try:
        qsrc,qpath=load_queue_receipt()
        receipt["queue_source_receipt_sha256"]=hashlib.sha256(qpath.read_bytes()).hexdigest()
        receipt["queue_daily_series_sha256"]=qsrc["daily_series_sha256"]
        events=build_events(qsrc["daily_source_records"])
        receipt["pre_market_signal_event_count"]=len(events)
        receipt["signal_rule"]={
            "lookback_prior_observations":LOOKBACK,
            "percentile":PCTL,
            "percentile_method":"linear",
            "current_t_excluded_from_threshold_window":True,
            "nonoverlap_next_eligible_signal_days":8,
            "last_signal_date":LAST_SIGNAL.isoformat()
        }

        prices,market_manifest=acquire_market_prices(out)
        receipt["market_manifest"]=market_manifest
        receipt["market_month_count"]=len(market_manifest)
        receipt["market_daily_date_count"]=len(prices)

        resolved=[]
        for e in events:
            entry=date.fromisoformat(e["entry_date"])
            exitd=date.fromisoformat(e["exit_date"])
            if entry>MARKET_END or exitd>MARKET_END:
                raise RuntimeError("event crossed protected market boundary despite frozen cutoff")
            if entry not in prices or exitd not in prices:
                raise RuntimeError(f"missing market open for event {e['signal_date']}")
            gross=prices[exitd]/prices[entry]-1.0
            net10=gross-BASE_COST
            net20=gross-STRESS_COST
            resolved.append({
                **e,
                "entry_open":prices[entry],
                "exit_open":prices[exitd],
                "gross_return":gross,
                "net10":net10,
                "net20":net20
            })

        net10s=[x["net10"] for x in resolved]
        net20s=[x["net20"] for x in resolved]
        n=len(resolved)
        receipt["resolved_event_count"]=n
        receipt["event_ledger"]=resolved

        if n==0:
            mean10=median10=mean20=0.0
            pf10=pf20=0.0
            win=0.0
            boot={"p_mean_le_zero":1.0,"ci95_low":0.0,"ci95_high":0.0}
        else:
            mean10=statistics.fmean(net10s)
            median10=statistics.median(net10s)
            mean20=statistics.fmean(net20s)
            pf10=pf(net10s); pf20=pf(net20s)
            win=sum(x>0 for x in net10s)/n
            boot=stationary_bootstrap(net10s)

        years={}
        for y in (2023,2024):
            vals=[x["net10"] for x in resolved if int(x["signal_date"][:4])==y]
            years[str(y)]={"events":len(vals),"mean_net10":statistics.fmean(vals) if vals else None}

        gates={
            "provenance_leakage_pass":True,
            "event_count_ge_30":n>=30,
            "mean_net10_gt_0":mean10>0,
            "pf_net10_gt_1":pf10>1.0,
            "stationary_bootstrap_p_le_0_10":boot["p_mean_le_zero"]<=0.10,
            "year_2023_nonnegative_if_ge5":years["2023"]["events"]<5 or years["2023"]["mean_net10"]>=0,
            "year_2024_nonnegative_if_ge5":years["2024"]["events"]<5 or years["2024"]["mean_net10"]>=0,
        }
        if n<30:
            classification="DISCOVERY_INSUFFICIENT_SAMPLE"
        elif all(gates.values()):
            classification="DISCOVERY_PASS_TO_INDEPENDENT_VALIDATION"
        else:
            classification="DISCOVERY_FAIL_NO_PROMOTION"
        valid_terminal=True
        receipt.update({
            "classification":classification,
            "mean_net10":mean10,
            "median_net10":median10,
            "win_rate_net10":win,
            "pf_net10":pf10,
            "mean_net20":mean20,
            "pf_net20":pf20,
            "bootstrap":boot,
            "year_blocks":years,
            "promotion_gates":gates,
            "all_promotion_gates_pass":all(gates.values()),
            "costs":{"base_round_trip_bps":10,"stress_round_trip_bps":20},
            "market_source":"Binance Data Vision Spot ETHUSDT 1d monthly klines + CHECKSUM",
            "market_instrument":"ETHUSDT spot",
            "accessed_2025_or_2026":False,
            "live_trading":False,
            "orders_created":False,
            "wallet_used":False,
            "exchange_mutation":False,
        })
    except Exception as exc:
        receipt.update({
            "classification":"DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE",
            "failure":f"{type(exc).__name__}: {str(exc)[:2000]}",
            "accessed_2025_or_2026":False,
            "live_trading":False,
            "orders_created":False,
            "wallet_used":False,
            "exchange_mutation":False,
        })
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "classification":receipt["classification"],
        "events":receipt.get("resolved_event_count"),
        "mean_net10":receipt.get("mean_net10"),
        "pf_net10":receipt.get("pf_net10"),
        "bootstrap_p":(receipt.get("bootstrap") or {}).get("p_mean_le_zero"),
        "all_gates":receipt.get("all_promotion_gates_pass"),
        "accessed_2025_or_2026":False,
        "live_trading":False
    },sort_keys=True,allow_nan=False))
    return 0 if valid_terminal else 2

if __name__=="__main__":
    sys.exit(main())
