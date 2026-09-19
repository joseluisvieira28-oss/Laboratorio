#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pyarrow.compute as pc

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "v012",
    HERE / "xatu_v3_replication_queue_shard_v012.py",
)
v012 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v012)

EMPTY_ROWGROUPS_SKIPPED = 0
NONEMPTY_ROWGROUPS_USED = 0


def _actual_timestamp_ranges_v013(pf):
    global EMPTY_ROWGROUPS_SKIPPED, NONEMPTY_ROWGROUPS_USED
    out = []
    for i in range(pf.metadata.num_row_groups):
        tab = pf.read_row_group(i, columns=["epoch_start_date_time"])
        arr = tab["epoch_start_date_time"]
        if len(arr) == 0:
            EMPTY_ROWGROUPS_SKIPPED += 1
            continue
        if arr.null_count:
            raise RuntimeError(f"row group {i}: null epoch_start_date_time in non-empty row group")
        mn = pc.min(arr).as_py()
        mx = pc.max(arr).as_py()
        if mn is None or mx is None:
            raise RuntimeError(f"row group {i}: timestamp extrema unavailable in non-empty row group")
        out.append((i, v012.base.stat_int(mn), v012.base.stat_int(mx)))
        NONEMPTY_ROWGROUPS_USED += 1
    if not out:
        raise RuntimeError("no non-empty row groups available for column-value fallback")
    return out


def main() -> int:
    if v012.os.environ["SHARD_ID"] not in v012.ALLOWED_SHARDS:
        raise SystemExit("recovery shard outside frozen allowlist")

    v012._actual_timestamp_ranges = _actual_timestamp_ranges_v013
    rc = v012.main()

    sid = v012.os.environ["SHARD_ID"]
    p = Path("xatu_v3_replication_shards") / f"queue_rep_{sid}.json"
    if not p.exists():
        return 2
    x = json.loads(p.read_text(encoding="utf-8"))
    x["phase"] = "V3_INDEPENDENT_REPLICATION_SOURCE_SHARD_V0_1_3_EMPTY_ROWGROUP_FALLBACK"
    x["empty_rowgroup_fallback_v013"] = {
        "empty_rowgroups_skipped": EMPTY_ROWGROUPS_SKIPPED,
        "nonempty_rowgroups_used_for_timestamp_ranges": NONEMPTY_ROWGROUPS_USED,
        "skip_scope": "ZERO_ROW_OR_ZERO_NON_NULL_TIMESTAMP_ROWGROUP_ONLY",
        "nonempty_null_timestamp_rowgroups_fail_closed": True,
        "same_url_same_day_only": True,
        "scientific_rule_changed": False,
        "signal_evaluated": False,
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }
    p.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "shard": sid,
        "classification": x.get("classification"),
        "empty_rowgroups_skipped": EMPTY_ROWGROUPS_SKIPPED,
        "nonempty_rowgroups_used": NONEMPTY_ROWGROUPS_USED,
        "signal": False,
        "market": False,
        "returns": False,
        "pnl": False,
    }, sort_keys=True))
    return 0 if x.get("classification") == "SHARD_PASS" else (rc or 2)


if __name__ == "__main__":
    sys.exit(main())
