#!/usr/bin/env python3
"""Source-only optionsDX public-sample schema probe for BTC Options VRP."""
from __future__ import annotations
import csv,hashlib,io,json,pathlib,urllib.request,urllib.error

A=pathlib.Path("labs/BTC_OPTIONS_VRP_001/OPTIONSDX_SOURCE_PROBE_AUTHORITY_V0.1.json")
OUT=pathlib.Path("artifacts/btc_options_vrp_optionsdx_source_probe_v01")
OUT.mkdir(parents=True,exist_ok=True)

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    a=json.loads(A.read_text())
    assert a["status"]=="FROZEN_SOURCE_ONLY_PUBLIC_SAMPLE_NO_PURCHASE"
    assert all(v is False for k,v in a["safety"].items() if k.endswith("_authorized"))
    rec={"lab_id":a["lab_id"],"probe_id":a["probe_id"],"classification":None,"failure":None,
         "http":None,"bytes":None,"sha256":None,"row_count":0,"column_count":0,
         "columns":[],"field_groups":{},"date_min":None,"date_max":None,
         "unique_instruments":None,"values_emitted":False,"outcomes_opened":False,"safety":a["safety"]}
    try:
        req=urllib.request.Request(a["provider"]["public_sample_url"],headers={"User-Agent":"SRC-Crypto-Lab/1.0"})
        with urllib.request.urlopen(req,timeout=60) as resp:
            raw=resp.read(); rec["http"]=int(resp.status)
        rec["bytes"]=len(raw); rec["sha256"]=sha(raw)
        text=raw.decode("utf-8-sig",errors="strict")
        rd=csv.DictReader(io.StringIO(text))
        cols=rd.fieldnames or []; rec["columns"]=cols; rec["column_count"]=len(cols)
        normalized={c.strip().upper().replace("-","_"):c for c in cols}
        groups={}
        for group,aliases in a["required_field_aliases"].items():
            found=None
            for alias in aliases:
                key=alias.strip().upper().replace("-","_")
                if key in normalized: found=normalized[key]; break
            groups[group]=found
        rec["field_groups"]=groups
        missing=[k for k,v in groups.items() if v is None]
        rows=0; instruments=set(); qts=[]
        for row in rd:
            rows+=1
            inst_col=groups.get("instrument"); qt_col=groups.get("quote_timestamp")
            if inst_col and row.get(inst_col): instruments.add(row[inst_col])
            if qt_col and row.get(qt_col):
                try: qts.append(int(float(row[qt_col])))
                except ValueError: pass
        rec["row_count"]=rows; rec["unique_instruments"]=len(instruments)
        if qts: rec["date_min"],rec["date_max"]=min(qts),max(qts)
        if rec["http"]!=200: rec["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        elif rows==0 or missing:
            rec["classification"]="SOURCE_ROUTE_SCHEMA_INSUFFICIENT"; rec["failure"]=f"missing={missing}, rows={rows}"
        else: rec["classification"]="OPTIONSDX_SAMPLE_SCHEMA_FEASIBLE"
    except Exception as e:
        rec["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; rec["failure"]=f"{type(e).__name__}: {e}"
    (OUT/"OPTIONSDX_SOURCE_PROBE_RECEIPT_V0.1.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:rec[k] for k in ["classification","http","bytes","row_count","column_count","unique_instruments","field_groups","failure","outcomes_opened"]},sort_keys=True))
    return 0 if rec["classification"] in {"OPTIONSDX_SAMPLE_SCHEMA_FEASIBLE","SOURCE_ROUTE_SCHEMA_INSUFFICIENT"} else 2
if __name__=="__main__": raise SystemExit(main())
