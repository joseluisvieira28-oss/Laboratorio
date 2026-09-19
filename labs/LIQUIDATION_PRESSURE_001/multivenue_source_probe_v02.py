#!/usr/bin/env python3
"""Corrected outcome-blind multi-venue liquidation source probe V0.2."""
from __future__ import annotations
import csv,gzip,hashlib,io,json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
AUTH=ROOT/"MULTIVENUE_SOURCE_PROBE_AUTHORITY_V0.2.json"
OUT=Path("artifacts/liquidation_pressure_multivenue_source_probe_v02")
OUT.mkdir(parents=True,exist_ok=True)

def h(b): return hashlib.sha256(b).hexdigest()

def fetch(exchange,dataset_symbol,date):
    y,m,d=date.split("-")
    url=f"https://datasets.tardis.dev/v1/{exchange}/liquidations/{y}/{m}/{d}/{dataset_symbol}.csv.gz"
    try: r=requests.get(url,timeout=(20,120))
    except requests.RequestException as e:
        return {"date":date,"url":url,"http":None,"transport_failure":f"REQUEST:{e}"}
    if r.status_code!=200:
        return {"date":date,"url":url,"http":r.status_code,"transport_failure":f"HTTP_{r.status_code}"}
    try: raw=gzip.decompress(r.content).decode("utf-8")
    except Exception as e:
        return {"date":date,"url":url,"http":200,"transport_failure":f"DECODE:{e}","compressed_sha256":h(r.content)}
    if raw=="":
        return {"date":date,"url":url,"http":200,"transport_failure":None,"compressed_sha256":h(r.content),
                "compressed_bytes":len(r.content),"empty_file":True,"schema":[],"rows":[]}
    rd=csv.DictReader(io.StringIO(raw)); fields=rd.fieldnames or []
    rows=list(rd)
    return {"date":date,"url":url,"http":200,"transport_failure":None,"compressed_sha256":h(r.content),
            "compressed_bytes":len(r.content),"empty_file":False,"schema":fields,"rows":rows}

def main():
    a=json.loads(AUTH.read_text())
    assert a["status"]=="FROZEN_SOURCE_ONLY_OUTCOME_BLIND"
    assert a["venue_pass_rule"]["zero_event_dates_allowed"] is True
    assert all(int(d[:4])<2025 for d in a["sample_dates"])
    assert all(v is False for k,v in a["safety"].items() if k.endswith("_authorized"))
    rec={"lab_id":a["lab_id"],"probe_id":a["probe_id"],"venues":[],"classification":None,
         "safety":a["safety"],"selection_firewall":a["selection_firewall"],"parent_v01_run":a["parent_v01_run"]}
    passed=0; noncensored=0
    for v in a["venues"]:
        vr={"exchange":v["exchange"],"dataset_symbol":v["dataset_symbol"],"target_symbols":v["target_symbols"],
            "source_method":v["source_method"],"source_quality_note":v["source_quality_note"],"dates":[],"route_pass":True}
        targets=set(v["target_symbols"]); observed_dates=0
        for date in a["sample_dates"]:
            x=fetch(v["exchange"],v["dataset_symbol"],date)
            drec={k:x.get(k) for k in ("date","url","http","transport_failure","compressed_sha256","compressed_bytes","empty_file","schema")}
            drec["target_rows"]=0; drec["target_symbols_present"]=[]; drec["missing_required_columns"]=[]
            if x.get("transport_failure"):
                vr["route_pass"]=False
            elif not x.get("empty_file"):
                missing=[c for c in a["required_columns"] if c not in (x.get("schema") or [])]
                drec["missing_required_columns"]=missing
                if missing:
                    vr["route_pass"]=False
                else:
                    counts={s:0 for s in targets}; bad=0
                    for row in x.get("rows",[]):
                        s=(row.get("symbol") or "").upper()
                        if s in counts:
                            counts[s]+=1
                            if not (row.get("timestamp") and row.get("price") and row.get("amount")): bad+=1
                    drec["target_symbol_counts"]=counts
                    drec["target_rows"]=sum(counts.values())
                    drec["target_symbols_present"]=sorted([s for s,n in counts.items() if n])
                    drec["bad_required_rows"]=bad
                    if bad: vr["route_pass"]=False
                    if drec["target_rows"]>0: observed_dates+=1
            drec["outcomes_opened"]=False
            vr["dates"].append(drec)
        vr["target_nonempty_dates"]=observed_dates
        if observed_dates<a["venue_pass_rule"]["target_symbol_nonempty_on_at_least_n_dates"]:
            vr["route_pass"]=False
        if vr["route_pass"]:
            passed+=1
            if "KNOWN_CENSORING" not in vr["source_quality_note"]: noncensored+=1
        rec["venues"].append(vr)
    rec["venues_passing"]=passed; rec["non_binance_style_venues_passing"]=noncensored
    rec["classification"]="MULTIVENUE_HISTORICAL_SOURCE_ROUTE_FEASIBLE" if passed>=a["overall_pass_rule"]["venues_passing_gte"] and noncensored>=a["overall_pass_rule"]["venues_without_known_binance_one_per_second_censoring_passing_gte"] else "MULTIVENUE_SOURCE_ROUTE_INSUFFICIENT"
    payload=json.dumps(rec,indent=2,sort_keys=True)+"\n"
    (OUT/"LIQUIDATION_PRESSURE_001_MULTIVENUE_SOURCE_PROBE_RECEIPT_V0_2.json").write_text(payload)
    print(json.dumps({"classification":rec["classification"],"venues_passing":passed,
      "venue_summary":[{"exchange":v["exchange"],"route_pass":v["route_pass"],"target_nonempty_dates":v["target_nonempty_dates"]} for v in rec["venues"]],
      "outcomes_opened":False},sort_keys=True))
    return 0 if rec["classification"]=="MULTIVENUE_HISTORICAL_SOURCE_ROUTE_FEASIBLE" else 2

if __name__=="__main__": raise SystemExit(main())
