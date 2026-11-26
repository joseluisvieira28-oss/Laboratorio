#!/usr/bin/env python3
"""LIQMAP003 independent historical real-position BTC hypothesis. NOT HyperQuant map.
Daily published-file timestamp may NOT attest original point-in-time publication.
Read-only public HF/Hyperliquid, no wallets published, no trading accounts.
"""
import collections
import concurrent.futures as cf
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"backtest_results"
UP=HERE.parent/"liqmap-diamante-002"
sys.path.insert(0,str(UP))
import settle
import rollup
H=3600000
START=dt.date(2026,7,1)
END=dt.date(2026,10,13)
HF="https://huggingface.co/api/datasets/ProbioticFarmer/hyperliquid-augmented-copytrading/tree/main/snapshots_perp?recursive=true&limit=1000"
RESOLVE="https://huggingface.co/datasets/ProbioticFarmer/hyperliquid-augmented-copytrading/resolve/main/"
INFO="https://api.hyperliquid.xyz/info"
UA={"User-Agent":"CryptoLab-LIQMAP003-NoTrading-Scientific-Replay/1.0"}
MAXFILE=35_000_000
TIMEOUT=80
FEES=(10,35,80)

def now():
    return dt.datetime.now(dt.timezone.utc)
def ms(t):
    return int(t.timestamp()*1000)
