#!/usr/bin/env python3
"""Outcome-blind multi-venue BTC liquidation source probe.

No market prices, returns, event thresholds or strategy outcomes are opened.
"""
from __future__ import annotations
import csv,gzip,hashlib,io,json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
AUTH=ROOT/"MULTIVENUE_SOURCE_PROBE_AUTHORITY_V0.1.json"
OUT=Path("artifacts/liquidation_pressure_multivenue_source_probe_v01")
OUT.mkdir(parents=True,exist_ok=True)

def h(b): return hashlib.sha256(b).hexdigest()

def fetch(exchange,dataset_symbol,date):
    y,m,d=date.split("-")
    url=f"https://datasets.tardis.dev/v1/{exchange}/liquidations/{y}/{m}/{d}/{dataset_symbol}.csv.gz"
    try: r=requests.get(url,timeout=(20,120))
    except requests.RequestException as e:
        return {"date":date,"url":url,"http":None,"failure":f"REQUEST:{e}"}
    if r.status_code!=200:
        return {"date":date,"url":url,"http":r.status_code,"failure":f"HTTP_{r.status_code}"}
    try: raw=gzip.decompress(r.content).decode("utf-8")
    except Exception as e:
        return {"date":date,"url":url,"http":200,"failure":f"DECODE:{e}","compressed_sha256":h(r.content)}
    rd=csv.DictReader(io.StringIO(raw)); fields=rd.fieldnames or []
    rows=list(rd)
    return {"date":date,"url":url,"http":200,"failure":None,"compressed_sha256":h(r.content),
            "compressed_bytes":len(r.content),"schema":fields,"rows":rows}

def main():
    a=json.loads(AUTH.read_text())
    assert a["status"]=="FROZEN_SOURCE_ONLY_OUTCOME_BLIND"
    assert all(int(d[:4])<2025 for d in a["sample_dates"])
    assert all(v is False for k,v in a["safety"].items() if k.endswith("_authorized"))
    receipt={"lab_id":a["lab_id"],"probe_id":a["probe_id"],"venues":[],"safety":a["safety"],
             "selection_firewall":a["selection_firewall"],"classification":None}
    passed=0; non_binance_style_pass=0
    for v in a["venues"]:
        vr={"exchange":v["exchange"],"dataset_symbol":v["dataset_symbol"],"target_symbols":v["target_symbols"],
            "source_method":v["source_method"],"source_quality_note":v["source_quality_note"],"dates":[],"route_pass":True}
        targets=set(v["target_symbols"])
        for date in a["sample_dates"]:
            x=fetch(v["exchange"],v["dataset_symbol"],date)
            drec={k:x.get(k) for k in ("date","url","http","failure","compressed_sha256","compressed_bytes","schema")}
            if x.get("failure"):
                vr["route_pass"]=False; drec["target_rows"]=0; drec["target_symbols_present"]=[]
            else:
                missing=[c for c in a["required_columns"] if c not in (x.get("schema") or [])]
                counts={s:0 for s in targets}
                bad_required=0
                for row in x["rows"]:
                    s=(row.get("symbol") or "").upper()
                    if s in counts:
                        counts[s]+=1
                        if not (row.get("timestamp") and row.get("price") and row.get("amount")):
                            bad_required+=1
                drec["target_rows"]=sum(counts.values())
                drec["target_symbols_present"]=sorted([s for s,n in counts.items() if n])
                drec["target_symbol_counts"]=counts
                drec["missing_required_columns"]=missing
                drec["bad_required_rows"]=bad_required
                if missing or drec["target_rows"]==0 or bad_required:
                    vr["route_pass"]=False
            drec["outcomes_opened"]=False
            vr["dates"].append(drec)
        if vr["route_pass"]:
            passed+=1
            if "KNOWN_CENSORING" not in vr["source_quality_note"]:
                non_binance_style_pass+=1
        receipt["venues"].append(vr)
    receipt["venues_passing"]=passed
    receipt["non_binance_style_venues_passing"]=non_binance_style_pass
    receipt["classification"]="MULTIVENUE_HISTORICAL_SOURCE_ROUTE_FEASIBLE" if passed>=3 and non_binance_style_pass>=1 else "MULTIVENUE_SOURCE_ROUTE_INSUFFICIENT"
    raw=json.dumps(receipt,indent=2,sort_keys=True)+"\n"
    (OUT/"LIQUIDATION_PRESSURE_001_MULTIVENUE_SOURCE_PROBE_RECEIPT_V0_1.json").write_text(raw)
    print(json.dumps({
      "classification":receipt["classification"],"venues_passing":passed,
      "venue_summary":[{"exchange":v["exchange"],"route_pass":v["route_pass"],
                        "target_rows_by_date":[d.get("target_rows",0) for d in v["dates"]]} for v in receipt["venues"]],
      "outcomes_opened":False
    },sort_keys=True))
    return 0 if receipt["classification"]=="MULTIVENUE_HISTORICAL_SOURCE_ROUTE_FEASIBLE" else 2

if __name__=="__main__": raise SystemExit(main())
