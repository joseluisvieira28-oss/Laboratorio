#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import fsspec
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "base_rep_source",
    HERE / "xatu_v3_replication_queue_shard_v01.py",
)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)

ORIGINAL_RECONSTRUCT_DAY = base.reconstruct_day
ALLOWED_SHARDS = {"202502", "202503", "202510"}
FALLBACK_ERROR_TOKEN = "no timestamp row-group stats"


def _actual_timestamp_ranges(pf: pq.ParquetFile) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for i in range(pf.metadata.num_row_groups):
        tab = pf.read_row_group(i, columns=["epoch_start_date_time"])
        arr = tab["epoch_start_date_time"]
        if arr.null_count:
            raise RuntimeError(f"row group {i}: null epoch_start_date_time")
        mn = pc.min(arr).as_py()
        mx = pc.max(arr).as_py()
        if mn is None or mx is None:
            raise RuntimeError(f"row group {i}: empty epoch_start_date_time")
        out.append((i, base.stat_int(mn), base.stat_int(mx)))
    if not out:
        raise RuntimeError("no row groups available for column-value fallback")
    return out


def reconstruct_day_column_value(d):
    url = base.url_for(d)
    with fsspec.open(
        url,
        "rb",
        block_size=4 * 1024 * 1024,
        cache_type="readahead",
    ) as f:
        pf = pq.ParquetFile(f)
        names = list(pf.schema_arrow.names)
        miss = [c for c in base.COLS if c not in names]
        if miss:
            raise RuntimeError(f"{d}: required columns missing {miss}")

        actual = _actual_timestamp_ranges(pf)
        T = min(x[1] for x in actual)
        start = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
        if not (start <= T <= start + base.MAX_OFFSET):
            raise RuntimeError(f"{d}: selected timestamp outside +32 slots: {T}")

        selected = [i for i, mn, mx in actual if mn <= T <= mx]
        if not selected:
            raise RuntimeError(f"{d}: no row group contains selected timestamp")

        tab = pf.read_row_groups(selected, columns=base.COLS)
        filt = tab.filter(
            pc.equal(
                tab["epoch_start_date_time"],
                pa.scalar(T, type=tab["epoch_start_date_time"].type),
            )
        )
        n = int(filt.num_rows)
        if n <= 0:
            raise RuntimeError(f"{d}: zero validator rows at selected timestamp")
        if filt["index"].null_count:
            raise RuntimeError(f"{d}: null validator index")
        uniq = int(pc.count_distinct(filt["index"]).as_py())
        if uniq != n:
            raise RuntimeError(f"{d}: duplicate validator index rows={n} unique={uniq}")
        epn = int(pc.count_distinct(filt["epoch"]).as_py())
        if epn != 1:
            raise RuntimeError(f"{d}: selected timestamp has {epn} epochs")
        epoch = int(pc.min(filt["epoch"]).as_py())
        pending = base.status_count(filt["status"], "pending_queued")
        exiting = base.status_count(filt["status"], "active_exiting")
        return {
            "date": d.isoformat(),
            "url": url,
            "selected_unix_time": T,
            "selected_time_utc": datetime.fromtimestamp(T, tz=timezone.utc).isoformat(),
            "selected_epoch": epoch,
            "selected_row_groups": selected,
            "validator_rows": n,
            "unique_validator_indices": uniq,
            "pending_queued_count": pending,
            "active_exiting_count": exiting,
            "net_queue_count": pending - exiting,
            "timestamp_locator": "COLUMN_VALUE_FALLBACK_NO_ROWGROUP_STATS",
        }


def reconstruct_day_v012(d):
    try:
        row = ORIGINAL_RECONSTRUCT_DAY(d)
        row["timestamp_locator"] = "ROWGROUP_METADATA_STATS"
        return row
    except RuntimeError as exc:
        if FALLBACK_ERROR_TOKEN not in str(exc):
            raise
        return reconstruct_day_column_value(d)


def equivalence_payload(d):
    original = ORIGINAL_RECONSTRUCT_DAY(d)
    fallback = reconstruct_day_column_value(d)
    fields = [
        "selected_unix_time",
        "selected_epoch",
        "validator_rows",
        "unique_validator_indices",
        "pending_queued_count",
        "active_exiting_count",
        "net_queue_count",
    ]
    mismatch = {
        k: {"original": original.get(k), "fallback": fallback.get(k)}
        for k in fields
        if original.get(k) != fallback.get(k)
    }
    return {
        "date": d.isoformat(),
        "pass": not mismatch,
        "mismatch": mismatch,
        "fields": {k: original.get(k) for k in fields},
    }


def main() -> int:
    sid = os.environ["SHARD_ID"]
    if sid not in ALLOWED_SHARDS:
        raise SystemExit("recovery shard outside frozen allowlist")

    base.reconstruct_day = reconstruct_day_v012
    rc = base.main()

    p = Path("xatu_v3_replication_shards") / f"queue_rep_{sid}.json"
    if not p.exists():
        return 2

    x = json.loads(p.read_text(encoding="utf-8"))
    x["phase"] = "V3_INDEPENDENT_REPLICATION_SOURCE_SHARD_V0_1_2_PARQUET_METADATA_FALLBACK"
    x["parquet_metadata_fallback"] = {
        "allowed_shards": sorted(ALLOWED_SHARDS),
        "fallback_trigger_exact": FALLBACK_ERROR_TOKEN,
        "same_url_same_day_only": True,
        "timestamp_semantics_changed": False,
        "scientific_rule_changed": False,
        "signal_evaluated": False,
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }
    p.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fallback_days = [
        r["date"]
        for r in x.get("daily_source_records") or []
        if r.get("timestamp_locator") == "COLUMN_VALUE_FALLBACK_NO_ROWGROUP_STATS"
    ]
    print(
        json.dumps(
            {
                "shard": sid,
                "classification": x.get("classification"),
                "observed": x.get("observed_dates"),
                "errors": len(x.get("errors") or []),
                "fallback_days": fallback_days,
                "signal": False,
                "market": False,
                "returns": False,
                "pnl": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if x.get("classification") == "SHARD_PASS" else (rc or 2)


if __name__ == "__main__":
    sys.exit(main())
