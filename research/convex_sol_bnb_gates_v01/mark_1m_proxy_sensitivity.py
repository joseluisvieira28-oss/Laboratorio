"""Public historical 1m mark-price bar OPEN sensitivity. NEVER exact settlement mark.

Separate source gate frozen after fundingRate API HTTP451 SOURCE_BLOCKED.
Original V5 signals, costs, stops and portfolio remain bytewise original.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,zipfile
from datetime import datetime,timezone
from pathlib import Path
from research.convex_sol_bnb_gates_v01 import exact_funding_mark as prior
from research.convex_8alt_common_2023_25 import common_3yr as old
from research.convex_multialt_4tf_20261013 import multialt_matrix as source
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src
from research.btc_convex_timeframe_matrix_20261013 import matrix as engine

MINUTE=60_000
MONTHS=tuple(f"{y:04d}-{mo:02d}" for y in range(2023,2026) for mo in range(1,13))

def get_verified_mark_minute(symbol,month):
    prior.approved_symbol(symbol)
    if month not in MONTHS:raise ValueError("UNFROZEN_MARK_MONTH")
    url=f"https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{symbol}/1m/{symbol}-1m-{month}.zip"
    zipped=src.fetch(url,30_000_000)
    wanted=src.fetch(url+".CHECKSUM",1200).decode("utf-8-sig").strip().split()[0].lower()
    sha=hashlib.sha256(zipped).hexdigest()
    if not re.fullmatch("[0-9a-f]{64}",wanted) or sha!=wanted:
        raise ValueError("BINANCE_PUBLISHER_MARK_1M_SHA256_MISMATCH:"+month)
    with zipfile.ZipFile(io.BytesIO(zipped)) as z:
        names=[x for x in z.namelist() if x.lower().endswith(".csv")]
        if len(names)!=1:raise ValueError("ONE_MARK_MINUTE_CSV_MEMBER_REQUIRED")
        raw=z.read(names[0]).decode("utf-8-sig")
    parsed={}
    for line in csv.reader(io.StringIO(raw)):
        if not line or not line[0].strip().isdigit():continue
        ts=src.ms(line[0])
        if ts%MINUTE or ts in parsed:
            raise ValueError("BAD_OR_DUPLICATE_MARK_1M_TIMESTAMP")
        v=float(line[1])
        if not math.isfinite(v) or v<=0:
            raise ValueError("NONPOSITIVE_MARK_1M_OPEN")
        parsed[ts]=v
    return parsed,{"official_url":url,"sha256_zip":sha,"bars":len(parsed),"month":month}

def verify_funding_against_parent(symbol,funding,previous_sha):
    old.apply_locked_3year_window()
    receipts=[]
    source_rates={}
    for mo in MONTHS:
        rows,rec=source.fetch_archive(symbol,"fundingRate",mo)
        if rec["sha256_zip"]!=previous_sha.get(mo):
            raise ValueError("PARENT_FUNDING_SHA_CHANGED:"+mo)
        block=src.funding_records(rows)
        if set(source_rates)&set(block):
            raise ValueError("FUNDING_EVENT_DUPLICATED_MONTHS")
        source_rates.update(block)
        receipts.append(rec)
    if len(source_rates)!=3288 or source_rates!=funding:
        raise ValueError("ORIGINAL_FUNDING_RATE_SOURCE_MISMATCH")
    return receipts

def complete_mark_minute(symbol,funding):
    mark={}
    receipts=[]
    for mo in MONTHS:
        allbars,receipt=get_verified_mark_minute(symbol,mo)
        month_start=int(datetime(int(mo[:4]),int(mo[5:7]),1,tzinfo=timezone.utc).timestamp()*1000)
        y,m=int(mo[:4]),int(mo[5:7])
        y2,m2=(y+1,1) if m==12 else (y,m+1)
        month_end=int(datetime(y2,m2,1,tzinfo=timezone.utc).timestamp()*1000)
        missing=[]
        for ts in sorted(t for t in funding if month_start<=t<month_end):
            if ts not in allbars:
                missing.append(ts)
            else:mark[ts]=allbars[ts]
        receipt["funding_month_events"]=sum(month_start<=t<month_end for t in funding)
        receipt["unresolved_funding_mark_minute_bars"]=len(missing)
        receipt["first_5_missing_marks"]=missing[:5]
        receipts.append(receipt)
        print("PUBLIC_1M_MARK_SOURCE",symbol,mo,
              "month_bar_count",len(allbars),"funding_marks_missing",len(missing),flush=True)
    if len(mark)!=3288:
        raise ValueError(f"MARK_1M_OPEN_FULL_SETTLEMENT_COVERAGE_MISSING:{len(mark)}/3288")
    return mark,receipts

def replay(symbol,prior_artifact_dir):
    sha,pair_fp=prior.previous_artifact_baseline(prior_artifact_dir,symbol)
    old.apply_locked_3year_window()
    five,one,funding,manifest=source.fetch_all(symbol)
    parent_funding_receipts=verify_funding_against_parent(symbol,funding,sha)
    mark1,mark_receipts=complete_mark_minute(symbol,funding)
    spread=[]
    adjusted={}
    for t in sorted(funding):
        bar=five.get(t)
        if not bar or bar["open"]<=0:
            raise ValueError("MISSING_OR_INVALID_5M_MARKET_FUNDING_PROXY:"+str(t))
        market=bar["open"]
        val=mark1[t]
        adjusted[t]=funding[t]*val/market
        spread.append({"ts":t,"mark_minute_open":val,"market_5m_open":market,
                       "relative_difference_pct":100*(val/market-1)})
    span=prior.PAIRS[symbol][1]
    bars=engine.resample(five,span)
    result={}
    for name,bps in (("BASE",2),("STRESS",5)):
        baseline=engine.simulate(span,bars,five,funding,bps)
        expected=pair_fp[name]
        for key,current,was in (
            ("return",baseline["marked_return_pct"],expected["return_pct"]),
            ("trades",baseline["closed_trades"],expected["trades"]),
            ("funding",baseline["funding_usdt"],expected["funding_usdt"]),
            ("PF",baseline["profit_factor"],expected["pf"])):
            if not math.isclose(current,was,rel_tol=1e-8,abs_tol=0.0001):
                raise ValueError(f"PARENT_V5_BASELINE_CHANGED:{symbol}:{name}:{key}:{current}/{was}")
        alt=engine.simulate(span,bars,five,adjusted,bps)
        result[name]={
            "baseline_market_open_funding_return_pct":baseline["marked_return_pct"],
            "mark_1m_open_proxy_return_pct":alt["marked_return_pct"],
            "delta_pp":alt["marked_return_pct"]-baseline["marked_return_pct"],
            "baseline_funding_usdt":baseline["funding_usdt"],
            "mark_1m_open_proxy_funding_usdt":alt["funding_usdt"],
            "funding_cashflow_difference_usdt":alt["funding_usdt"]-baseline["funding_usdt"],
            "baseline_pf":baseline["profit_factor"],
            "proxy_pf":alt["profit_factor"],
            "baseline_closed_trades":baseline["closed_trades"],
            "proxy_closed_trades":alt["closed_trades"],
            "baseline_drawdown_pct":baseline["max_5m_low_stress_dd_pct"],
            "proxy_drawdown_pct":alt["max_5m_low_stress_dd_pct"],
            "venue_execution_verified":False,"actual_funding_mark_proven":False}
    diff=sorted(abs(x["relative_difference_pct"]) for x in spread)
    return {
      "status":"OFFICIAL_MARK_1M_OPEN_PROXY_REPLAY_PASS_NOT_EXACT_MARK_NOT_OOS",
      "pairs":result,
      "source_comparison":{
        "settlement_events":len(spread),
        "median_abs_mark1m_vs_market5m_pct":diff[len(diff)//2],
        "max_abs_mark1m_vs_market5m_pct":max(diff),
        "worst_10_mark_vs_market":[x for x in sorted(spread,key=lambda r:abs(r["relative_difference_pct"]),reverse=True)[:10]]
      },
      "mark1m_official_publisher_sha256_receipts":mark_receipts,
      "funding_original_archive_receipts":parent_funding_receipts
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=tuple(prior.PAIRS))
    p.add_argument("--prior-artifact",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    receipt={"symbol":a.symbol,"status":"SOURCE_BLOCKED","experiment":"F1B_SEPARATELY_FROZEN_1M_MARK_OPEN_PROXY",
             "prior_funding_api_451_gate":"REMAINS_SOURCE_BLOCKED",
             "economic_outcome_role":"KNOWN_2023_25_RETROSPECTIVE_ONLY",
             "actual_settlement_mark_verified":False,"trading_authority":"NONE"}
    try:receipt.update(replay(a.symbol,a.prior_artifact))
    except Exception as exc:receipt["block_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"MARK_1M_PROXY_RESULT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("MARK_1M_PROXY_FINAL",json.dumps({k:v for k,v in receipt.items() if k in ("symbol","status","block_reason","pairs","source_comparison")},sort_keys=True),flush=True)
    if receipt["status"]!="OFFICIAL_MARK_1M_OPEN_PROXY_REPLAY_PASS_NOT_EXACT_MARK_NOT_OOS":
        raise SystemExit(2)
if __name__=="__main__":main()