def get(url,max_bytes=4_000_000):
    t0=now().isoformat()
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=TIMEOUT) as response:
        raw=response.read(max_bytes+1)
    t1=now().isoformat()
    if len(raw)>max_bytes:raise ValueError("SOURCE_BLOCKED response too big")
    return raw,{"url":url,"start_utc":t0,"end_utc":t1,
        "raw_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def archive_files():
    raw,receipt=get(HF)
    items=json.loads(raw)
    mapping=collections.defaultdict(list)
    for row in items:
        if row.get("type")!="file":continue
        path=row.get("path","")
        d=re.search(r"date=(20\d\d-\d\d-\d\d)/",path)
        if d:
            mapping[d.group(1)].append({"path":path,"bytes":row.get("size"),
                      "lfs_oid":row.get("lfs",{}).get("oid")})
    if len(items)>=1000:raise ValueError("SOURCE_BLOCKED HF tree may be truncated")
    return mapping,receipt

def claim_time(date,path):
    m=re.search(r"_([0-9]{13})[.]parquet$",path)
    if not m:raise ValueError("UNVERIFIABLE file as-of timestamp")
    t=dt.datetime.fromtimestamp(int(m.group(1))/1000,dt.timezone.utc)
    if t.date()!=date or t.hour>=12:raise ValueError("UNVERIFIABLE claimed daily as-of")
    return t

def position_levels(values,mark):
    """HYPOTHESIS: actual positive-price liquidation zones; same LIQMAP002 bins and score."""
    if mark<=0:raise ValueError("invalid mark")
    bins=collections.defaultdict(float)
    good=0
    for size,liq in values:
        try:sz=float(size);px=float(liq)
        except (ValueError,TypeError):continue
        if not all(math.isfinite(z) for z in (sz,px)) or sz==0 or px<=0:continue
        if sz>0 and px>=mark:continue
        if sz<0 and px<=mark:continue
        key=math.floor(math.log(px)/.005)
        center=math.exp((key+.5)*.005)
        d=math.log(center/mark)
        if not .005<=abs(d)<=.05:continue
        if sz>0 and d>=0 or sz<0 and d<=0:continue
        bins[key]+=abs(sz)*px*math.exp(-abs(d)/.03)
        good+=1
    if good<100:raise ValueError("SOURCE_BLOCKED fewer than 100 valid BTC liquidation levels")
    if not bins:raise ValueError("SOURCE_BLOCKED no candidate price bins")
    best=min(bins,key=lambda b:(-bins[b],b))
    target=math.exp((best+.5)*.005)
    return {"mark":mark,"target":target,"mirror":mark*mark/target,
       "signal":"UP" if target>mark else "DOWN",
       "distance_log":abs(math.log(target/mark)),
       "mass_weighted_not_actual_liquidations":bins[best],
       "n_valid_positions_eligible":good}

def extract_positions(raw,day,path):
    t=claim_time(day,path)
    tab=pq.read_table(io.BytesIO(raw),columns=["market","size","notional","liquidation_price"])
    btc=tab.filter(pc.equal(tab.column("market"),pa.scalar("BTC")))
    if btc.num_rows<1000:raise ValueError("SOURCE_BLOCKED fewer than 1000 BTC rows")
    sizes=btc.column("size").to_pylist()
    notionals=btc.column("notional").to_pylist()
    lps=btc.column("liquidation_price").to_pylist()
    marks=[]
    for s,n in zip(sizes,notionals):
        try:
            s=float(s);n=float(n)
            if math.isfinite(s) and math.isfinite(n) and abs(s)>0 and abs(n)>0:
                v=abs(n/s)
                if 100<v<1e6:marks.append(v)
        except (ValueError,TypeError,ZeroDivisionError):pass
    if len(marks)<500:raise ValueError("SOURCE_BLOCKED notional-to-size mark unavailable")
    mark=statistics.median(marks)
    levels=position_levels(zip(sizes,lps),mark)
    return {"claimed_utc":t.isoformat(),"claimed_ms":ms(t),
          "btc_rows":btc.num_rows,"mark_median_inferred_from_notional_per_size":mark,
          "valid_mark_rows":len(marks),**levels}

def fetch_day(day,metadata):
    path=metadata["path"]
    t=claim_time(day,path)
    expected=metadata["lfs_oid"]
    if not expected or len(expected)!=64:raise ValueError("SOURCE_BLOCKED missing LFS digest")
    if not isinstance(metadata["bytes"],int) or metadata["bytes"]>MAXFILE:
        raise ValueError("SOURCE_BLOCKED abnormal or large file size")
    url=RESOLVE+path+"?download=true"
    last=None
    for attempt in range(2):
        try:
            raw,receipt=get(url,MAXFILE)
            if len(raw)!=metadata["bytes"] or receipt["raw_sha256"]!=expected:
                raise ValueError("SOURCE_BLOCKED LFS bytes/hash mismatch")
            features=extract_positions(raw,day,path)
            return {"date":str(day),"status":"SOURCE_PASS",
                    "hf_file_lfs_sha256":expected,"receipt":receipt,
                    "features":features}
        except Exception as e:last=e
    return {"date":str(day),"status":"SOURCE_BLOCKED",
            "error":type(last).__name__+": "+str(last)[:260],
            "file_path":path}

def hl_prices(first,last):
    body=json.dumps({"type":"candleSnapshot",
         "req":{"coin":"BTC","interval":"1h","startTime":first,"endTime":last-1}},
         separators=(",",":")).encode()
    t0=now().isoformat()
    req=urllib.request.Request(INFO,data=body,method="POST",
         headers={"Content-Type":"application/json",**UA})
    with urllib.request.urlopen(req,timeout=80) as response:
        raw=response.read(2_500_000)
    t1=now().isoformat()
    if len(raw)>=2_500_000:raise ValueError("PRICE_SOURCE_BLOCKED payload >2.5 MB")
    obj=json.loads(raw)
    if not isinstance(obj,list):raise ValueError("PRICE_SOURCE_BLOCKED not list")
    data={}
    for row in obj:
        t=int(row["t"])
        if not first<=t<last:continue
        o,hi,lo,cl=(float(row[k]) for k in ("o","h","l","c"))
        if not all(math.isfinite(x) and x>0 for x in (o,hi,lo,cl)) or not lo<=min(o,cl)<=max(o,cl)<=hi:
            raise ValueError("PRICE_SOURCE_BLOCKED invalid candle")
        if t in data:raise ValueError("PRICE_SOURCE_BLOCKED duplicate")
        if int(row["T"])!=t+H-1:raise ValueError("PRICE_SOURCE_BLOCKED candle end mismatch")
        data[t]={"t":t,"o":o,"h":hi,"l":lo,"c":cl}
    expected=(last-first)//H
    if len(data)!=expected or any(first+i*H not in data for i in range(expected)):
        raise ValueError("PRICE_SOURCE_BLOCKED gap "+str(len(data))+"/"+str(expected))
    return data,{"url":INFO,"request_sha256":hashlib.sha256(body).hexdigest(),
         "raw_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
         "start_utc":t0,"end_utc":t1,"price_hours":len(data)}

def first_touch_record(row,prices):
    a=row["features"];claim=a["claimed_ms"]
    t0=claim//H*H
    prev_t=t0-H
    older=prev_t-24*H
    future=t0+H
    if any(t not in prices for t in (prev_t,older)):
        raise ValueError("PRICE_SOURCE_BLOCKED missing momentum history")
    prior_close=prices[prev_t]["c"]
    if not abs(prior_close/a["mark"]-1)<.05:
        raise ValueError("SOURCE_BLOCKED snapshot mark deviates >5% from prior HL price")
    bars=[prices[future+i*H] for i in range(24)]
    mom="UP" if prior_close>prices[older]["c"] else "DOWN"
    target=a["target"];mirror=a["mirror"];mark=a["mark"];signal=a["signal"]
    observed=settle.touch(bars,mark,target,mirror)
    result={"date":row["date"],"claimed_utc":a["claimed_utc"],
        "source_hf_sha256":row["hf_file_lfs_sha256"],"btc_rows":a["btc_rows"],
        "valid_level_positions":a["n_valid_positions_eligible"],
        "mark":mark,"prior_hl_close":prior_close,
        "reference_mark_discrepancy_pct":100*(mark/prior_close-1),
        "target":target,"mirror":mirror,
        "distance_pct":100*(math.exp(a["distance_log"])-1),
        "signal":signal,"momentum24":mom,
        "first_touch_kind":observed["kind"],
        "map_classification":settle.classify(observed,signal),
        "mom_classification":settle.classify(observed,mom),
        "simulated_futures_net_bps":{},"source_asof_warning":"claimed_file_epoch_no_per_row_ts"}
    for fee in FEES:
        result["simulated_futures_net_bps"][str(fee)]={
           "map":settle.pnl(bars,observed,signal,mark,target,mirror,fee)["net_bps"],
           "mom24":settle.pnl(bars,observed,mom,mark,target,mirror,fee)["net_bps"]}
    return result

def result_gate(outcomes,all_days):
    scored=[x for x in outcomes if x.get("status")=="EVENT_PASS"]
    resolved=[x for x in scored if x["map_classification"] in ("TARGET_FIRST","MIRROR_FIRST")]
    wins=sum(x["map_classification"]=="TARGET_FIRST" for x in resolved)
    paired=[x for x in resolved if x["mom_classification"] in ("TARGET_FIRST","MIRROR_FIRST")]
    mm=sum(x["map_classification"]=="TARGET_FIRST" for x in paired)
    mo=sum(x["mom_classification"]=="TARGET_FIRST" for x in paired)
    excess=(mm-mo)/len(paired) if paired else None
    nets=[x["simulated_futures_net_bps"]["80"]["map"] for x in scored]
    paired_diffs=[(x["date"],x["simulated_futures_net_bps"]["80"]["map"]-
                 x["simulated_futures_net_bps"]["80"]["mom24"]) for x in scored]
    ci=rollup.bootstrap_by_week(paired_diffs,seed=3003)
    month=collections.defaultdict(list)
    for date,val in paired_diffs:month[date[:7]].append(val)
    positive_months=sum(statistics.mean(v)>0 for v in month.values())
    ciw=rollup.wilson(wins,len(resolved))
    gates={"min_60_valid_sources":len(scored)>=60,
         "min_50_resolved":len(resolved)>=50,
         "Wilson_low_gt_half":ciw["low"] is not None and ciw["low"]>.5,
         "paired_plus_5pp":excess is not None and excess>.05,
         "mean_net80_positive":bool(nets) and statistics.mean(nets)>0,
         "weekly_bootstrap_lower_positive":ci["low"] is not None and ci["low"]>0,
         "two_months_positive_paired_excess":positive_months>=2}
    if len(scored)<60:scientific="SOURCE_INSUFFICIENT"
    elif len(resolved)<50:scientific="SCIENTIFIC_INCONCLUSIVE_INSUFFICIENT_FIRST_TOUCH"
    else:scientific="HYPOTHESIS_NO_GO" if not all(gates.values()) else "HISTORICAL_SHADOW_CANDIDATE_ONLY"
    return {"calendar_days":len(all_days),"valid_source_and_outcome":len(scored),
       "blocked_dates":len(outcomes)-len(scored),
       "resolved":len(resolved),"target_first":wins,"mirror_first":len(resolved)-wins,
       "ambiguous":sum(x["map_classification"]=="AMBIGUOUS" for x in scored),
       "neither":sum(x["map_classification"]=="NEITHER" for x in scored),
       "hit_rate":wins/len(resolved) if resolved else None,"wilson95":ciw,
       "paired_resolved":len(paired),"paired_hit_rate_excess":excess,
       "mom_hits_in_pairs":mo,"map_hits_in_pairs":mm,
       "average_pseudo_PnL_80bps_per_side":statistics.mean(nets) if nets else None,
       "paired_mean_pseudoPnL_excess_bps":statistics.mean(v for _,v in paired_diffs) if paired_diffs else None,
       "weekly_bootstrap_paired_excess_bps":ci,
       "monthly_blocks_positive_paired_excess":positive_months,
       "gates":gates,"scientific_status":scientific,
       "live_trading_verdict":"NO_GO"}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    days=[START+dt.timedelta(days=i) for i in range((END-START).days+1)]
    result={"study":"LIQMAP-DIAMANTE-003 actual historical daily positions",
       "start":str(START),"end":str(END),"selection":"ALL 105 calendar days, never cherry-pick",
       "historical_and_retrospective":True,"not_exact_HyperQuant":True,
       "per_row_asof_unverified":True,"not_Neuron":True,
       "no_trades":True,"no_paid_data":True,"sources":{},"events":[]}
    try:
        files,source=get_archive()
    except Exception as e:
        result["status"]="SOURCE_BLOCKED";result["error"]=str(e)
        (OUT/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
        raise
    result["sources"]["parquet_tree"]=source
    result["source_metadata_dates"]=len(files)
    begin=ms(dt.datetime.combine(START-dt.timedelta(days=2),dt.time(),dt.timezone.utc))
    end=ms(dt.datetime.combine(END+dt.timedelta(days=3),dt.time(),dt.timezone.utc))
    try:
        price_data,price_proof=hl_prices(begin,end)
        result["sources"]["hl_candles"]=price_proof
    except Exception as e:
        result["sources"]["hl_candle_blocker"]=str(e)
        price_data=None
    results=[]
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        futures={}
        for day in days:
            meta=files.get(str(day),[])
            if len(meta)!=1:
                results.append({"date":str(day),"status":"SOURCE_BLOCKED",
                        "error":"Expected 1 archive per date, found "+str(len(meta))})
                continue
            futures[pool.submit(fetch_day,day,meta[0])]=day
        for f in cf.as_completed(futures):
            day=futures[f]
            try:
                rr=f.result()
            except Exception as e:rr={"date":str(day),"status":"SOURCE_BLOCKED","error":str(e)[:300]}
            if rr.get("status")=="SOURCE_PASS":
                if price_data is None:
                    rr={"date":str(day),"status":"PRICE_SOURCE_BLOCKED","error":"Hyperliquid BTC candles missing"}
                else:
                    try:
                        observed=first_touch_record(rr,price_data)
                        rr={"date":str(day),"status":"EVENT_PASS","evidence":rr["receipt"],**observed}
                    except Exception as e:
                        rr={"date":str(day),"status":"ANALYSIS_BLOCKED","error":type(e).__name__+": "+str(e),
                            "source_file_sha256":rr["hf_file_lfs_sha256"]}
            results.append(rr)
            if len(results)%20==0:print("PROGRESS source_rows",len(results),"/",len(days),flush=True)
    results.sort(key=lambda x:x["date"])
    result["events"]=results
    result["gate"]=result_gate(results,days)
    result["status"]=result["gate"]["scientific_status"]
    (OUT/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    g=result["gate"]
    lines=["# LIQMAP003 - 105-day historical liquidation-price hypothesis test","",
      "**Retrospective only: not the original HyperQuant map, no source per-row timestamps, no live trades.**",
      "Data: claimed daily historical Hyperliquid BTC position snapshots on public HF, exact original file SHA256 and hourly price receipts.",
      "Hypothesis frozen before outcomes; always every date 2026-07-01..2026-10-13, missing days counted.","",
      "## Evidence and main economic findings","",
      "| Metric | Result |","|---|---:|",
      "| Calendar dates | "+str(g["calendar_days"])+" |",
      "| Valid source-and-price events | "+str(g["valid_source_and_outcome"])+" |",
      "| Resolved first touches | "+str(g["resolved"])+" |",
      "| Predicted target touched first | "+str(g["target_first"])+" |",
      "| Symmetric mirror touched first | "+str(g["mirror_first"])+" |",
      "| Hit rate among resolved | "+str(g["hit_rate"])+" |",
      "| Wilson lower 95% | "+str(g["wilson95"]["low"])+" |",
      "| Matched MOM24 hit excess | "+str(g["paired_hit_rate_excess"])+" |",
      "| Mean pseudo-PnL after 80bps each side | "+str(g["average_pseudo_PnL_80bps_per_side"])+" bps |",
      "| 7day block bootstrap CI | "+str(g["weekly_bootstrap_paired_excess_bps"])+" bps |",
      "| Scientific verdict | **"+g["scientific_status"]+"** |",
      "| REAL money verdict | **NO-GO** |","",
      "Sources that fail, wrong-side liq_px, no event, ambiguous first touch, costs, and gaps are never silently removed.",
      "This is NOT a confirmation of Neuron, CoinGlass or HyperQuant strategies, and cannot show real fill PnL or prospective edge.",
      "The filename epoch may be an as-of claim, but is not independent immutable proof the file existed at that time.",
      "Open the corresponding RESULT.json for all days, SHA-256, costs, controls and rejected source gates."]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("LIQMAP003_HISTORIC",g["scientific_status"],"valid",g["valid_source_and_outcome"],
          "resolved",g["resolved"],"wins",g["target_first"],"rate",g["hit_rate"],
          "net80bps",g["average_pseudo_PnL_80bps_per_side"],flush=True)

def get_archive():
    return archive_files()

if __name__=="__main__":main()
