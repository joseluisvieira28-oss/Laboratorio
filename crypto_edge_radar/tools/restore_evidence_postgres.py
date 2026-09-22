#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path

from radar.evidence_portability import restore_snapshot


def load_snapshot(path: Path) -> dict:
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    snapshot = load_snapshot(Path(args.snapshot))
    result = restore_snapshot(
        snapshot,
        target_url=os.getenv("RADAR_MIGRATION_TARGET_URL", ""),
        apply=bool(args.apply),
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["classification"] in {
        "AUTH_REQUIRED_NOT_EXECUTED",
        "DRY_RUN_VERIFIED_NO_TARGET_MUTATION",
        "TARGET_RESTORE_VERIFIED",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
