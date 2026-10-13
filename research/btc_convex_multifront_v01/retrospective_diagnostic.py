#!/usr/bin/env python3
"""RETROSPECTIVE diagnostic ONLY (BTCUSDT 2021-2025).
Exact previously frozen F2 inputs; no 2026 outcomes. Public ZIP CHECKSUMs;
market-price proxy fills, *not* actual MEXC execution or independent OOS.
"""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import io
import json
import math
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parents[1] / "labs/btc-convex-trend-capture-001/prospective_shadow_snapshot_v0_2_aggressive.py"
H, FIVE = 3600_000, 300_000
FEE = 0.0008
START = datetime(2021,1,1,tzinfo=timezone.utc)
STOP = datetime(2026,1,1,tzinfo=timezone.utc)
START_MS = int(START.timestamp()*1000)
STOP_MS = int(STOP.timestamp()*1000)
OUT = ROOT / "historical_receipts"
BASE = "https://data.binance.vision/data/futures/um/monthly"

def load_parent():
    assert PARENT.exists(), "RECOVERED_PARENT_SOURCE_MISSING"
    src = importlib.util.spec_from_file_location("convex_parent_unchanged", PARENT)
    mod = importlib.util.module_from_spec(src)
    src.loader.exec_module(mod)
    return mod.build_signals

def month_strings():
    y,m=2020,12
    while (y,m)<=(2025,12):
        yield f"{y:04}-{m:02}"
        m+=1
        if m>12:y,m=y+1,1

def fetch(url, maxbytes):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url, headers={"User-Agent":"CryptoLab-HistoricalRetrospective/0.1"})
            with urllib.request.urlopen(req,timeout=40) as fh:
                data=fh.read(maxbytes+1)
            if len(data)>maxbytes: raise ValueError("MAX_SOURCE_BYTES_EXCEEDED:"+url)
            return data
        except (OSError, ValueError) as exc:
            last=exc
            time.sleep(1+attempt)
    raise RuntimeError("SOURCE_FETCH_BLOCKED:"+url+":"+repr(last))

def collect(kind, ym):
    if kind not in ("1h","5m","fundingRate"): raise ValueError("SOURCE_SCOPE_INVALID")
    if kind=="fundingRate":
        stem=f"fundingRate/BTCUSDT/BTCUSDT-fundingRate-{ym}.zip"
    else:
        stem=f"klines/BTCUSDT/{kind}/BTCUSDT-{kind}-{ym}.zip"
    url=BASE+"/"+stem
    blob=fetch(url,25_000_000)
    expected=fetch(url+".CHECKSUM",1000).decode("utf-8-sig").strip().split()[0].lower()
    digest=hashlib.sha256(blob).hexdigest()
    if len(expected)!=64 or expected!=digest:raise RuntimeError("PUBLISHER_SHA256_MISMATCH:"+url)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        csvs=[name for name in z.namelist() if name.lower().endswith(".csv")]
        if len(csvs)!=1:raise ValueError("ZIP_MEMBERS_INVALID:"+stem)
        raw=z.read(csvs[0]).decode("utf-8-sig")
    return list(csv.reader(io.StringIO(raw))), {
        "kind":kind,"month":ym,"official_url":url,"sha256":digest,"zip_bytes":len(blob)}

def ms(a):
    v=int(a)
    if v>10**14:v//=1000
    return v

def candles(rows, step):
    out={}
    for r in rows:
        if not r or not r[0].strip().isdigit():continue
        if len(r)<6:raise ValueError("MARKET_ROW_SCHEMA")
        t=ms(r[0])
        op,hi,lo,cl,vol=map(float,r[1:6])
        if t%step or not all(map(math.isfinite,(op,hi,lo,cl,vol))) or not (0<lo<=min(op,cl)<=max(op,cl)<=hi and vol>=0):
            raise ValueError("INVALID_OHLCV:"+str(t))
        if t in out:raise ValueError("DUPLICATE_SOURCE_KLINE")
        out[t]={"t":t,"open":op,"high":hi,"low":lo,"close":cl,"volume":vol}
    if not out:raise ValueError("EMPTY_KLINES")
    return out

