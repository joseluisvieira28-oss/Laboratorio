#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from datetime import date,timedelta
from pathlib import Path

LAB_ID="ETH-STAKING-FLOW-001"
MVE_ID="ESF-NETQUEUE-XATU-7D-003"
START=date(2023,4,12); END=date(2024,12,31); EXPECTED=630

def expected_dates():
    out=[]; d=START
    while d<=END:
        out.append(d.isoformat()); d+=timedelta(days=1)
    return out

def main():
    out=Path("xatu_v03d_queue_output");out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_FULL_QUEUE_RECONSTRUCTION_V0_3D.json"
    receipt={"lab_id":LAB_ID,"mve_id":MVE_ID,"phase":"XATU_FULL_QUEUE_RECONSTRUCTION_AGGREGATE_V0_3D",
             "classification":None,"failure":None}
    try:
        files=sorted(Path("downloaded_v03d_shards").rglob("queue_*.json"))
        if len(files)!=21: raise RuntimeError(f"expected 21 queue shard receipts, got {len(files)}")
        shards=[json.loads(p.read_text(encoding="utf-8")) for p in files]
        bad={str(s.get("shard_id")):s.get("classification") for s in shards if s.get("classification")!="SHARD_PASS"}
        if bad:
            receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
            receipt["failure"]=f"non-pass shards: {bad}"
        else:
            rows=[]
            for s in shards:
                rows.extend(s.get("daily_source_records") or [])
            dates=[str(r["date"]) for r in rows]
            exp=expected_dates()
            dup=len(dates)-len(set(dates))
            missing=sorted(set(exp)-set(dates))
            outside=sorted(set(dates)-set(exp))
            invalid_counts=[]
            invalid_time=[]
            invalid_unique=[]
            for r in rows:
                p=r.get("pending_queued_count"); e=r.get("active_exiting_count"); n=r.get("net_queue_count")
                if not isinstance(p,int) or not isinstance(e,int) or p<0 or e<0 or n!=p-e:
                    invalid_counts.append(r.get("date"))
                if not r.get("selected_time_utc") or not r.get("selected_epoch") and r.get("selected_epoch")!=0:
                    invalid_time.append(r.get("date"))
                if int(r.get("validator_rows",-1))!=int(r.get("unique_validator_indices",-2)):
                    invalid_unique.append(r.get("date"))
            if len(rows)!=EXPECTED or dup or missing or outside:
                receipt["classification"]="PROVENANCE_FAILURE"
                receipt["failure"]=f"coverage mismatch rows={len(rows)} dup={dup} missing={len(missing)} outside={len(outside)}"
            elif invalid_counts or invalid_time or invalid_unique:
                receipt["classification"]="PROVENANCE_FAILURE"
                receipt["failure"]=f"daily integrity failure counts={len(invalid_counts)} time={len(invalid_time)} unique={len(invalid_unique)}"
            else:
                rows.sort(key=lambda r:r["date"])
                h=hashlib.sha256()
                for r in rows:
                    h.update(f"{r['date']}|{r['selected_unix_time']}|{r['selected_epoch']}|{r['validator_rows']}|{r['pending_queued_count']}|{r['active_exiting_count']}|{r['net_queue_count']}\n".encode())
                receipt.update({
                    "classification":"SOURCE_DATA_PASS",
                    "observed_date_count":len(rows),
                    "expected_date_count":EXPECTED,
                    "duplicate_date_count":dup,
                    "missing_dates":missing,
                    "outside_dates":outside,
                    "daily_series_sha256":h.hexdigest(),
                    "first_date":rows[0]["date"],
                    "last_date":rows[-1]["date"],
                    "min_pending_queued_count":min(r["pending_queued_count"] for r in rows),
                    "max_pending_queued_count":max(r["pending_queued_count"] for r in rows),
                    "min_active_exiting_count":min(r["active_exiting_count"] for r in rows),
                    "max_active_exiting_count":max(r["active_exiting_count"] for r in rows),
                    "daily_source_records":rows
                })
        receipt.update({
            "validator_level_rows_persisted":False,
            "signal_evaluated":False,
            "event_count_computed":False,
            "market_prices_opened":False,
            "returns_opened":False,
            "pnl_opened":False,
            "accessed_2025_or_2026":False,
            "live_trading":False,
            "exchange_mutation":False
        })
    except Exception as exc:
        receipt.update({
            "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
            "failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
            "validator_level_rows_persisted":False,
            "signal_evaluated":False,
            "event_count_computed":False,
            "market_prices_opened":False,
            "returns_opened":False,
            "pnl_opened":False,
            "accessed_2025_or_2026":False
        })
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "classification":receipt["classification"],
        "observed":receipt.get("observed_date_count"),
        "missing":len(receipt.get("missing_dates") or []),
        "series_sha256":receipt.get("daily_series_sha256"),
        "signal":False,"events":False,"prices":False,"returns":False,"pnl":False
    },sort_keys=True))
    return 0 if receipt["classification"]=="SOURCE_DATA_PASS" else 2

if __name__=="__main__":sys.exit(main())
