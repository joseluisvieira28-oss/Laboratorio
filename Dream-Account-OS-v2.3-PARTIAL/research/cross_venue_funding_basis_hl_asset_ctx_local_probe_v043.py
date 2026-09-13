"""Local requester-pays Hyperliquid asset_ctx provenance probe (V0.4.3).

Expected usage AFTER the user has explicitly downloaded the pre-registered S3
objects with their own AWS requester-pays credentials. This reader emits only
schema/timestamp/hash/missing-sentinel diagnostics. It never emits nonzero
price values or computes basis/returns/carry/PnL.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import lz4.frame
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: pip install lz4") from exc

REQUIRED = {"time", "coin", "mark_px", "oracle_px", "mid_px"}
TARGET_COINS = {"BTC", "ETH"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _minute_key(text: str) -> str:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def inspect_file(path: Path) -> dict[str, Any]:
    with lz4.frame.open(path, "rb") as fh:
        raw = fh.read()
    text = io.StringIO(raw.decode("utf-8"))
    reader = csv.DictReader(text)
    columns = reader.fieldnames or []
    required_ok = REQUIRED.issubset(columns)

    rows = Counter()
    minutes: dict[str, set[str]] = defaultdict(set)
    exact_times: dict[str, Counter[str]] = defaultdict(Counter)
    zero_mark = Counter()
    first: dict[str, str | None] = {"BTC": None, "ETH": None}
    last: dict[str, str | None] = {"BTC": None, "ETH": None}

    if required_ok:
        for row in reader:
            coin = row.get("coin")
            if coin not in TARGET_COINS:
                continue
            t = row.get("time") or ""
            rows[coin] += 1
            exact_times[coin][t] += 1
            try:
                minutes[coin].add(_minute_key(t))
            except ValueError:
                pass
            if first[coin] is None or t < first[coin]:
                first[coin] = t
            if last[coin] is None or t > last[coin]:
                last[coin] = t
            try:
                if float(row.get("mark_px", "nan")) == 0.0:
                    zero_mark[coin] += 1
            except ValueError:
                zero_mark[coin] += 1

    duplicates = {
        coin: sum(c - 1 for c in exact_times[coin].values() if c > 1)
        for coin in TARGET_COINS
    }
    return {
        "file": path.name,
        "compressed_sha256": _sha256(path),
        "schema_columns": columns,
        "required_columns_present": required_ok,
        "BTC_row_count": rows["BTC"],
        "ETH_row_count": rows["ETH"],
        "BTC_distinct_minute_count": len(minutes["BTC"]),
        "ETH_distinct_minute_count": len(minutes["ETH"]),
        "duplicate_timestamp_counts": duplicates,
        "mark_px_zero_sentinel_counts": {"BTC": zero_mark["BTC"], "ETH": zero_mark["ETH"]},
        "first_timestamp": first,
        "last_timestamp": last,
        "price_values_output": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", type=Path)
    ap.add_argument("--output", type=Path, default=Path("HYPERLIQUID_ASSET_CTX_PROVENANCE_V043_RECEIPT.json"))
    args = ap.parse_args()
    files = sorted(args.directory.glob("*.csv.lz4"))
    if not files:
        raise SystemExit("No *.csv.lz4 files found")
    results = [inspect_file(p) for p in files]
    receipt = {
        "schema_version": "0.1",
        "lab_id": "CROSS_VENUE_FUNDING_BASIS_LAB_V01",
        "probe_id": "HYPERLIQUID_ASSET_CTX_PROVENANCE_PROBE_V043",
        "classification": "LOCAL_PROVENANCE_ONLY_NOT_DISCOVERY",
        "file_count": len(results),
        "files": results,
        "all_required_columns_present": all(x["required_columns_present"] for x in results),
        "all_target_coins_present": all(x["BTC_row_count"] > 0 and x["ETH_row_count"] > 0 for x in results),
        "price_values_output": False,
        "basis_computed": False,
        "returns_computed": False,
        "carry_computed": False,
        "pnl_computed": False,
        "discovery_authorized": False,
        "trading_authorized": False,
    }
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS_SAMPLE_SCHEMA" if receipt["all_required_columns_present"] and receipt["all_target_coins_present"] else "FAIL_CLOSED",
        "file_count": len(results),
        "receipt": str(args.output),
    }))
    return 0 if receipt["all_required_columns_present"] and receipt["all_target_coins_present"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
