#!/usr/bin/env python3
"""Independent offline source/market direction reproduction of archived 2025 historical results."""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import zipfile
from collections import defaultdict
from datetime import timezone
ROOT=pathlib.Path("downloaded")
OUT=pathlib.Path("artifacts/btc10m_original_zip_independent_audit_v01")
MS=60000
MONTHS=["2025-%02d"%m for m in (1,3,5,7,9,11)]
RULES={"FLOW55":(.55,.45),"FLOW60":(.60,.40)}
def h(x):return hashlib.sha256(x).hexdigest()
def reject(what):raise ValueError(what)
def data(market,month,manifest):
    a=f"{market}_{month}.zip"
    b=(ROOT/"official_zip"/a).read_bytes()
    official=(ROOT/"official_zip"/(a+".CHECKSUM")).read_bytes()
    checksum=official.decode("ascii").strip().split()[0].lower()
    if h(b)!=checksum or h(b)!=manifest[(market,month)]["archive_zip_sha256"]:
        reject("ZIP_OFFICIAL_CHECKSUM_MISMATCH_"+a)
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        fs=[f for f in z.namelist() if f.endswith(".csv") and "/" not in f]
        if len(fs)!=1:reject("ZIP_CSV_SCHEMA_"+a)
        candles={}
        f=io.TextIOWrapper(z.open(fs[0]),encoding="utf-8-sig",newline="")
        for row in csv.reader(f):
            if not row or not row[0].isdigit():continue
            raw_t=int(row[0])
            t=raw_t//1000 if raw_t>10**14 else raw_t
            op=float(row[1]);tq=float(row[7]);buy=float(row[10])
            if t in candles:reject("DUPLICATE_MINUTE_"+a)
            candles[t]=(op,tq,buy)
        if not candles:reject("ZERO_CANDLES_"+a)
    return candles
def select(spot_buy,fut_buy,cut):
    hi,lo=cut
    if spot_buy>=hi and fut_buy<=lo:return "UP"
    if spot_buy<=lo and fut_buy>=hi:return "DOWN"
    return None
