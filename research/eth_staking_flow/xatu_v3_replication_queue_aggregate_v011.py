#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("base_agg", HERE / "xatu_v3_replication_queue_aggregate_v01.py")
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)

RECOVERED = ["202502", "202503", "202510"]


def main() -> int:
    rc = base.main()
    p = Path("xatu_v3_replication_output") / "ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_1.json"
    if not p.exists():
        return 2
    x = json.loads(p.read_text(encoding="utf-8"))
    x["phase"] = "V3_INDEPENDENT_REPLICATION_SOURCE_AGGREGATE_V0_1_1_TRANSPORT_RECOVERY"
    x["transport_recovery_lineage"] = {
        "original_run_id": 35387477455,
        "original_pass_shards_reused": 17,
        "recovered_shards": RECOVERED,
        "original_failed_receipts_preserved": True,
        "base_aggregate_implementation_unchanged": True,
        "signal_evaluated": False,
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }
    p.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": x.get("classification"),
        "observed": x.get("observed_date_count"),
        "series_sha256": x.get("daily_series_sha256"),
        "recovered_shards": RECOVERED,
        "signal": False,
        "market": False,
        "returns": False,
        "pnl": False,
    }, sort_keys=True), flush=True)
    return 0 if x.get("classification") == "SOURCE_REPLICATION_PASS" else (rc or 2)


if __name__ == "__main__":
    sys.exit(main())
