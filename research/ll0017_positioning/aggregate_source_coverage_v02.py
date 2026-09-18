#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, sys
from collections import Counter
from pathlib import Path

LAB_ID="LL-0017-POSITIONING-RATIO-001"
EXPECTED_RANGES=[
 ("0","2021-01-01","2021-07-02",183),
 ("1","2021-07-03","2022-01-01",183),
 ("2","2022-01-02","2022-07-03",183),
 ("3","2022-07-04","2023-01-02",183),
 ("4","2023-01-03","2023-07-04",183),
 ("5","2023-07-05","2024-01-02",182),
 ("6","2024-01-03","2024-07-02",182),
 ("7","2024-07-03","2024-12-31",182),
]
EXPECTED_DAYS=1461
MIN_FULL_288=math.ceil(EXPECTED_DAYS*0.995)

def main()->int:
    out=Path("ll0017_coverage_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"LL0017_HISTORICAL_SOURCE_COVERAGE_RECEIPT_V0_2.json"
    files=sorted(Path("downloaded_coverage_shards").rglob("coverage_shard_*.json"))
    failure=None
    receipts=[]
    try:
        if len(files)!=8: raise RuntimeError(f"expected 8 shard receipts, found {len(files)}")
        receipts=[json.loads(p.read_text(encoding="utf-8")) for p in files]
        receipts.sort(key=lambda x:int(x["shard_id"]))
        got=[(str(x["shard_id"]),x["start_date"],x["end_date"],int(x["expected_day_count"])) for x in receipts]
        if got!=EXPECTED_RANGES: raise RuntimeError(f"shard ranges mismatch {got}")
        if any(x.get("lab_id")!=LAB_ID for x in receipts): raise RuntimeError("lab id mismatch")
    except Exception as exc:
        failure=f"{type(exc).__name__}: {str(exc)[:1200]}"

    all_days=[]; all_failures=[]; transport=Counter(); shard_classes={}
    digest=hashlib.sha256()
    if failure is None:
        for r in receipts:
            shard_classes[str(r["shard_id"])]=r.get("classification")
            all_days.extend(r.get("days") or [])
            all_failures.extend(r.get("failures") or [])
            for k,v in (r.get("transport_stats") or {}).items(): transport[k]+=int(v)
            for d in r.get("days") or []:
                digest.update(f"{d['date']}|{d['archive_sha256']}|{d['normalized_unique_timestamp_count']}|{d['exact_duplicate_rows_removed']}\n".encode())
        dates=[x["date"] for x in all_days]
        if len(dates)!=len(set(dates)): failure="duplicate calendar dates across shards"
        elif len(all_days)+len(all_failures)!=EXPECTED_DAYS: failure=f"adjudicated day count mismatch days={len(all_days)} failures={len(all_failures)}"
        elif any(x in d for d in dates for x in ("2025-","2026-")): failure="protected-period date admitted"

    full_288=sum(1 for x in all_days if int(x["normalized_unique_timestamp_count"])==288)
    min_unique=min((int(x["normalized_unique_timestamp_count"]) for x in all_days),default=0)
    total_unique=sum(int(x["normalized_unique_timestamp_count"]) for x in all_days)
    duplicate_rows_removed=sum(int(x["exact_duplicate_rows_removed"]) for x in all_days)

    if failure is not None:
        classification="PROVENANCE_FAILURE"
    elif all_failures:
        classes=[x.get("classification") for x in all_failures]
        precedence=["PROVENANCE_FAILURE","SOURCE_CHECKSUM_FAILURE","SOURCE_SCHEMA_INADEQUATE","SOURCE_TEMPORAL_COVERAGE_INADEQUATE","SOURCE_ACCESS_BLOCKED","SOURCE_ACQUISITION_TECHNICAL_FAILURE"]
        classification=next((x for x in precedence if x in classes),"SOURCE_ACQUISITION_TECHNICAL_FAILURE")
    elif any(x.get("classification")!="SHARD_PASS" for x in receipts):
        classification="PROVENANCE_FAILURE"
        failure="non-pass shard without day failure receipt"
    elif len(all_days)!=EXPECTED_DAYS:
        classification="SOURCE_TEMPORAL_COVERAGE_INADEQUATE"
        failure=f"resolved days {len(all_days)} != {EXPECTED_DAYS}"
    elif min_unique<280:
        classification="SOURCE_TEMPORAL_COVERAGE_INADEQUATE"
        failure=f"minimum unique timestamps/day {min_unique} < 280"
    elif full_288<MIN_FULL_288:
        classification="SOURCE_TEMPORAL_COVERAGE_INADEQUATE"
        failure=f"full 288-snapshot days {full_288} < {MIN_FULL_288}"
    else:
        classification="SOURCE_COVERAGE_PASS"

    receipt={
      "lab_id":LAB_ID,"phase":"HISTORICAL_SOURCE_COVERAGE_CANONICAL_V0_2_OUTCOME_BLIND",
      "classification":classification,"failure":failure,
      "frozen_start_date":"2021-01-01","frozen_end_date":"2024-12-31",
      "expected_day_count":EXPECTED_DAYS,"resolved_day_count":len(all_days),"failed_day_count":len(all_failures),
      "full_288_snapshot_day_count":full_288,"minimum_required_full_288_days":MIN_FULL_288,
      "minimum_unique_timestamps_any_day":min_unique,"total_normalized_unique_timestamps":total_unique,
      "exact_duplicate_rows_removed_total":duplicate_rows_removed,
      "shard_classifications":shard_classes,"failure_details":all_failures,
      "transport_stats":dict(transport),"coverage_structural_digest_sha256":digest.hexdigest(),
      "safety":{"ratio_numeric_values_parsed":False,"metric_values_exposed":False,"prices_opened":False,"returns_opened":False,"pnl_opened":False,"2025_accessed":False,"2026_accessed":False,"live_trading":False,"exchange_mutation":False}
    }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"resolved_days":len(all_days),"failed_days":len(all_failures),"full_288_days":full_288,"min_unique":min_unique,"total_unique":total_unique,"duplicate_rows_removed":duplicate_rows_removed,"failure":failure,"ratio_values_parsed":False},sort_keys=True))
    return 0 if classification=="SOURCE_COVERAGE_PASS" else 2
if __name__=="__main__": sys.exit(main())
