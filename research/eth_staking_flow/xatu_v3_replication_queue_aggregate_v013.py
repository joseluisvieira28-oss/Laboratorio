#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "v012agg",
    HERE / "xatu_v3_replication_queue_aggregate_v012.py",
)
v012agg = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v012agg)


def main() -> int:
    rc = v012agg.main()
    p = Path("xatu_v3_replication_output") / "ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_1.json"
    if not p.exists():
        return 2
    x = json.loads(p.read_text(encoding="utf-8"))
    x["phase"] = "V3_INDEPENDENT_REPLICATION_SOURCE_AGGREGATE_V0_1_3_EMPTY_ROWGROUP_FALLBACK"
    lineage = x.setdefault("empty_rowgroup_fallback_v013_lineage", {})
    lineage.update({
        "original_run_id": 35387477455,
        "v012_recovery_run_id": 35438864217,
        "original_pass_shards_reused": 17,
        "recovered_shards": ["202502", "202503", "202510"],
        "exact_fallback_days": sorted(v012agg.EXPECTED_FALLBACK_DAYS),
        "v012_equivalence_qa_preserved": True,
        "scientific_rule_changed": False,
        "signal_evaluated": False,
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    })
    p.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": x.get("classification"),
        "observed": x.get("observed_date_count"),
        "series_sha256": x.get("daily_series_sha256"),
        "signal": False,
        "market": False,
        "returns": False,
        "pnl": False,
    }, sort_keys=True))
    return 0 if x.get("classification") == "SOURCE_REPLICATION_PASS" else (rc or 2)


if __name__ == "__main__":
    sys.exit(main())