def audit():
    original=json.loads((ROOT/"receipt.json").read_text())
    if original["status"]!="HISTORICAL_SOURCE_AND_EXECUTION_COMPLETE":
        reject("ORIGINAL_NOT_COMPLETE")
    manifest={(x["venue"],x["month"]):x for x in original["archive_manifest"]}
    if len(manifest)!=24:reject("ORIGINAL_NOT_24_MANIFEST_ZIPS")
    new={name:{} for name in RULES}
    valid=0;rows_read=0
    for month in MONTHS:
        spot=data("spot",month,manifest)
        fut=data("um",month,manifest)
        first=min(spot)
        start=dt.datetime.strptime(month+"-01","%Y-%m-%d").replace(tzinfo=timezone.utc)
        lo=int(start.timestamp()*1000)
        if start.month==12:nextstart=dt.datetime(2026,1,1,tzinfo=timezone.utc)
        else:nextstart=dt.datetime(start.year,start.month+1,1,tzinfo=timezone.utc)
        stop=int(nextstart.timestamp()*1000)
        for t in range(lo+10*MS,stop-10*MS+1,10*MS):
            previous=[t-k*MS for k in (3,2,1)]
            if any(x not in spot or x not in fut for x in previous):
                continue
            if t not in spot or t+10*MS not in spot:continue
            vs=sum(spot[x][1] for x in previous)
            vp=sum(fut[x][1] for x in previous)
            if vs<=0 or vp<=0:continue
            buy_spot=sum(spot[x][2] for x in previous)/vs
            buy_perp=sum(fut[x][2] for x in previous)/vp
            p0=spot[t][0];p10=spot[t+10*MS][0]
            label="UP" if p10>p0 else "DOWN" if p10<p0 else "TIE"
            valid+=1
            for name,cut in RULES.items():
                side=select(buy_spot,buy_perp,cut)
                if side:
                    if t in new[name]:reject("SIGNAL_ID_DUPLICATED")
                    new[name][t]=(month,side,label,p0,p10,buy_spot,buy_perp)
        print("AUDIT_MONTH",month,"SPOT_ROWS",len(spot),"PERP_ROWS",len(fut),flush=True)
    result={"study":"BTC10M_2025_INDEPENDENT_ORIGINAL_ZIP_AUDIT_V01",
            "original_artifact_id":13054236463,"months":MONTHS,
            "original_2025_proxy_only":True,"fresh_market_api_calls":0,
            "market_inputs_from_original_archives":12,"2025_evaluable_slots":valid,
            "source_and_label_reproduction":{},"economic_edge_certified":False}
    for name in RULES:
        path=ROOT/f"2025_{name.lower()}_signal_events.jsonl"
        stored={}
        for line in path.read_text().splitlines():
            row=json.loads(line);i=int(row["time_ms"])
            if i in stored:reject("REPORTED_SIGNAL_DUPLICATED")
            stored[i]=row
        if set(stored)!=set(new[name]):
            reject(f"ORIGINAL_NEW_SIGNAL_ID_SETS_DIFFER_{name}_{len(stored)}_{len(new[name])}")
        for t,rec in new[name].items():
            mon,side,truth,p0,p10,bs,bp=rec
            row=stored[t]
            if row["side"]!=side or row["truth"]!=truth or row["month"]!=mon:
                reject("SIGNAL_DIRECTION_OR_OUTCOME_WRONG_"+name)
            if abs(row["price_t"]-p0)>1e-9 or abs(row["price_t_10m"]-p10)>1e-9:
                reject("TARGET_PRICE_MISMATCH_"+name)
            if abs(float(row["spot_aggressive_buy_share"])-bs)>1e-7 or abs(float(row["perp_aggressive_buy_share"])-bp)>1e-7:
                reject("FLOW_SHARE_MISMATCH_"+name)
        all_events=list(new[name].values())
        n=len(all_events)
        wins=sum(x[1]==x[2] for x in all_events)
        ties=sum(x[2]=="TIE" for x in all_events)
        losses=n-wins-ties
        q70=(wins*.7-losses)/n if n else None
        q80=(wins*.8-losses)/n if n else None
        expected=original["year_economic_and_science_metrics"]["years"]["2025"][name]
        for key,v in {"signals":n,"wins":wins,"losses":losses,"ties":ties}.items():
            if expected[key]!=v:reject("RECEIPT_COUNT_DIFFERS_"+name+"_"+key)
        if abs(expected["synthetic_payoff_per_stake_q_0p7"]-q70)>1e-10 or abs(expected["synthetic_payoff_per_stake_q_0p8"]-q80)>1e-10:
            reject("RECEIPT_PAYOUT_MATH_DIFFERENT_"+name)
        result["source_and_label_reproduction"][name]={"event_set_exact":True,"source_buy_ratios_exact":True,
            "direction_and_future_spot_open_price_exact":True,"signals":n,"wins":wins,"losses":losses,"ties":ties,
            "independent_accuracy":wins/(n-ties) if n>ties else None,
            "independent_q0p70_unit_payoff":q70,"independent_q0p80_unit_payoff":q80}
    result["status"]="INDEPENDENT_ORIGINAL_SOURCE_REPLAY_PASS"
    return result
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as ex:
        r={"study":"BTC10M_2025_INDEPENDENT_ORIGINAL_ZIP_AUDIT_V01",
           "status":"INDEPENDENT_AUDIT_FAIL","reason":type(ex).__name__+":"+str(ex)[:320],
           "fresh_market_api_calls":0}
    (OUT/"audit_receipt.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("FINAL_AUDIT",json.dumps(r,sort_keys=True),flush=True)
    if r["status"]!="INDEPENDENT_ORIGINAL_SOURCE_REPLAY_PASS":
        raise SystemExit(2)
if __name__=="__main__":main()
