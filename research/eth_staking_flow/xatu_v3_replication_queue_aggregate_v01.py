#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from datetime import date,timedelta
from pathlib import Path

LAB_ID="ETH-STAKING-FLOW-001"
MVE_ID="ESF-NETQUEUE-XATU-7D-003"
REPLICATION_ID="ESF-V3-REPLICATION-2025-2026A"
START=date(2025,1,1); END=date(2026,8,31); EXPECTED=608

def expected_dates():
    out=[]; d=START
    while d<=END:
        out.append(d.isoformat()); d+=timedelta(days=1)
    return out

def main():
    out=Path("xatu_v3_replication_output");out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_1.json"
    receipt={"lab_id":LAB_ID,"mve_id":MVE_ID,"replication_id":REPLICATION_ID,
             "phase":"V3_INDEPENDENT_REPLICATION_SOURCE_AGGREGATE_V0_1","classification":None,"failure":None}
    try:
        files=sorted(Path("downloaded_replication_shards").rglob("queue_rep_*.json"))
        if len(files)!=20: raise RuntimeError(f"expected 20 source shard receipts, got {len(files)}")
        shards=[json.loads(p.read_text(encoding="utf-8")) for p in files]
        bad={str(s.get("shard_id")):s.get("classification") for s in shards if s.get("classification")!="SHARD_PASS"}
        if bad:
            receipt["classification"]="SOURCE_REPLICATION_TECHNICAL_FAILURE"
            receipt["failure"]=f"non-pass shards: {bad}"
        else:
            rows=[]
            for s in shards: rows.extend(s.get("daily_source_records") or [])
            dates=[str(r["date"]) for r in rows]
            exp=expected_dates()
            dup=len(dates)-len(set(dates)); missing=sorted(set(exp)-set(dates)); outside=sorted(set(dates)-set(exp))
            badrows=[]
            for r in rows:
                p=r.get("pending_queued_count"); e=r.get("active_exiting_count"); n=r.get("net_queue_count")
                if not isinstance(p,int) or not isinstance(e,int) or p<0 or e<0 or n!=p-e:
                    badrows.append(r.get("date")); continue
                if int(r.get("validator_rows",-1))!=int(r.get("unique_validator_indices",-2)):
                    badrows.append(r.get("date"))
            if len(rows)!=EXPECTED or dup or missing or outside or badrows:
                receipt["classification"]="SOURCE_REPLICATION_PROVENANCE_FAILURE"
                receipt["failure"]=f"coverage/integrity rows={len(rows)} dup={dup} missing={len(missing)} outside={len(outside)} bad={len(badrows)}"
            else:
                rows.sort(key=lambda r:r["date"])
                h=hashlib.sha256()
                for r in rows:
                    h.update(f"{r['date']}|{r['selected_unix_time']}|{r['selected_epoch']}|{r['validator_rows']}|{r['pending_queued_count']}|{r['active_exiting_count']}|{r['net_queue_count']}\n".encode())
                receipt.update({
                    "classification":"SOURCE_REPLICATION_PASS",
                    "observed_date_count":len(rows),"expected_date_count":EXPECTED,
                    "duplicate_date_count":dup,"missing_dates":missing,"outside_dates":outside,
                    "daily_series_sha256":h.hexdigest(),
                    "first_date":rows[0]["date"],"last_date":rows[-1]["date"],
                    "daily_source_records":rows
                })
        receipt.update({
          "signal_evaluated":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
          "protected_2025_2026_source_opened_under_specific_v3_authority":True,
          "source_cutoff_2026":"2026-08-31","market_cutoff_2026":None,
          "live_trading":False,"exchange_mutation":False
        })
    except Exception as exc:
        receipt.update({"classification":"SOURCE_REPLICATION_TECHNICAL_FAILURE",
                        "failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
                        "signal_evaluated":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
                        "protected_2025_2026_source_opened_under_specific_v3_authority":True,
                        "live_trading":False,"exchange_mutation":False})
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"observed":receipt.get("observed_date_count"),
                      "missing":len(receipt.get("missing_dates") or []),"series_sha256":receipt.get("daily_series_sha256"),
                      "signal":False,"market":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if receipt["classification"]=="SOURCE_REPLICATION_PASS" else 2

if __name__=="__main__":sys.exit(main())
