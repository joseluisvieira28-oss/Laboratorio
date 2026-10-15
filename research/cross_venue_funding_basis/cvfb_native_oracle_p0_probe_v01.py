#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://rpc.hyperliquid.xyz/explorer"
TARGET_MS = 1725148800000
LOW_HEIGHT = 100_000_000
HIGH_HEIGHT = 600_000_000
RADIUS = 150
TOKENS = ("oracle", "funding", "mark", "price", "premium")


def fail(msg: str) -> None:
    raise RuntimeError("TECHNICAL_BLOCKED: " + msg)


def post_block(height: int, retries: int = 5) -> dict:
    payload = json.dumps({"type": "blockDetails", "height": int(height)}, separators=(",", ":")).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "CryptoLab-CVFB-P0/0.1"},
        method="POST",
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read()
                if r.status != 200:
                    raise RuntimeError(f"HTTP {r.status}")
                data = json.loads(body)
                if not isinstance(data, dict):
                    raise RuntimeError("non-object response")
                return data
        except Exception as e:
            last = e
            if attempt + 1 < retries:
                time.sleep(0.5 * (2 ** attempt))
    fail(f"blockDetails height={height} unavailable after retries: {last}")


def details(raw: dict) -> dict:
    d = raw.get("blockDetails", raw)
    if not isinstance(d, dict):
        fail("missing blockDetails object")
    return d


def block_time(raw: dict) -> int:
    d = details(raw)
    v = d.get("blockTime", d.get("block_time"))
    try:
        return int(v)
    except Exception:
        fail("missing/invalid blockTime")


def canonical_sha(raw: dict) -> str:
    b = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(b).hexdigest()


def walk_schema(obj, path="$", paths=None, types=None):
    if paths is None:
        paths = set()
    if types is None:
        types = collections.Counter()
    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = f"{path}.{k}"
            paths.add(kp)
            if str(k).lower() == "type" and isinstance(v, str):
                types[v] += 1
            walk_schema(v, kp, paths, types)
    elif isinstance(obj, list):
        ap = f"{path}[]"
        paths.add(ap)
        for v in obj:
            walk_schema(v, ap, paths, types)
    return paths, types


def iso(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")


def locate_target():
    low_raw = post_block(LOW_HEIGHT)
    high_raw = post_block(HIGH_HEIGHT)
    low_t, high_t = block_time(low_raw), block_time(high_raw)
    if not (low_t < TARGET_MS <= high_t):
        fail(f"frozen height bracket does not contain target: low={low_t}, high={high_t}, target={TARGET_MS}")
    lo, hi = LOW_HEIGHT, HIGH_HEIGHT
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        raw = post_block(mid)
        t = block_time(raw)
        if t < TARGET_MS:
            lo = mid
        else:
            hi = mid
    chosen_raw = post_block(hi)
    chosen_t = block_time(chosen_raw)
    prev_raw = post_block(hi - 1)
    prev_t = block_time(prev_raw)
    if not (prev_t < TARGET_MS <= chosen_t):
        fail("binary-search boundary invariant failed")
    return {
        "low_height": LOW_HEIGHT,
        "low_time_ms": low_t,
        "low_time_utc": iso(low_t),
        "high_height": HIGH_HEIGHT,
        "high_time_ms": high_t,
        "high_time_utc": iso(high_t),
        "first_height_at_or_after_target": hi,
        "first_time_ms": chosen_t,
        "first_time_utc": iso(chosen_t),
        "previous_height": hi - 1,
        "previous_time_ms": prev_t,
        "previous_time_utc": iso(prev_t),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    boundary = locate_target()
    center = boundary["first_height_at_or_after_target"]
    start, end = center - RADIUS, center + RADIUS

    all_paths = set()
    all_types = collections.Counter()
    hashes = []
    first_ms = None
    last_ms = None
    for i, h in enumerate(range(start, end + 1)):
        raw = post_block(h)
        t = block_time(raw)
        if t >= 1767225600000:  # 2026-01-01T00:00:00Z
            fail("2026 block encountered")
        if first_ms is None:
            first_ms = t
        last_ms = t
        paths, types = walk_schema(raw)
        all_paths.update(paths)
        all_types.update(types)
        hashes.append({"height": h, "block_time_ms": t, "sha256": canonical_sha(raw)})
        if i and i % 40 == 0:
            time.sleep(0.20)
        else:
            time.sleep(0.025)

    token_paths = sorted(p for p in all_paths if any(tok in p.lower() for tok in TOKENS))
    oracle_paths = sorted(p for p in all_paths if "oracle" in p.lower())
    oracle_type_labels = sorted(k for k in all_types if "oracle" in k.lower())
    decision = "PASS_SCHEMA_CANDIDATE" if (oracle_paths or oracle_type_labels) else "FAIL_NO_NATIVE_ORACLE_SCHEMA_VISIBLE"

    receipt = {
        "schema_version": "0.1",
        "recovery_id": "CVFB_NATIVE_ORACLE_PROVENANCE_RECOVERY_V0.5",
        "stage": "P0_SOURCE_SCHEMA_PROBE",
        "status": "COMPLETE",
        "decision": decision,
        "endpoint": ENDPOINT,
        "target_utc": "2024-09-01T00:00:00Z",
        "target_epoch_ms": TARGET_MS,
        "boundary": boundary,
        "scan": {
            "radius_blocks_each_side": RADIUS,
            "start_height": start,
            "end_height": end,
            "block_count": len(hashes),
            "first_time_utc": iso(first_ms),
            "last_time_utc": iso(last_ms),
            "complete": len(hashes) == 2 * RADIUS + 1,
        },
        "schema": {
            "unique_key_path_count": len(all_paths),
            "sensitive_token_key_paths": token_paths,
            "oracle_key_paths": oracle_paths,
            "transaction_action_type_labels": dict(sorted(all_types.items())),
            "oracle_type_labels": oracle_type_labels,
        },
        "raw_response_fingerprints": hashes,
        "market_numeric_values_emitted": False,
        "economic_outcomes_computed": False,
        "primary_replication_reopened": False,
        "2026_opened": False,
        "live_trading_authorized": False,
        "next_action": (
            "FREEZE_P1_DETERMINISTIC_NATIVE_ORACLE_RECONSTRUCTION_BEFORE_ANY_ORACLE_VALUES" if decision == "PASS_SCHEMA_CANDIDATE"
            else "EXPLORER_BLOCKDETAILS_PATH_CLOSED; ASSESS_OFFICIAL_S3_REPLICA_CMDS_OR_OTHER_OFFICIAL_NODE_HISTORY_SOURCE_ONLY_WITH_SEPARATE_FREEZE"
        ),
    }
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "decision": decision,
        "center_height": center,
        "scanned_blocks": len(hashes),
        "oracle_key_path_count": len(oracle_paths),
        "oracle_type_label_count": len(oracle_type_labels),
        "2026_opened": False,
    }, indent=2))


if __name__ == "__main__":
    main()
