#!/usr/bin/env python3
"""V0.2 read-only source receipt audit: NEW local-arrival-boundary semantics.

Reads V0.1 immutable *metadata receipts* only, not raw 7.9M source rows.
NO economic labels, outcomes, private exchanges, or original gate changes.
"""
import json
from pathlib import Path
BASE=Path("research/mexc_event_direction_v01/joint_v01")
START=1775001600000000
END=START+86400*1000000
MAX_LAG_US=5000000
def verify():
    j=json.loads((BASE/"joint_source_validation.json").read_text())
    records=j.get("files",[])
    assert len(records)==6,"missing immutable six source receipts"
    assert j.get("verdict")=="SOURCE_INCOMPLETE", "parent verdict mutated"
    reports={}
    for sym in ("BTCUSDT","ETHUSDT"):
        defect=json.loads((BASE/f"joint_book_defects_{sym}.json").read_text())
        rows=defect["badrows"]
        if len(rows)!=6 or defect["counts"].get("exchange_time_outside_day")!=6:
            raise AssertionError("source defect evidence changed")
        if any(n for k,n in defect["counts"].items() if k!="exchange_time_outside_day"):
            raise AssertionError("non-boundary book geometry defect")
        for row in rows:
            ex=int(row["timestamp"]);local=int(row["local_timestamp"])
            if not START<=local<END or not 0<=local-ex<=MAX_LAG_US:
                raise AssertionError("collector boundary invalid")
        reports[sym]={
            "boundary_cases":len(rows),
            "min_exchange_ts_us":min(int(x["timestamp"]) for x in rows),
            "max_local_ts_us":max(int(x["local_timestamp"]) for x in rows),
            "max_boundary_lag_us":max(int(x["local_timestamp"])-int(x["timestamp"]) for x in rows),
            "defects_preserved":True
        }
    for x in records:
        if not x.get("publisher_md5_match") or x.get("invalid_rows") not in (0,6):
            raise AssertionError("original content source fails provenance")
        if x.get("local_regressions")!=0 or x.get("negative_lag_rows")!=0:
            raise AssertionError("invalid original monotonicity")
        if x["kind"] in ("trades","book_snapshot_5") and x["active_local_minutes"]!=1440:
            raise AssertionError("previous source coverage not demonstrated")
    return {
        "gate":"METADATA_BOUNDARY_RECONCILED_V02",
        "original_v01_gate":"SOURCE_INCOMPLETE_UNCHANGED",
        "historical_records_original":sum(int(v["rows"]) for v in records),
        "revalidated_raw_bytes_in_this_run":0,
        "cases":reports,
        "liquidation_no_event_intervals":"UNKNOWN",
        "liquidation_continuity":"NOT_ESTABLISHED",
        "can_open_outcomes":False,
        "no_model_or_edge_claim":True
    }
if __name__=="__main__":
    value=verify()
    p=Path("artifacts/triple_flow_v02");p.mkdir(parents=True,exist_ok=True)
    (p/"boundary_receipt.json").write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
    print(json.dumps(value,indent=2,sort_keys=True))
