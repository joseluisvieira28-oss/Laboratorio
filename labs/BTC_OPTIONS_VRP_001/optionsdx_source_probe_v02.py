#!/usr/bin/env python3
"""Corrected source-only optionsDX public-sample schema probe V0.2."""
from __future__ import annotations
import csv,hashlib,io,json,pathlib,urllib.request

A=pathlib.Path("labs/BTC_OPTIONS_VRP_001/OPTIONSDX_SOURCE_PROBE_AUTHORITY_V0.2.json")
OUT=pathlib.Path("artifacts/btc_options_vrp_optionsdx_source_probe_v02")
OUT.mkdir(parents=True,exist_ok=True)

def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s):
    s=(s or "").strip()
    if s.startswith("[") and s.endswith("]"): s=s[1:-1]
    return s.strip().upper().replace(" ","_").replace("-","_")

def main():
    a=json.loads(A.read_text())
    assert a["status"]=="FROZEN_SOURCE_ONLY_PUBLIC_SAMPLE_NO_PURCHASE"
    assert all(v is False for k,v in a["safety"].items() if k.endswith("_authorized"))
    rec={"lab_id":a["lab_id"],"probe_id":a["probe_id"],"classification":None,"failure":None,
         "http":None,"bytes":None,"sha256":None,"row_count":0,"column_count":0,
         "columns_raw":[],"columns_normalized":[],"required_fields_present":{},
         "quote_timestamp_min":None,"quote_timestamp_max":None,"unique_instruments":0,
         "values_emitted":False,"outcomes_opened":False,"safety":a["safety"],"parent_v01_run":a["parent_v01_run"]}
    try:
        req=urllib.request.Request(a["provider"]["public_sample_url"],headers={"User-Agent":"SRC-Crypto-Lab/1.0"})
        with urllib.request.urlopen(req,timeout=90) as resp:
            raw=resp.read(); rec["http"]=int(resp.status)
        rec["bytes"]=len(raw); rec["sha256"]=sha(raw)
        text=raw.decode("utf-8-sig",errors="strict")
        rd=csv.DictReader(io.StringIO(text))
        rawcols=rd.fieldnames or []; normalized=[norm(c) for c in rawcols]
        rec["columns_raw"]=rawcols; rec["columns_normalized"]=normalized; rec["column_count"]=len(rawcols)
        mapping={norm(c):c for c in rawcols}
        rec["required_fields_present"]={f:(f in mapping) for f in a["required_fields"]}
        missing=[f for f,v in rec["required_fields_present"].items() if not v]
        qcol=mapping.get("QUOTE_UNIXTIME"); icol=mapping.get("INSTRUMENT_NAME")
        qts=[]; instruments=set(); rows=0
        for row in rd:
            rows+=1
            if icol and row.get(icol): instruments.add(row[icol].strip())
            if qcol and row.get(qcol):
                try: qts.append(int(float(row[qcol])))
                except ValueError: pass
        rec["row_count"]=rows; rec["unique_instruments"]=len(instruments)
        if qts:
            rec["quote_timestamp_min"]=min(qts); rec["quote_timestamp_max"]=max(qts)
        if rec["http"]!=200:
            rec["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        elif rows==0 or missing:
            rec["classification"]="SOURCE_ROUTE_SCHEMA_INSUFFICIENT"; rec["failure"]=f"missing={missing}, rows={rows}"
        else:
            rec["classification"]="OPTIONSDX_SAMPLE_SCHEMA_FEASIBLE"
    except Exception as e:
        rec["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; rec["failure"]=f"{type(e).__name__}: {e}"
    (OUT/"OPTIONSDX_SOURCE_PROBE_RECEIPT_V0.2.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":rec["classification"],"http":rec["http"],"bytes":rec["bytes"],
      "row_count":rec["row_count"],"column_count":rec["column_count"],"unique_instruments":rec["unique_instruments"],
      "required_fields_present":rec["required_fields_present"],"quote_timestamp_min":rec["quote_timestamp_min"],
      "quote_timestamp_max":rec["quote_timestamp_max"],"failure":rec["failure"],"outcomes_opened":False},sort_keys=True))
    return 0 if rec["classification"] in {"OPTIONSDX_SAMPLE_SCHEMA_FEASIBLE","SOURCE_ROUTE_SCHEMA_INSUFFICIENT"} else 2
if __name__=="__main__": raise SystemExit(main())
