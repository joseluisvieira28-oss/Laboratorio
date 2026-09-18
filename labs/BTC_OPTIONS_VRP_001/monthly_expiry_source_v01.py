#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
AUTH_PATH=ROOT/"MONTHLY_EXPIRY_SOURCE_AUTHORITY_V0.1.json"
OUT=Path("artifacts/btc_options_vrp_monthly_expiry_source_v01")
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
import tardis_source_probe_v01 as base

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def expiry_dates_from_delivery(auth):
    url=auth["source"]["delivery_prices_url"]
    params={"index_name":auth["source"]["delivery_index_name"],"count":1000,"offset":0}
    r=requests.get(url,params=params,timeout=(20,60),headers={"User-Agent":"Crypto-Lab-VRP-monthly-source/0.1"})
    raw=r.content; digest=hashlib.sha256(raw).hexdigest()
    if r.status_code!=200:
        raise RuntimeError(f"delivery HTTP {r.status_code} sha256={digest}")
    obj=r.json()
    result=(obj or {}).get("result")
    if isinstance(result,dict):
        rows=result.get("data") or result.get("records") or []
    elif isinstance(result,list):
        rows=result
    else:
        rows=[]
    dates=set()
    for x in rows:
        if not isinstance(x,dict): continue
        v=x.get("date")
        if isinstance(v,(int,float)):
            dates.add(datetime.fromtimestamp(int(v)/1000,tz=timezone.utc).date().isoformat())
        elif isinstance(v,str):
            try:
                if v.isdigit():
                    dates.add(datetime.fromtimestamp(int(v)/1000,tz=timezone.utc).date().isoformat())
                else:
                    dates.add(datetime.fromisoformat(v.replace("Z","+00:00")).date().isoformat())
            except Exception:
                pass
    return dates,{"url":r.url,"http_status":r.status_code,"sha256":digest,"rows_seen":len(rows),"distinct_dates":len(dates)}

def run_year(auth,year):
    samples=[x for x in auth["sample_dates"] if int(x[:4])==year]
    delivery_dates,delivery_receipt=expiry_dates_from_delivery(auth)
    out={"year":year,"classification":"YEAR_SOURCE_COMPLETE","sample_dates":len(samples),"complete":[],"incomplete":[],"delivery_receipt":delivery_receipt}
    for sample in samples:
        try:
            chain=base.probe_chain(auth,sample)
            quotes=base.probe_quotes(auth,sample,chain["selected_pair"])
            exp=chain["selected_pair"]["expiry"]
            delivery_ok=exp in delivery_dates
            rec={
                "date":sample,
                "expiry":exp,
                "dte":chain["selected_pair"]["dte"],
                "call":chain["selected_pair"]["call"],
                "put":chain["selected_pair"]["put"],
                "chain_rows_scanned":chain["rows_scanned"],
                "quote_rows_scanned":quotes["rows_scanned"],
                "chain_bbo_both":True,
                "quote_bbo_both":len(quotes["targets_with_nonempty_bbo"])==2,
                "delivery_date_present":delivery_ok
            }
            if rec["quote_bbo_both"] and delivery_ok:
                out["complete"].append(rec)
            else:
                out["incomplete"].append({**rec,"reason":"DELIVERY_DATE_MISSING" if not delivery_ok else "QUOTE_BBO_MISSING"})
        except base.RouteInsufficient as e:
            out["incomplete"].append({"date":sample,"reason":"TARDIS_ROUTE_INSUFFICIENT","detail":str(e)[:500]})
        except base.AcquisitionFailure as e:
            out["classification"]="YEAR_SOURCE_TECHNICAL_FAILURE"
            out["incomplete"].append({"date":sample,"reason":"TARDIS_ACQUISITION_FAILURE","detail":str(e)[:500]})
            break
    out["complete_count"]=len(out["complete"])
    out["incomplete_count"]=len(out["incomplete"])
    out["receipt_sha256"]=h({k:v for k,v in out.items() if k!="receipt_sha256"})
    p=OUT/f"monthly_expiry_source_{year}.json"
    p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"year":year,"classification":out["classification"],"complete":out["complete_count"],"incomplete":out["incomplete_count"],"receipt_sha256":out["receipt_sha256"]},sort_keys=True))
    return 2 if out["classification"]=="YEAR_SOURCE_TECHNICAL_FAILURE" else 0

def aggregate(auth,input_dir):
    rows=[]
    for y in (2021,2022,2023,2024):
        matches=list(Path(input_dir).rglob(f"monthly_expiry_source_{y}.json"))
        if len(matches)!=1: raise RuntimeError(f"expected one receipt for {y}, got {len(matches)}")
        rows.append(json.loads(matches[0].read_text()))
    tech=any(x["classification"]=="YEAR_SOURCE_TECHNICAL_FAILURE" for x in rows)
    by={str(x["year"]):x["complete_count"] for x in rows}
    total=sum(by.values()); years=sum(1 for v in by.values() if v>0)
    gates=auth["source_gates"]
    checks={
      "total_ge_min":total>=gates["minimum_complete_months_total"],
      "years_ge_min":years>=gates["minimum_distinct_years"],
      "per_year_ge_min":all(by[str(y)]>=gates["minimum_complete_months_by_year"][str(y)] for y in (2021,2022,2023,2024))
    }
    if tech: cls=auth["classifications"]["technical_failure"]
    elif all(checks.values()): cls=auth["classifications"]["pass"]
    else: cls=auth["classifications"]["insufficient"]
    result={
      "lab_id":auth["lab_id"],"source_gate_id":auth["source_gate_id"],"classification":cls,
      "complete_months_total":total,"complete_months_by_year":by,"distinct_years":years,
      "gate_checks":checks,"year_receipt_sha256":{str(x["year"]):x["receipt_sha256"] for x in rows},
      "safety":{"performance_outcomes_opened":False,"strategy_pnl_opened":False,"returns_opened":False,
                "delivery_price_values_retained":False,"paid_subscription_used":False,"api_key_used":False,
                "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
    }
    result["receipt_sha256"]=h({k:v for k,v in result.items() if k!="receipt_sha256"})
    p=OUT/"MONTHLY_EXPIRY_SOURCE_AGGREGATE_V0.1.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 2 if cls in (auth["classifications"]["technical_failure"],auth["classifications"]["provenance_failure"]) else 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--year",type=int);ap.add_argument("--aggregate-dir")
    args=ap.parse_args();auth=json.loads(AUTH_PATH.read_text())
    assert auth["status"]=="FROZEN_SOURCE_ONLY_OUTCOME_BLIND"
    assert len(auth["sample_dates"])==45
    assert all(int(x[:4])<2025 for x in auth["sample_dates"])
    assert all(v is False for k,v in auth["safety"].items() if k.endswith("_authorized"))
    if args.year:return run_year(auth,args.year)
    if args.aggregate_dir:return aggregate(auth,args.aggregate_dir)
    raise SystemExit("need --year or --aggregate-dir")
if __name__=="__main__":raise SystemExit(main())
