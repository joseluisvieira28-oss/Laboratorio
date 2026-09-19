#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "base_agg",
    HERE / "xatu_v3_replication_queue_aggregate_v01.py",
)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)

RECOVERED = ["202502", "202503", "202510"]
EXPECTED_FALLBACK_DAYS = {
    "2025-02-25",
    "2025-02-26",
    "2025-02-27",
    "2025-02-28",
    "2025-03-01",
    "2025-10-18",
    "2025-10-19",
}


def main() -> int:
    fallback_days: set[str] = set()
    shard_files = sorted(Path("downloaded_replication_shards").glob("queue_rep_*.json"))
    if len(shard_files) != 20:
        raise SystemExit(f"expected 20 assembled monthly receipts, got {len(shard_files)}")
    for p in shard_files:
        x = json.loads(p.read_text(encoding="utf-8"))
        if str(x.get("shard_id")) in RECOVERED:
            for row in x.get("daily_source_records") or []:
                if row.get("timestamp_locator") == "COLUMN_VALUE_FALLBACK_NO_ROWGROUP_STATS":
                    fallback_days.add(str(row["date"]))
    if fallback_days != EXPECTED_FALLBACK_DAYS:
        raise SystemExit(
            f"fallback-day identity mismatch got={sorted(fallback_days)} "
            f"expected={sorted(EXPECTED_FALLBACK_DAYS)}"
        )

    rc = base.main()
    p = Path("xatu_v3_replication_output") / "ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_1.json"
    if not p.exists():
        return 2
    x = json.loads(p.read_text(encoding="utf-8"))
    x["phase"] = "V3_INDEPENDENT_REPLICATION_SOURCE_AGGREGATE_V0_1_2_PARQUET_METADATA_FALLBACK"
    x["parquet_metadata_fallback_lineage"] = {
        "original_run_id": 35387477455,
        "original_pass_shards_reused": 17,
        "recovered_shards": RECOVERED,
        "exact_fallback_days": sorted(EXPECTED_FALLBACK_DAYS),
        "original_failed_receipts_preserved": True,
        "v011_failed_recovery_preserved": True,
        "base_aggregate_implementation_unchanged": True,
        "timestamp_selection_semantics_changed": False,
        "scientific_rule_changed": False,
        "signal_evaluated": False,
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }
    p.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "classification": x.get("classification"),
                "observed": x.get("observed_date_count"),
                "series_sha256": x.get("daily_series_sha256"),
                "fallback_days": sorted(EXPECTED_FALLBACK_DAYS),
                "signal": False,
                "market": False,
                "returns": False,
                "pnl": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if x.get("classification") == "SOURCE_REPLICATION_PASS" else (rc or 2)


if __name__ == "__main__":
    sys.exit(main())
