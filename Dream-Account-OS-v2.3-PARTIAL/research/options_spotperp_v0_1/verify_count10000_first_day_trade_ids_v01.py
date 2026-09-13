#!/usr/bin/env python3
"""Outcome-blind exact trade-ID equivalence verifier for 2021-04-01.

The reference hash was computed from the preserved count=1000 one-day raw probe
artifact (7,149 unique trade IDs). This verifier can be applied to a completed
count=10000 full raw acquisition to prove that pagination optimization preserved
the exact first-day trade set, not merely the row count.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path

UTC = dt.timezone.utc
DAY_START = int(dt.datetime(2021, 4, 1, tzinfo=UTC).timestamp() * 1000)
DAY_END = int(dt.datetime(2021, 4, 2, tzinfo=UTC).timestamp() * 1000) - 1
EXPECTED_TRADE_COUNT = 7149
EXPECTED_UNIQUE_TRADE_IDS = 7149
EXPECTED_SORTED_TRADE_ID_SHA256 = "95bd1de97b47f40a76c05ea51346a983c619b5eb6a6ac22251bacf85f45edd86"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="source_audit_data")
    args = ap.parse_args()
    root = Path(args.input).resolve()
    manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf-8"))

    ids: list[str] = []
    rows = 0
    pages = 0
    for e in manifest.get("raw_pages", []):
        lo, hi = int(e["start_ms"]), int(e["end_ms"])
        if hi < DAY_START or lo > DAY_END:
            continue
        p = root / "raw" / e["page"]
        obj = json.loads(gzip.decompress(p.read_bytes()).decode("utf-8"))
        trades = obj.get("result", {}).get("trades", [])
        pages += 1
        for row in trades:
            ts = int(row["timestamp"])
            if DAY_START <= ts <= DAY_END:
                rows += 1
                tid = str(row.get("trade_id", ""))
                if not tid:
                    raise RuntimeError("missing trade_id in first-day raw data")
                ids.append(tid)

    digest = hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()
    assert rows == EXPECTED_TRADE_COUNT, (rows, EXPECTED_TRADE_COUNT)
    assert len(ids) == EXPECTED_UNIQUE_TRADE_IDS, len(ids)
    assert len(set(ids)) == EXPECTED_UNIQUE_TRADE_IDS, len(set(ids))
    assert digest == EXPECTED_SORTED_TRADE_ID_SHA256, digest

    print("COUNT10000_EXACT_TRADE_ID_EQUIVALENCE_PASS")
    print(f"PAGES={pages}")
    print(f"TRADES={rows}")
    print(f"UNIQUE_TRADE_IDS={len(set(ids))}")
    print(f"SORTED_TRADE_ID_SHA256={digest}")
    print("NO SKEW / NO SIGNALS / NO RETURNS / NO PNL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
