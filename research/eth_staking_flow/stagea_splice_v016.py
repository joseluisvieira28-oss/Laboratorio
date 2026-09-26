#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import date, timedelta
from pathlib import Path

REC=Path("research/eth_staking_flow/ETH_STAKING_FLOW_001_BEACON_ARCHIVE_RECOVERY_V0_1_6.json")
LEG=Path("legacy_artifacts")
OUT=Path("artifacts/stagea_v016")
OUT.mkdir(parents=True,exist_ok=True)

recovery=json.loads(REC.read_text())
if recovery.get("classification")!="BEACON_ARCHIVE_RECOVERY_PASS":
    raise SystemExit("BEACON_ARCHIVE_RECOVERY_NOT_PASS")

legacy={}
files=sorted(LEG.rglob("queue_rep_*.json"))
if len(files)!=20:
    raise SystemExit(f"legacy shard file count {len(files)} != 20")

for p in files:
    x=json.loads(p.read_text())
    for r in x.get("daily_source_records",[]):
        d=str(r["date"])
        row={
          "date":d,
          "selected_epoch":int(r["selected_epoch"]),
          "selected_unix_time":int(r["selected_unix_time"]),
          "pending_queued_count":int(r["pending_queued_count"]),
          "active_exiting_count":int(r["active_exiting_count"]),
          "net_queue_count":int(r["net_queue_count"]),
          "source":"XATU_CANONICAL_PARQUET_ORIGINAL_V3"
        }
        if d in legacy and legacy[d]!=row:
            raise SystemExit(f"conflicting legacy duplicate {d}")
        legacy[d]=row

if len(legacy)!=601:
    raise SystemExit(f"legacy date count {len(legacy)} != 601")

recovered={}
for r in recovery.get("recovered_missing_dates",[]):
    d=str(r["date"])
    recovered[d]={
      "date":d,
      "selected_epoch":int(r["selected_epoch"]),
      "selected_unix_time":int(r["selected_unix_time"]),
      "pending_queued_count":int(r["pending_queued_count"]),
      "active_exiting_count":int(r["active_exiting_count"]),
      "net_queue_count":int(r["net_queue_count"]),
      "source":"BEACON_ARCHIVE_QUORUM_V0_1_6",
      "quorum_endpoints":sorted(r["quorum_endpoints"])
    }

expected_missing={"2025-02-25","2025-02-26","2025-02-27","2025-02-28","2025-03-01","2025-10-18","2025-10-19"}
if set(recovered)!=expected_missing:
    raise SystemExit(f"recovered missing date set mismatch: {sorted(recovered)}")
if set(recovered)&set(legacy):
    raise SystemExit("recovered date overlaps immutable legacy corpus")

allrows={**legacy,**recovered}

expected=[]
d=date(2025,1,1)
end=date(2026,8,31)
while d<=end:
    expected.append(d.isoformat())
    d+=timedelta(days=1)

errors=[]
if len(expected)!=608: errors.append("EXPECTED_DATE_GEOMETRY_NOT_608")
if len(allrows)!=608: errors.append(f"LEDGER_COUNT:{len(allrows)}")
missing=sorted(set(expected)-set(allrows))
outside=sorted(set(allrows)-set(expected))
if missing: errors.append("MISSING:"+",".join(missing))
if outside: errors.append("OUTSIDE:"+",".join(outside))

rows=[allrows[d] for d in expected if d in allrows]
for r in rows:
    if r["net_queue_count"]!=r["pending_queued_count"]-r["active_exiting_count"]:
        errors.append("NET_QUEUE_IDENTITY:"+r["date"])

canon=[{k:r[k] for k in ("date","selected_epoch","selected_unix_time","pending_queued_count","active_exiting_count","net_queue_count")} for r in rows]
sha=hashlib.sha256((json.dumps(canon,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()

receipt={
 "lab_id":"ETH-STAKING-FLOW-001",
 "stage":"V3_INDEPENDENT_REPLICATION_SOURCE_AGGREGATE_V0_1_6",
 "classification":"SOURCE_REPLICATION_PASS" if not errors else "SOURCE_PROVENANCE_FAILURE",
 "observed_date_count":len(rows),
 "expected_date_count":608,
 "legacy_date_count":len(legacy),
 "recovered_date_count":len(recovered),
 "missing_dates":missing,
 "outside_dates":outside,
 "daily_series_sha256":sha,
 "recovery_receipt_classification":recovery.get("classification"),
 "recovery_quorum_endpoint_names":sorted(set(e for r in recovery.get("recovered_missing_dates",[]) for e in r.get("quorum_endpoints",[]))),
 "errors":errors,
 "source_cutoff_2026":"2026-08-31",
 "signal_evaluated":False,
 "market_prices_opened":False,
 "returns_opened":False,
 "pnl_opened":False,
 "live_trading":False,
 "exchange_mutation":False
}

(OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_1_6.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
(OUT/"ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_1_6.json").write_text(json.dumps({"lab_id":receipt["lab_id"],"daily_series_sha256":sha,"records":rows},indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
raise SystemExit(0 if receipt["classification"]=="SOURCE_REPLICATION_PASS" else 2)
