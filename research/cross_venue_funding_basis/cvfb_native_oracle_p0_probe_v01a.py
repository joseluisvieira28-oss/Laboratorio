#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
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
TOTAL_BLOCKS = 2 * RADIUS + 1
SHARDS = 12
MIN_INTERVAL_SECONDS = 2.3
TOKENS = ("oracle", "funding", "mark", "price", "premium")
LAST_REQUEST_MONO = 0.0


def fail(msg: str) -> None:
    raise RuntimeError("TECHNICAL_BLOCKED: " + msg)


def pace() -> None:
    global LAST_REQUEST_MONO
    now = time.monotonic()
    delay = MIN_INTERVAL_SECONDS - (now - LAST_REQUEST_MONO)
    if delay > 0:
        time.sleep(delay)
    LAST_REQUEST_MONO = time.monotonic()


def post_block(height: int, retries: int = 8) -> dict:
    payload = json.dumps({"type": "blockDetails", "height": int(height)}, separators=(",", ":")).encode()
    last = None
    for attempt in range(retries):
        pace()
        req = urllib.request.Request(
            ENDPOINT,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "CryptoLab-CVFB-P0/0.1A",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                if r.status != 200:
                    raise RuntimeError(f"HTTP {r.status}")
                data = json.loads(body)
                if not isinstance(data, dict):
                    raise RuntimeError("non-object response")
                return data
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 and attempt + 1 < retries:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                try:
                    sleep_s = max(65.0, float(retry_after)) if retry_after else 65.0
                except Exception:
                    sleep_s = 65.0
                time.sleep(sleep_s)
                continue
            if attempt + 1 < retries:
                time.sleep(min(30.0, 2.0 ** attempt))
        except Exception as e:
            last = e
            if attempt + 1 < retries:
                time.sleep(min(30.0, 2.0 ** attempt))
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


def write_json(path: str | Path, obj: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def do_boundary(out: str) -> None:
    low_raw = post_block(LOW_HEIGHT)
    high_raw = post_block(HIGH_HEIGHT)
    low_t, high_t = block_time(low_raw), block_time(high_raw)
    if not (low_t < TARGET_MS <= high_t):
        fail("frozen height bracket does not contain target")
    lo, hi = LOW_HEIGHT, HIGH_HEIGHT
    query_count = 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        raw = post_block(mid)
        query_count += 1
        if block_time(raw) < TARGET_MS:
            lo = mid
        else:
            hi = mid
    chosen_raw = post_block(hi)
    prev_raw = post_block(hi - 1)
    query_count += 2
    chosen_t = block_time(chosen_raw)
    prev_t = block_time(prev_raw)
    if not (prev_t < TARGET_MS <= chosen_t):
        fail("binary-search boundary invariant failed")
    receipt = {
        "schema_version": "0.1A",
        "stage": "P0_BOUNDARY",
        "status": "COMPLETE",
        "target_utc": "2024-09-01T00:00:00Z",
        "target_epoch_ms": TARGET_MS,
        "height_bracket": [LOW_HEIGHT, HIGH_HEIGHT],
        "first_height_at_or_after_target": hi,
        "first_time_utc": iso(chosen_t),
        "previous_height": hi - 1,
        "previous_time_utc": iso(prev_t),
        "query_count": query_count,
        "low_response_sha256": canonical_sha(low_raw),
        "high_response_sha256": canonical_sha(high_raw),
        "chosen_response_sha256": canonical_sha(chosen_raw),
        "previous_response_sha256": canonical_sha(prev_raw),
        "market_numeric_values_emitted": False,
        "economic_outcomes_computed": False,
        "2026_opened": False,
    }
    write_json(out, receipt)
    print(json.dumps({"status": "COMPLETE", "center_height": hi, "query_count": query_count}))


def shard_bounds(center: int, shard: int) -> tuple[int, int, int]:
    if shard < 0 or shard >= SHARDS:
        fail("invalid shard index")
    base = TOTAL_BLOCKS // SHARDS
    rem = TOTAL_BLOCKS % SHARDS
    count = base + (1 if shard < rem else 0)
    start_index = shard * base + min(shard, rem)
    start = center - RADIUS + start_index
    end = start + count - 1
    return start, end, count


def do_scan(center: int, shard: int, out: str) -> None:
    start, end, expected = shard_bounds(center, shard)
    all_paths = set()
    all_types = collections.Counter()
    hashes = []
    first_ms = None
    last_ms = None
    for h in range(start, end + 1):
        raw = post_block(h)
        t = block_time(raw)
        if t >= 1767225600000:
            fail("2026 block encountered")
        if first_ms is None:
            first_ms = t
        last_ms = t
        paths, types = walk_schema(raw)
        all_paths.update(paths)
        all_types.update(types)
        hashes.append({"height": h, "block_time_utc": iso(t), "sha256": canonical_sha(raw)})
    if len(hashes) != expected:
        fail("shard incomplete")
    receipt = {
        "schema_version": "0.1A",
        "stage": "P0_SCAN_SHARD",
        "status": "COMPLETE",
        "shard": shard,
        "shards_total": SHARDS,
        "center_height": center,
        "start_height": start,
        "end_height": end,
        "block_count": len(hashes),
        "first_time_utc": iso(first_ms),
        "last_time_utc": iso(last_ms),
        "schema_key_paths": sorted(all_paths),
        "transaction_action_type_labels": dict(sorted(all_types.items())),
        "raw_response_fingerprints": hashes,
        "market_numeric_values_emitted": False,
        "economic_outcomes_computed": False,
        "2026_opened": False,
    }
    write_json(out, receipt)
    print(json.dumps({"status": "COMPLETE", "shard": shard, "blocks": len(hashes)}))


def do_aggregate(boundary_path: str, scan_dir: str, out: str) -> None:
    boundary = json.loads(Path(boundary_path).read_text(encoding="utf-8"))
    if boundary.get("status") != "COMPLETE":
        fail("boundary incomplete")
    center = int(boundary["first_height_at_or_after_target"])
    files = sorted(glob.glob(str(Path(scan_dir) / "CVFB_NATIVE_ORACLE_PROVENANCE_P0_SCAN_SHARD_*.json")))
    if len(files) != SHARDS:
        fail(f"expected {SHARDS} shard receipts, found {len(files)}")
    all_paths = set()
    all_types = collections.Counter()
    all_hashes = []
    seen_shards = set()
    for fp in files:
        r = json.loads(Path(fp).read_text(encoding="utf-8"))
        if r.get("status") != "COMPLETE":
            fail(f"incomplete shard {fp}")
        shard = int(r["shard"])
        if shard in seen_shards:
            fail("duplicate shard")
        seen_shards.add(shard)
        if int(r["center_height"]) != center:
            fail("center mismatch across shards")
        all_paths.update(r.get("schema_key_paths", []))
        all_types.update(r.get("transaction_action_type_labels", {}))
        all_hashes.extend(r.get("raw_response_fingerprints", []))
    heights = [int(x["height"]) for x in all_hashes]
    expected_heights = list(range(center - RADIUS, center + RADIUS + 1))
    if len(heights) != TOTAL_BLOCKS or len(set(heights)) != TOTAL_BLOCKS:
        fail("aggregate block count/uniqueness failure")
    if sorted(heights) != expected_heights:
        fail("aggregate frozen-height coverage failure")
    by_height = {int(x["height"]): x for x in all_hashes}
    ordered = [by_height[h] for h in expected_heights]
    token_paths = sorted(p for p in all_paths if any(tok in p.lower() for tok in TOKENS))
    oracle_paths = sorted(p for p in all_paths if "oracle" in p.lower())
    oracle_type_labels = sorted(k for k in all_types if "oracle" in k.lower())
    decision = "PASS_SCHEMA_CANDIDATE" if (oracle_paths or oracle_type_labels) else "FAIL_NO_NATIVE_ORACLE_SCHEMA_VISIBLE"
    receipt = {
        "schema_version": "0.1A",
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
            "start_height": center - RADIUS,
            "end_height": center + RADIUS,
            "block_count": len(ordered),
            "complete": True,
            "shards": SHARDS,
        },
        "schema": {
            "unique_key_path_count": len(all_paths),
            "sensitive_token_key_paths": token_paths,
            "oracle_key_paths": oracle_paths,
            "transaction_action_type_labels": dict(sorted(all_types.items())),
            "oracle_type_labels": oracle_type_labels,
        },
        "raw_response_fingerprints": ordered,
        "market_numeric_values_emitted": False,
        "economic_outcomes_computed": False,
        "primary_replication_reopened": False,
        "2026_opened": False,
        "live_trading_authorized": False,
        "next_action": (
            "FREEZE_P1_DETERMINISTIC_NATIVE_ORACLE_RECONSTRUCTION_BEFORE_ANY_ORACLE_VALUES"
            if decision == "PASS_SCHEMA_CANDIDATE"
            else "EXPLORER_BLOCKDETAILS_PATH_CLOSED; ASSESS_OFFICIAL_S3_REPLICA_CMDS_OR_OTHER_OFFICIAL_NODE_HISTORY_SOURCE_ONLY_WITH_SEPARATE_FREEZE"
        ),
    }
    write_json(out, receipt)
    print(json.dumps({
        "status": "COMPLETE",
        "decision": decision,
        "scanned_blocks": len(ordered),
        "oracle_key_path_count": len(oracle_paths),
        "oracle_type_label_count": len(oracle_type_labels),
        "2026_opened": False,
    }, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("boundary")
    p.add_argument("--out", required=True)
    p = sub.add_parser("scan")
    p.add_argument("--center", required=True, type=int)
    p.add_argument("--shard", required=True, type=int)
    p.add_argument("--out", required=True)
    p = sub.add_parser("aggregate")
    p.add_argument("--boundary", required=True)
    p.add_argument("--scan-dir", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "boundary":
        do_boundary(a.out)
    elif a.cmd == "scan":
        do_scan(a.center, a.shard, a.out)
    elif a.cmd == "aggregate":
        do_aggregate(a.boundary, a.scan_dir, a.out)


if __name__ == "__main__":
    main()
