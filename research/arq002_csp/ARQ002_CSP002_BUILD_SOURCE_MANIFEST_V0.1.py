#!/usr/bin/env python3
"""Build canonical CSP-002 source manifest from outcome-blind prior-run receipts."""
from pathlib import Path
import json,hashlib,sys

STRICT=Path("strict_receipts")
MASK=Path("mask_receipts")
OUT=Path("ARQ002_CSP002_SOURCE_MANIFEST_V0.1.json")
MASKED={"2024-02-16","2024-10-28"}

def load_one(p):
    return json.loads(p.read_text())

def main():
    strict={}
    for p in STRICT.glob("arq002_source_2024-*.json"):
        r=load_one(p); strict[r["month"]]=r
    masks={}
    for p in MASK.glob("arq002_csp002_mask_2024-*.json"):
        r=load_one(p); masks[r["month"]]=r
    required={f"2024-{m:02d}" for m in range(1,13)}
    usable_strict=required-{"2024-02","2024-10"}
    if not usable_strict.issubset(strict):
        raise SystemExit(f"STRICT_MONTHS_MISSING:{sorted(usable_strict-set(strict))}")
    if set(masks)!={"2024-02","2024-10"}:
        raise SystemExit(f"MASK_MONTHS:{sorted(masks)}")

    days={}; months={}; warmup=None
    for ym in sorted(required):
        r=masks[ym] if ym in masks else strict[ym]
        if ym in masks:
            if r.get("classification")!="SOURCE_MASK_MONTH_PASS":
                raise SystemExit(f"MASK_MONTH_NOT_PASS:{ym}")
            months[ym]={"funding_sha256":r["funding"]["sha256"],"receipt_sha256":r["receipt_sha256"]}
            for d in r["days"]:
                days[d["date"]]={
                    "source_eligible":bool(d["source_eligible"]),
                    "agg_sha256":d["agg_sha256"],
                    "kline_sha256":d["kline_sha256"],
                    "metrics_sha256":d["metrics"]["sha256"],
                    "metrics_unique_slots":d["metrics"]["unique_slots"],
                }
        else:
            if r.get("classification")!="SOURCE_MONTH_PASS":
                raise SystemExit(f"STRICT_MONTH_NOT_PASS:{ym}")
            months[ym]={"funding_sha256":r["funding"]["sha256"],"receipt_sha256":r["receipt_sha256"]}
            for d in r["days"]:
                days[d["date"]]={
                    "source_eligible":True,
                    "agg_sha256":d["agg"]["sha256"],
                    "kline_sha256":d["kline"]["sha256"],
                    "metrics_sha256":d["metrics"]["sha256"],
                    "metrics_unique_slots":d["metrics"]["rows"],
                }
            if ym=="2024-01":
                w=r.get("warmup")
                if not w or not w.get("pass"):
                    raise SystemExit("WARMUP_MISSING")
                warmup={
                    "date":"2023-12-31",
                    "kline_sha256":w["kline"]["sha256"],
                    "metrics_sha256":w["metrics"]["sha256"],
                    "funding_month":"2023-12",
                    "funding_sha256":w["funding"]["sha256"],
                }

    if len(days)!=366: raise SystemExit(f"DAY_COUNT:{len(days)}")
    found_mask={d for d,v in days.items() if not v["source_eligible"]}
    if found_mask!=MASKED: raise SystemExit(f"MASK_MISMATCH:{sorted(found_mask)}")
    elig=sum(1 for v in days.values() if v["source_eligible"])
    if elig!=364: raise SystemExit(f"ELIGIBLE_COUNT:{elig}")

    out={
        "schema_version":"0.1","lab_id":"ARQ-002-CSP-002","date_utc":"2026-09-23",
        "source_mask_run":35900923026,
        "source_mask_receipt_sha256":"5d4bc118faf14234465dbcf124b895f16224f847c828651faa08f081c5602b18",
        "parent_strict_source_run":35899452900,
        "source_eligible_days":elig,"calendar_days":366,"coverage_fraction":elig/366,
        "masked_days":sorted(found_mask),"months":months,"warmup":warmup,
        "days":dict(sorted(days.items())),
        "economic_values_opened":False,"outcomes_opened":False,
        "protected_2025_accessed":False,"protected_2026_accessed":False,
    }
    out["manifest_sha256"]=hashlib.sha256(
        json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":"SOURCE_MANIFEST_PASS","days":len(days),"eligible":elig,
                      "masked_days":sorted(found_mask),"manifest_sha256":out["manifest_sha256"]},sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