def funding_records(rows):
    if not rows: raise ValueError("EMPTY_FUNDING")
    hdr=[x.strip().lower() for x in rows[0]]
    it=next((hdr.index(s) for s in ("calc_time","fundingtime") if s in hdr),None)
    ir=next((hdr.index(s) for s in ("last_funding_rate","fundingrate","rate") if s in hdr),None)
    if it is None or ir is None: raise ValueError("UNKNOWN_FUNDING_SCHEMA")
    out={}
    for r in rows[1:]:
        if not r:continue
        if len(r)<=max(it,ir):raise ValueError("BAD_FUNDING_RECORD")
        t=ms(r[it]);rate=float(r[ir])
        normalized=((t+H//2)//H)*H
        if abs(t-normalized)>1000 or not math.isfinite(rate): raise ValueError("FUNDING_INVALID_TIME_OR_RATE")
        if normalized in out and out[normalized]!=rate: raise ValueError("CONFLICTING_FUNDING")
        out[normalized]=rate
    if not out:raise ValueError("ZERO_FUNDING_SOURCE")
    return out

def source():
    bars1={}; bars5={}; funding={}; manifest=[]
    for ym in month_strings():
        is_warmup=(ym=="2020-12")
        for kind in (("1h",) if is_warmup else ("1h","5m","fundingRate")):
            rows,prov=collect(kind,ym);manifest.append(prov)
            block=(candles(rows,H) if kind=="1h" else candles(rows,FIVE) if kind=="5m" else funding_records(rows))
            dest=bars1 if kind=="1h" else bars5 if kind=="5m" else funding
            if set(dest).intersection(block):raise ValueError("DUPLICATE_CROSS_MONTH")
            dest.update(block)
        print("PROVENANCE_OK",ym,flush=True)
    start_warmup=int(datetime(2020,12,1,tzinfo=timezone.utc).timestamp()*1000)
    for name,dest,step,start in [
        ("one_hour",bars1,H,start_warmup),
        ("five_minute",bars5,FIVE,START_MS)]:
        expected=(STOP_MS-start)//step
        if len(dest)!=expected:
            missing=next((t for t in range(start,STOP_MS,step) if t not in dest),None)
            raise ValueError(f"COMPLETE_HISTORICAL_COVERAGE_BLOCKED:{name}:{len(dest)}/{expected}:first_missing={missing}")
    if any(t<START_MS or t>=STOP_MS for t in funding):
        raise ValueError("FUNDING_OUT_OF_SCOPE")
    # One genuine funding settlement typically every 8h; never treat a month
    # with an absent funding archive as free funding.
    if len(funding)<4000:
        raise ValueError("FUNDING_RECORD_COVERAGE_TOO_LOW")
    return bars1,bars5,funding,manifest

def backtest(signals,bars1,bars5,funding,slipbps,delay_hours=0):
    equity=10000.
    trades=[]
    next_free=START_MS
    slip=slipbps/10000.
    eq_peak=equity
    max_closed_dd=0
    max_5m_low_dd=0
    skipped_overlap=0
    omitted_data=0
    for i,b in enumerate(bars1):
        t=b["t"]
        if t<START_MS or t>=STOP_MS or not signals[i]:continue
        entry_t=t+H+FIVE+delay_hours*H
        if entry_t>=STOP_MS:continue
        if entry_t<next_free:
            skipped_overlap+=1
            continue
        if entry_t not in bars5:raise RuntimeError("SOURCE_MISSING_ENTRY")
        ent_bar=bars5[entry_t]
        entry=ent_bar["open"]*(1+slip)
        qty=equity*0.2/entry
        initial_eq=equity
        stop=entry*(1-0.0035)
        target=entry*(1+0.0075)
        entryfee=qty*entry*FEE
        exitprice=None; reason=None; exit_t=None; funding_usdt=0.0
        min_marked=equity
        for k in range(48):
            ts=entry_t+k*FIVE
            if ts>=STOP_MS:
                omitted_data+=1
                break
            bar=bars5.get(ts)
            if bar is None:raise ValueError("SOURCE_GAP")
            if k and ts in funding:
                # Binance market OPEN used as conservative/proxy funding mark.
                funding_usdt-=qty*bar["open"]*funding[ts]
            if bar["open"]<=stop:raw=bar["open"];reason="STOP_GAP"
            elif bar["open"]>=target:raw=bar["open"];reason="TARGET_GAP"
            elif bar["low"]<=stop:raw=stop;reason="STOP_FIRST"
            elif bar["high"]>=target:raw=target;reason="TARGET"
            elif k==47:raw=bar["close"];reason="TIME_EXIT"
            else:raw=None
            fee_est=qty*bar["low"]*FEE
            min_marked=min(min_marked, initial_eq+qty*(bar["low"]*(1-slip)-entry)-entryfee-fee_est+funding_usdt)
            if raw is not None:
                exitprice=raw*(1-slip)
                exit_t=ts+FIVE
                break
        if exitprice is None:
            break # right censored; zero realized PnL
        exitfee=qty*exitprice*FEE
        pnl=qty*(exitprice-entry)-entryfee-exitfee+funding_usdt
        equity+=pnl
        eq_peak=max(eq_peak,equity)
        max_closed_dd=min(max_closed_dd,equity/eq_peak-1)
        max_5m_low_dd=min(max_5m_low_dd,min_marked/eq_peak-1)
        next_free=exit_t
        trades.append({"entry_t":entry_t,"exit_t":exit_t,"year":datetime.fromtimestamp(exit_t/1000,tz=timezone.utc).year,
                       "net_usdt":pnl,"equity_after":equity,"entry":entry,"exit":exitprice,
                       "qty":qty,"reason":reason,"funding_usdt":funding_usdt,
                       "fee_usdt":entryfee+exitfee,"price_pnl_usdt":qty*(exitprice-entry),
                       "net_return_on_entry_notional_pct":pnl/(qty*entry)*100})
    wins=[x for x in trades if x["net_usdt"]>0]
    losses=[x for x in trades if x["net_usdt"]<=0]
    wg=sum(x["net_usdt"] for x in wins)
    lg=-sum(x["net_usdt"] for x in losses)
    year_pnl=defaultdict(float)
    for x in trades:year_pnl[x["year"]]+=x["net_usdt"]
    streak=0;maxstreak=0
    for x in trades:
        streak=0 if x["net_usdt"]>0 else streak+1
        maxstreak=max(maxstreak,streak)
    return {"initial_usdt":10000,"final_usdt":equity,"return_pct":100*(equity/10000-1),
            "closed_trades":len(trades),"wins":len(wins),"win_rate_pct":100*len(wins)/len(trades) if trades else None,
            "pf":wg/lg if lg else None,
            "max_closed_equity_dd_pct":100*max_closed_dd,
            "approx_intra_5m_low_dd_pct":100*max_5m_low_dd,
            "max_loss_streak":maxstreak,"overlap_skipped_signals":skipped_overlap,
            "right_censored":omitted_data,
            "year_pnl_usdt":dict(sorted(year_pnl.items())),
            "fee_usdt":sum(x["fee_usdt"] for x in trades),
            "funding_usdt":sum(x["funding_usdt"] for x in trades),
            "reason_counts":{key:sum(x["reason"]==key for x in trades) for key in ("STOP_FIRST","STOP_GAP","TARGET","TARGET_GAP","TIME_EXIT")},
            "trades":trades}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"HISTORICAL_DIAGNOSTIC_ONLY","period":"2021-01-01..2025-12-31",
            "venue":"Binance official historical USD-M market/funding, MEXC fills UNPROVEN",
            "already_seen":"Parent family historical BTC period; NOT independent OOS",
            "assumption":"market OHLC open as entry/exit proxy, fees 8bps side, 2/5bps assumed slip, funding uses market-price proxy not mark"}
    try:
        bars1,bars5,funding,manifest=source()
        report["manifest"]=manifest
        report["source_counts"]={"1h":len(bars1),"5m":len(bars5),"funding":len(funding)}
        signal_func=load_parent()
        hourly=[bars1[t] for t in sorted(bars1)]
        sig,_=signal_func(hourly)
        report["signals_on_2021_2025_1h"]=sum(a for a,b in zip(sig,hourly) if b["t"]>=START_MS)
        for s,name in [(2,"BASE"),(5,"STRESS")]:
            for delay,kind in ((0,"SCALP"),(6,"DELAYED_6H_PLACEBO")):
                label=f"{kind}_{name}"
                result=backtest(sig,hourly,bars5,funding,s,delay_hours=delay)
                report[label]={k:v for k,v in result.items() if k!="trades"}
                with (OUT/(label+"_TRADES.csv")).open("w",newline="",encoding="utf8") as fh:
                    rows=result["trades"]
                    if rows:
                        writer=csv.DictWriter(fh,fieldnames=rows[0].keys())
                        writer.writeheader();writer.writerows(rows)
        report["status"]="HISTORICAL_DIAGNOSTIC_SUCCESS_NO_OOS_CREDIT"
    except Exception as exc:
        report["status"]="SOURCE_OR_MODEL_BLOCKED"
        report["error"]=type(exc).__name__+":"+str(exc)
    (OUT/"HISTORICAL_RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf8")
    print(json.dumps({"status":report["status"],"source_counts":report.get("source_counts"),
                      "signals":report.get("signals_on_2021_2025_1h"),
                      "error":report.get("error"),
                      "scenarios":{k:v for k,v in report.items() if k.startswith(("SCALP_","DELAYED_"))}},indent=2))
    if report["status"]!="HISTORICAL_DIAGNOSTIC_SUCCESS_NO_OOS_CREDIT":
        sys.exit(2)

if __name__=="__main__":
    main()
