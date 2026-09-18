#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import date,timedelta
from pathlib import Path

LAB_ID="ETH-STAKING-FLOW-001"; MVE_ID="ESF-NETQUEUE-XATU-7D-003"
START=date(2023,4,12); END=date(2024,12,31); EXPECTED=630

def daterange(a,b):
    out=[];d=a
    while d<=b: out.append(d.isoformat()); d+=timedelta(days=1)
    return out

def main():
    out=Path("xatu_v03b_coverage_output");out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_FULL_COVERAGE_V0_3B.json"
    try:
        files=sorted(Path("downloaded_v03b_shards").rglob("coverage_*.json"))
        if len(files)!=21: raise RuntimeError(f"expected 21 shard receipts, got {len(files)}")
        receipts=[json.loads(p.read_text(encoding="utf-8")) for p in files]
        if any(r.get("classification")!="SHARD_PASS" for r in receipts):
            classes={r.get("shard_id"):r.get("classification") for r in receipts if r.get("classification")!="SHARD_PASS"}
            if any(v=="PROVENANCE_FAILURE" for v in classes.values()): cls="PROVENANCE_FAILURE"
            elif any(v=="DATA_FAILURE" for v in classes.values()): cls="DATA_FAILURE"
            else: cls="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
            receipt={"classification":cls,"failure":f"non-pass shards: {classes}"}
        else:
            rows=[]
            for r in receipts: rows.extend(r.get("probes") or [])
            dates=[str(x["date"]) for x in rows]
            exp=daterange(START,END)
            dup=len(dates)-len(set(dates))
            missing=sorted(set(exp)-set(dates)); outside=sorted(set(dates)-set(exp))
            bad_http=[x["date"] for x in rows if x.get("http_status") not in (200,206)]
            bad_sig=[x["date"] for x in rows if x.get("prefix_ascii")!="PAR1"]
            if len(rows)!=EXPECTED or dup or missing or outside:
                cls="PROVENANCE_FAILURE"; fail=f"coverage identity mismatch rows={len(rows)} dup={dup} missing={len(missing)} outside={len(outside)}"
            elif bad_http:
                cls="DATA_FAILURE"; fail=f"bad http objects={len(bad_http)}"
            elif bad_sig:
                cls="PROVENANCE_FAILURE"; fail=f"bad parquet signatures={len(bad_sig)}"
            else:
                cls="XATU_FULL_COVERAGE_PASS"; fail=None
            receipt={"classification":cls,"failure":fail,"expected_date_count":EXPECTED,"observed_date_count":len(rows),
                     "duplicate_date_count":dup,"missing_dates":missing,"outside_dates":outside,
                     "bad_http_dates":bad_http,"bad_signature_dates":bad_sig,
                     "http_200_206_count":sum(1 for x in rows if x.get("http_status") in (200,206)),
                     "par1_count":sum(1 for x in rows if x.get("prefix_ascii")=="PAR1"),
                     "shard_count":len(receipts)}
        receipt.update({"lab_id":LAB_ID,"mve_id":MVE_ID,"phase":"XATU_FULL_COVERAGE_AGGREGATE_V0_3B",
                        "status_values_opened":False,"queue_counts_computed":False,"market_prices_opened":False,
                        "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
                        "live_trading":False,"exchange_mutation":False})
    except Exception as exc:
        receipt={"lab_id":LAB_ID,"mve_id":MVE_ID,"phase":"XATU_FULL_COVERAGE_AGGREGATE_V0_3B",
                 "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
                 "failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
                 "status_values_opened":False,"queue_counts_computed":False,"market_prices_opened":False,
                 "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"observed":receipt.get("observed_date_count"),
                      "http_pass":receipt.get("http_200_206_count"),"par1":receipt.get("par1_count"),
                      "missing":len(receipt.get("missing_dates") or []),"queue_counts":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if receipt["classification"]=="XATU_FULL_COVERAGE_PASS" else 2
if __name__=="__main__":sys.exit(main())
