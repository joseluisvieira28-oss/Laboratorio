#!/usr/bin/env python3
"""Frozen primary Discovery for BTC-OPTIONS-VRP-BINANCE-001.

MVE: BOVRP-ATM30-24H-STRADDLE-CARRY-001
Primary only: 15 <= DTE < 31, target 30D, ATM by Binance BTCUSDT index,
08:00 UTC -> next day 08:00 UTC, executable option BBO, regular-user fees.

This script intentionally does NOT touch 2025/2026 and does NOT trade.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import math
import random
import re
import statistics
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

OPT_BASE="https://data.binance.vision/data/option/daily/EOHSummary/BTCUSDT/"
IDX_BASE="https://data.binance.vision/data/futures/um/daily/indexPriceKlines/BTCUSDT/1m/"
START=dt.date.fromisoformat("2023-05-18")
END=dt.date.fromisoformat("2023-10-23")
HOUR=8
DTE_MIN=15.0
DTE_MAX=31.0
TARGET_DTE=30.0
MIN_N=80
FEE_RATE=0.0003
CONTRACT_UNIT=1.0
OPT_SIZE=1.0
BOOT_REPS=10000
BOOT_BLOCK=5
BOOT_SEED=230911

def norm(x:str)->str:
    return re.sub(r"[^a-z0-9]+","_",x.strip().strip("[]").lower()).strip("_")

def parse_hour(v)->int|None:
    s=str(v).strip()
    try:
        f=float(s)
        if 0<=f<24:return int(f)
    except Exception:
        pass
    m=re.search(r"(\d{1,2})",s)
    if not m:return None
    h=int(m.group(1))
    return h if 0<=h<24 else None

def parse_expiry(symbol:str)->dt.datetime|None:
    m=re.search(r"(?:^|-)(\d{6})(?:-|$)",symbol)
    if not m:return None
    try:
        x=dt.datetime.strptime(m.group(1),"%y%m%d").replace(tzinfo=dt.timezone.utc)
        return x.replace(hour=8)
    except ValueError:
        return None

def parse_strike(raw,symbol:str)->float:
    s=str(raw).strip()
    try:return float(s)
    except ValueError:pass
    m=re.fullmatch(r"(\d{6})-([0-9]+(?:\.[0-9]+)?)",s)
    if not m:raise ValueError("unrecognized strike")
    sm=re.search(r"(?:^|-)(\d{6})-([0-9]+(?:\.[0-9]+)?)(?:-|$)",symbol)
    if not sm:raise ValueError("symbol strike unavailable")
    if sm.group(1)!=m.group(1):raise ValueError("expiry token mismatch")
    if float(sm.group(2))!=float(m.group(2)):raise ValueError("strike mismatch")
    return float(m.group(2))

def get_bytes(url:str)->bytes|None:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-FrozenDiscovery/0.1"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:return r.read()
    except urllib.error.HTTPError as e:
        if e.code==404:return None
        raise

def opt_url(ds:str)->str:
    return f"{OPT_BASE}BTCUSDT-EOHSummary-{ds}.zip"

def idx_url(ds:str)->str:
    return f"{IDX_BASE}BTCUSDT-1m-{ds}.zip"

def load_options_0800(ds:str,raw:bytes)->dict[str,dict]:
    out={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:raise RuntimeError(f"{ds}: unexpected option zip")
        with z.open(names[0]) as fh:
            reader=csv.DictReader(io.TextIOWrapper(fh,encoding="utf-8-sig",newline=""))
            by={norm(h):h for h in (reader.fieldnames or [])}
            required=["hour","symbol","type","strike","best_bid_price","best_bid_qty","best_ask_price","best_ask_qty"]
            miss=[k for k in required if k not in by]
            if miss:raise RuntimeError(f"{ds}: missing option fields {miss}")
            snap_dt=dt.datetime.fromisoformat(ds).replace(hour=8,tzinfo=dt.timezone.utc)
            for row in reader:
                if parse_hour(row.get(by["hour"],""))!=HOUR:continue
                symbol=str(row.get(by["symbol"],"")).strip()
                expiry=parse_expiry(symbol)
                if not symbol or expiry is None:continue
                typ=str(row.get(by["type"],"")).strip().upper()
                if typ not in {"C","P","CALL","PUT"}:continue
                right="C" if typ in {"C","CALL"} else "P"
                try:
                    strike=parse_strike(row.get(by["strike"],""),symbol)
                    bid=float(row.get(by["best_bid_price"],""))
                    ask=float(row.get(by["best_ask_price"],""))
                    bqty=float(row.get(by["best_bid_qty"],""))
                    aqty=float(row.get(by["best_ask_qty"],""))
                except Exception:
                    continue
                if not (bid>0 and ask>0 and bqty>0 and aqty>0 and ask>=bid):
                    continue
                dte=(expiry-snap_dt).total_seconds()/86400.0
                out[symbol]={
                    "symbol":symbol,"right":right,"strike":strike,
                    "expiry":expiry.date().isoformat(),"dte":dte,
                    "bid":bid,"ask":ask,"bid_qty":bqty,"ask_qty":aqty
                }
    return out

def load_index_0800(ds:str,raw:bytes)->float:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:raise RuntimeError(f"{ds}: unexpected index zip")
        with z.open(names[0]) as fh:
            reader=csv.reader(io.TextIOWrapper(fh,encoding="utf-8-sig",newline=""))
            for row in reader:
                if len(row)<2:continue
                try:
                    ts=int(row[0]); sec=ts/1000 if ts>10_000_000_000 else ts
                    x=dt.datetime.fromtimestamp(sec,dt.timezone.utc)
                    if x.hour==8 and x.minute==0:
                        px=float(row[1])
                        if px<=0:raise RuntimeError(f"{ds}: nonpositive index")
                        return px
                except ValueError:
                    continue
    raise RuntimeError(f"{ds}: 08:00 index not found")

def fee(option_price:float,index_price:float)->float:
    return min(FEE_RATE*index_price*CONTRACT_UNIT,0.10*option_price)*OPT_SIZE

def choose_pair(entry:dict[str,dict],exit_:dict[str,dict],index_px:float):
    by_key=defaultdict(dict)
    for sym,r in entry.items():
        if not (DTE_MIN<=r["dte"]<DTE_MAX):continue
        if sym not in exit_:continue
        er=exit_[sym]
        if not (er["bid"]>0 and er["ask"]>0 and er["bid_qty"]>0 and er["ask_qty"]>0 and er["ask"]>=er["bid"]):
            continue
        by_key[(r["expiry"],r["strike"])][r["right"]]=(r,er)
    candidates=[]
    for (expiry,strike),legs in by_key.items():
        if "C" not in legs or "P" not in legs:continue
        call_e,call_x=legs["C"]; put_e,put_x=legs["P"]
        dte=call_e["dte"]
        if abs(put_e["dte"]-dte)>1e-9:continue
        candidates.append({
            "expiry":expiry,"strike":strike,"dte":dte,
            "call_e":call_e,"call_x":call_x,"put_e":put_e,"put_x":put_x
        })
    if not candidates:return None
    expiries=sorted({(c["expiry"],c["dte"]) for c in candidates},key=lambda x:(abs(x[1]-TARGET_DTE),x[1],x[0]))
    chosen_expiry=expiries[0][0]
    cands=[c for c in candidates if c["expiry"]==chosen_expiry]
    cands.sort(key=lambda c:(abs(math.log(c["strike"]/index_px)),c["strike"]))
    return cands[0] if cands else None

def percentile(xs,p):
    ys=sorted(xs)
    if not ys:return float("nan")
    if len(ys)==1:return ys[0]
    pos=(len(ys)-1)*p
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi:return ys[lo]
    w=pos-lo
    return ys[lo]*(1-w)+ys[hi]*w

def circular_block_bootstrap_mean(values):
    rng=random.Random(BOOT_SEED)
    n=len(values); means=[]
    for _ in range(BOOT_REPS):
        sample=[]
        while len(sample)<n:
            start=rng.randrange(n)
            for j in range(BOOT_BLOCK):
                sample.append(values[(start+j)%n])
                if len(sample)>=n:break
        means.append(sum(sample)/n)
    return percentile(means,0.025),percentile(means,0.975)

def skew(values):
    n=len(values)
    if n<3:return float("nan")
    mu=sum(values)/n
    m2=sum((x-mu)**2 for x in values)/n
    if m2<=0:return 0.0
    m3=sum((x-mu)**3 for x in values)/n
    return m3/(m2**1.5)

def max_losing_streak(pnls):
    best=cur=0
    for x in pnls:
        if x<0:
            cur+=1;best=max(best,cur)
        else:cur=0
    return best

def main():
    opt_cache={}; idx_cache={}; option_hashes={}; index_hashes={}
    def get_opt(ds):
        if ds not in opt_cache:
            raw=get_bytes(opt_url(ds))
            if raw is None:
                opt_cache[ds]=None
            else:
                option_hashes[ds]=hashlib.sha256(raw).hexdigest()
                opt_cache[ds]=load_options_0800(ds,raw)
        return opt_cache[ds]
    def get_idx(ds):
        if ds not in idx_cache:
            raw=get_bytes(idx_url(ds))
            if raw is None:
                idx_cache[ds]=None
            else:
                index_hashes[ds]=hashlib.sha256(raw).hexdigest()
                idx_cache[ds]=load_index_0800(ds,raw)
        return idx_cache[ds]

    trades=[]; skipped=defaultdict(int)
    d=START
    while d<=END:
        d1=d+dt.timedelta(days=1)
        ds=d.isoformat(); ds1=d1.isoformat()
        e=get_opt(ds); x=get_opt(ds1)
        if e is None:
            skipped["entry_option_source_missing"]+=1; d=d1; continue
        if x is None:
            skipped["exit_option_source_missing"]+=1; d=d1; continue
        i0=get_idx(ds); i1=get_idx(ds1)
        if i0 is None or i1 is None:
            skipped["index_source_missing"]+=1; d=d1; continue
        pair=choose_pair(e,x,i0)
        if pair is None:
            skipped["no_primary_executable_pair"]+=1; d=d1; continue

        ce,cx,pe,px=pair["call_e"],pair["call_x"],pair["put_e"],pair["put_x"]
        entry_credit=(ce["bid"]+pe["bid"])*OPT_SIZE
        exit_debit=(cx["ask"]+px["ask"])*OPT_SIZE
        if entry_credit<=0:
            skipped["nonpositive_entry_credit"]+=1; d=d1; continue
        fees=(
            fee(ce["bid"],i0)+fee(pe["bid"],i0)+
            fee(cx["ask"],i1)+fee(px["ask"],i1)
        )
        gross=entry_credit-exit_debit
        net=gross-fees
        ret=net/entry_credit
        trades.append({
            "date":ds,"exit_date":ds1,"expiry":pair["expiry"],"entry_dte":pair["dte"],
            "strike":pair["strike"],"entry_index":i0,"exit_index":i1,
            "entry_credit":entry_credit,"exit_debit":exit_debit,
            "fees":fees,"gross_pnl":gross,"net_pnl":net,"net_premium_return":ret
        })
        d=d1

    n=len(trades)
    verdict="INSUFFICIENT_EXECUTABLE_SAMPLE"
    stats={}
    gates={}
    if n>0:
        rets=[t["net_premium_return"] for t in trades]
        pnls=[t["net_pnl"] for t in trades]
        mean=sum(rets)/n
        median=statistics.median(rets)
        positive_fraction=sum(x>0 for x in pnls)/n
        pos=sum(x for x in pnls if x>0)
        neg=-sum(x for x in pnls if x<0)
        pf=float("inf") if neg==0 and pos>0 else (pos/neg if neg>0 else 0.0)
        blo,bhi=circular_block_bootstrap_mean(rets)
        k=max(1,math.ceil(0.05*n))
        cvar=sum(sorted(rets)[:k])/k

        monthly=defaultdict(list)
        for t in trades: monthly[t["date"][:7]].append(t["net_premium_return"])
        monthly_means={m:sum(v)/len(v) for m,v in sorted(monthly.items())}
        positive_months=sum(v>0 for v in monthly_means.values())

        lomo={}
        for m in sorted(monthly):
            vals=[t["net_premium_return"] for t in trades if t["date"][:7]!=m]
            lomo[m]=sum(vals)/len(vals) if vals else float("nan")
        lomo_positive=sum(v>0 for v in lomo.values() if not math.isnan(v))

        stats={
            "N":n,"mean_net_premium_return":mean,"median_net_premium_return":median,
            "positive_fraction":positive_fraction,"profit_factor_on_net_pnl":pf,
            "bootstrap_95_ci_mean":[blo,bhi],"worst_trade":min(rets),"best_trade":max(rets),
            "CVaR_5pct":cvar,"skew":skew(rets),"max_losing_streak":max_losing_streak(pnls),
            "monthly_means":monthly_means,"positive_month_count":positive_months,
            "leave_one_month_out_means":lomo,"leave_one_month_out_positive_count":lomo_positive
        }
        gates={
            "primary_n_gte_80":n>=80,
            "mean_net_premium_return_gt_0":mean>0,
            "median_net_premium_return_gt_0":median>0,
            "profit_factor_gt_1":pf>1,
            "bootstrap_95_lower_mean_gt_0":blo>0,
            "positive_months_gte_4":positive_months>=4,
            "leave_one_month_out_positive_count_gte_5":lomo_positive>=5
        }
        if n>=MIN_N:
            verdict="DISCOVERY_PASS_SHORT_VOL_CARRY_SIGNAL" if all(gates.values()) else "DISCOVERY_FAIL_NO_PROMOTION"

    manifest={
        "options_zip_hash_chain":hashlib.sha256("".join(f"{k}:{option_hashes[k]}\n" for k in sorted(option_hashes)).encode()).hexdigest(),
        "index_zip_hash_chain":hashlib.sha256("".join(f"{k}:{index_hashes[k]}\n" for k in sorted(index_hashes)).encode()).hexdigest(),
        "option_source_days_hashed":len(option_hashes),
        "index_source_days_hashed":len(index_hashes)
    }
    receipt={
        "lab_id":"BTC-OPTIONS-VRP-BINANCE-001",
        "mve_id":"BOVRP-ATM30-24H-STRADDLE-CARRY-001",
        "verdict":verdict,
        "primary_dte":"15<=DTE<31; target 30D",
        "decision_time_utc":"08:00",
        "hold_hours":24,
        "fee_rate_regular_user":FEE_RATE,
        "contract_unit_btc":CONTRACT_UNIT,
        "source_manifest":manifest,
        "skipped":dict(skipped),
        "stats":stats,
        "gates":gates,
        "trades":trades,
        "secondary_strata_opened":False,
        "access_2025":False,"access_2026":False,
        "live_trading":False,"exchange_mutation":False
    }
    Path("binance_vrp_discovery_receipt_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "verdict":verdict,"N":n,
        "mean_net_premium_return":stats.get("mean_net_premium_return"),
        "median_net_premium_return":stats.get("median_net_premium_return"),
        "profit_factor":stats.get("profit_factor_on_net_pnl"),
        "bootstrap_95_ci_mean":stats.get("bootstrap_95_ci_mean"),
        "positive_month_count":stats.get("positive_month_count"),
        "lomo_positive_count":stats.get("leave_one_month_out_positive_count"),
        "gates":gates
    },sort_keys=True))
    return 0 if verdict=="DISCOVERY_PASS_SHORT_VOL_CARRY_SIGNAL" else 2

if __name__=="__main__":
    raise SystemExit(main())
