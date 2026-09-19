#!/usr/bin/env python3
"""L2-RESILIENCY-001 full-corpus structural schema audit V0.1.

SOURCE-SCHEMA ONLY / OUTCOME-BLIND.

Implements the frozen policy:
research/l2_resiliency/L2_RESILIENCY_001_FULL_CORPUS_SCHEMA_AUDIT_POLICY_V0_1.md

This program validates raw Hyperliquid 2024 BTC l2Book corpus bytes and structure.
It DOES NOT construct sweep events, replenishment ratios, midpoint responses,
returns, PnL, or any trading signal.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

import lz4.frame

LAB_ID = "L2-RESILIENCY-001"
EXPECTED_OBJECTS = 8707
EXPECTED_TOTAL_BYTES = 6_832_137_900
YEAR = 2024
ASSET = "BTC"

KEY_PREFIX = "market_data/"
KEY_SUFFIX = "/l2Book/BTC.lz4"


class AuditFailure(RuntimeError):
    pass


def sha256_and_md5(path: Path) -> tuple[str, str, int]:
    h256 = hashlib.sha256()
    hmd5 = hashlib.md5()
    total = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(8 * 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            h256.update(chunk)
            hmd5.update(chunk)
    return h256.hexdigest(), hmd5.hexdigest(), total


def parse_hour_from_key(key: str) -> dt.datetime:
    # Exact expected shape: market_data/YYYYMMDD/H/l2Book/BTC.lz4
    parts = key.split("/")
    if len(parts) != 5 or parts[0] != "market_data" or parts[3] != "l2Book" or parts[4] != "BTC.lz4":
        raise AuditFailure(f"unexpected key shape: {key}")
    ymd = parts[1]
    hour_raw = parts[2]
    if len(ymd) != 8 or not ymd.isdigit() or not hour_raw.isdigit():
        raise AuditFailure(f"invalid key timestamp: {key}")
    hour = int(hour_raw)
    if not 0 <= hour <= 23:
        raise AuditFailure(f"invalid key hour: {key}")
    x = dt.datetime.strptime(ymd, "%Y%m%d").replace(hour=hour, tzinfo=dt.timezone.utc)
    if x.year != YEAR:
        raise AuditFailure(f"protected/non-2024 key rejected: {key}")
    return x


def hour_bounds_ms(key: str) -> tuple[int, int]:
    x = parse_hour_from_key(key)
    start = int(x.timestamp() * 1000)
    return start, start + 3_600_000


def _pick(row: dict[str, Any], names: Iterable[str]) -> Any:
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return None


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Load a strict present-object manifest while tolerating serialization shape only.

    Accepted serialization: JSON array/object with rows, JSONL, or CSV.
    Field aliases are transport/schema aliases only; all scientific identities
    (key, byte size, SHA256, MD5/ETag) remain mandatory.
    """
    suffix = path.suffix.lower()
    rows: list[dict[str, Any]]
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = [dict(r) for r in csv.DictReader(f)]
    else:
        text = path.read_text(encoding="utf-8")
        try:
            obj = json.loads(text)
            if isinstance(obj, list):
                rows = [dict(x) for x in obj]
            elif isinstance(obj, dict) and isinstance(obj.get("rows"), list):
                rows = [dict(x) for x in obj["rows"]]
            else:
                raise ValueError("not row container")
        except Exception:
            rows = [dict(json.loads(line)) for line in text.splitlines() if line.strip()]

    normalized = []
    for i, r in enumerate(rows):
        status = str(_pick(r, ["status", "inventory_status"]) or "PRESENT").upper()
        if status != "PRESENT":
            # The body manifest for this gate must contain exactly PRESENT objects only.
            continue
        key = _pick(r, ["key", "object_key", "s3_key"])
        size = _pick(r, ["content_length", "size", "bytes", "compressed_bytes"])
        sha = _pick(r, ["sha256", "sha_256", "raw_sha256"])
        md5 = _pick(r, ["md5", "etag_md5", "content_md5"])
        etag = _pick(r, ["etag", "ETag"])
        local_path = _pick(r, ["local_path", "path", "file", "filename"])

        if key is None or size is None or sha is None:
            raise AuditFailure(f"manifest row {i} missing mandatory key/size/sha256")
        key = str(key)
        parse_hour_from_key(key)
        try:
            size_i = int(size)
        except Exception as exc:
            raise AuditFailure(f"manifest row {i} invalid size") from exc
        sha_s = str(sha).lower().strip()
        if len(sha_s) != 64 or any(c not in "0123456789abcdef" for c in sha_s):
            raise AuditFailure(f"manifest row {i} invalid sha256")

        etag_s = str(etag).strip().strip('"').lower() if etag is not None else None
        md5_s = str(md5).lower().strip() if md5 is not None else None
        # Frozen acquisition receipt says every row has valid MD5 and ordinary ETag.
        if md5_s is None and etag_s is not None and len(etag_s) == 32 and "-" not in etag_s:
            md5_s = etag_s
        if md5_s is None or len(md5_s) != 32 or any(c not in "0123456789abcdef" for c in md5_s):
            raise AuditFailure(f"manifest row {i} missing/invalid md5")
        if etag_s is None or etag_s != md5_s:
            raise AuditFailure(f"manifest row {i} ETag/MD5 mismatch")

        normalized.append({
            "key": key,
            "content_length": size_i,
            "sha256": sha_s,
            "md5": md5_s,
            "etag": etag_s,
            "local_path": str(local_path) if local_path else None,
        })

    normalized.sort(key=lambda x: parse_hour_from_key(x["key"]))
    keys = [x["key"] for x in normalized]
    if len(keys) != len(set(keys)):
        raise AuditFailure("duplicate manifest key")
    return normalized


@dataclass
class ObjectAudit:
    key: str
    compressed_bytes: int
    record_count: int
    first_timestamp_ms: int | None
    last_timestamp_ms: int | None
    duplicate_timestamp_transitions: int
    json_schema_violations: int
    wrong_coin_channel_records: int
    timestamp_outside_hour_records: int
    backward_timestamp_transitions: int
    top5_structural_violations: int
    crossed_book_records: int


def parse_num(x: Any, field: str) -> float:
    try:
        v = float(x)
    except Exception as exc:
        raise AuditFailure(f"non-numeric {field}") from exc
    if not math.isfinite(v):
        raise AuditFailure(f"non-finite {field}")
    return v


def audit_record(obj: Any, start_ms: int, end_ms: int) -> tuple[int, bool, bool]:
    """Return (timestamp_ms, top5_ok, uncrossed_ok); raise on structural violation."""
    if not isinstance(obj, dict):
        raise AuditFailure("top-level record not object")
    if "time" not in obj or "ver_num" not in obj or "raw" not in obj:
        raise AuditFailure("missing top-level time/ver_num/raw")
    raw = obj.get("raw")
    if not isinstance(raw, dict):
        raise AuditFailure("raw not object")
    if raw.get("channel") != "l2Book":
        raise AuditFailure("wrong channel")
    data = raw.get("data")
    if not isinstance(data, dict):
        raise AuditFailure("raw.data not object")
    if data.get("coin") != ASSET:
        raise AuditFailure("wrong coin")
    ts = data.get("time")
    if not isinstance(ts, int):
        raise AuditFailure("data.time not integer")
    if not start_ms <= ts < end_ms:
        raise AuditFailure("timestamp outside encoded UTC hour")

    levels = data.get("levels")
    if not isinstance(levels, list) or len(levels) != 2:
        raise AuditFailure("levels must contain exactly two sides")
    if not all(isinstance(side, list) and len(side) >= 5 for side in levels):
        raise AuditFailure("each side must contain at least five levels")

    bid_prices: list[float] = []
    ask_prices: list[float] = []
    for side_i, side in enumerate(levels):
        prices = []
        for level in side[:5]:
            if not isinstance(level, dict):
                raise AuditFailure("level not object")
            px = parse_num(level.get("px"), "px")
            sz = parse_num(level.get("sz"), "sz")
            n = level.get("n")
            if px <= 0 or sz < 0 or not isinstance(n, int) or n < 0:
                raise AuditFailure("invalid top5 level values")
            prices.append(px)
        if side_i == 0:
            bid_prices = prices
            if not all(bid_prices[i] > bid_prices[i + 1] for i in range(4)):
                raise AuditFailure("bid top5 not strictly descending")
        else:
            ask_prices = prices
            if not all(ask_prices[i] < ask_prices[i + 1] for i in range(4)):
                raise AuditFailure("ask top5 not strictly ascending")

    if not bid_prices or not ask_prices or not bid_prices[0] < ask_prices[0]:
        raise AuditFailure("crossed/locked best book")
    return ts, True, True


def resolve_local_path(corpus_root: Path, row: dict[str, Any]) -> Path:
    lp = row.get("local_path")
    if lp:
        p = Path(lp)
        if not p.is_absolute():
            p = corpus_root / p
        if p.is_file():
            return p
    p = corpus_root / row["key"]
    if p.is_file():
        return p
    # Conservative flat-file fallback uses exact basename only if unique.
    basename = Path(row["key"]).name
    hits = list(corpus_root.rglob(basename))
    if len(hits) == 1:
        return hits[0]
    raise AuditFailure(f"raw object not found uniquely for {row['key']}")


def audit_object(path: Path, row: dict[str, Any]) -> ObjectAudit:
    sha, md5, size = sha256_and_md5(path)
    if size != int(row["content_length"]):
        raise AuditFailure(f"{row['key']}: compressed byte size mismatch")
    if sha != row["sha256"]:
        raise AuditFailure(f"{row['key']}: SHA256 mismatch")
    if md5 != row["md5"] or md5 != row["etag"]:
        raise AuditFailure(f"{row['key']}: MD5/ETag mismatch")

    start_ms, end_ms = hour_bounds_ms(row["key"])
    count = 0
    first_ts = None
    last_ts = None
    dup = 0

    try:
        with lz4.frame.open(path, mode="rb") as f:
            for raw_line in f:
                if not raw_line.strip():
                    continue
                try:
                    obj = json.loads(raw_line)
                except Exception as exc:
                    raise AuditFailure(f"{row['key']}: invalid JSON") from exc
                try:
                    ts, _, _ = audit_record(obj, start_ms, end_ms)
                except AuditFailure as exc:
                    raise AuditFailure(f"{row['key']}: {exc}") from exc
                if last_ts is not None:
                    if ts < last_ts:
                        raise AuditFailure(f"{row['key']}: backwards timestamp")
                    if ts == last_ts:
                        dup += 1
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
                count += 1
    except lz4.frame.LZ4FrameError as exc:
        raise AuditFailure(f"{row['key']}: LZ4 decompression failure") from exc

    if count <= 0:
        raise AuditFailure(f"{row['key']}: zero records")

    return ObjectAudit(
        key=row["key"],
        compressed_bytes=size,
        record_count=count,
        first_timestamp_ms=first_ts,
        last_timestamp_ms=last_ts,
        duplicate_timestamp_transitions=dup,
        json_schema_violations=0,
        wrong_coin_channel_records=0,
        timestamp_outside_hour_records=0,
        backward_timestamp_transitions=0,
        top5_structural_violations=0,
        crossed_book_records=0,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-root", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default="L2_RESILIENCY_001_FULL_CORPUS_SCHEMA_AUDIT_V0_1.json")
    args = ap.parse_args()

    corpus_root = Path(args.corpus_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    out_path = Path(args.out).resolve()

    receipt: dict[str, Any] = {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "phase": "FULL_CORPUS_STRUCTURAL_SCHEMA_AUDIT_ONLY",
        "classification": None,
        "firewalls": {
            "sweep_events_computed": False,
            "replenishment_computed": False,
            "midpoint_response_computed": False,
            "returns_computed": False,
            "pnl_computed": False,
            "access_2025": False,
            "access_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }

    try:
        rows = load_manifest(manifest_path)
        if len(rows) != EXPECTED_OBJECTS:
            raise AuditFailure(f"manifest present-object count {len(rows)} != {EXPECTED_OBJECTS}")
        total_bytes = sum(int(r["content_length"]) for r in rows)
        if total_bytes != EXPECTED_TOTAL_BYTES:
            raise AuditFailure(f"manifest byte total {total_bytes} != {EXPECTED_TOTAL_BYTES}")

        audits: list[ObjectAudit] = []
        total_records = 0
        total_dups = 0
        prev: ObjectAudit | None = None
        prev_hour: dt.datetime | None = None
        segment_count = 0
        segment_breaks: list[dict[str, Any]] = []

        for idx, row in enumerate(rows):
            p = resolve_local_path(corpus_root, row)
            a = audit_object(p, row)
            current_hour = parse_hour_from_key(row["key"])
            if prev_hour is None or current_hour != prev_hour + dt.timedelta(hours=1):
                segment_count += 1
                if prev_hour is not None:
                    gap_hours = int((current_hour - prev_hour).total_seconds() // 3600) - 1
                    segment_breaks.append({
                        "after_key": prev.key if prev else None,
                        "before_key": a.key,
                        "missing_hours": gap_hours,
                    })
            elif prev is not None:
                # Adjacent PRESENT objects must not move time backwards across the boundary.
                if a.first_timestamp_ms is None or prev.last_timestamp_ms is None:
                    raise AuditFailure("missing object boundary timestamps")
                if a.first_timestamp_ms < prev.last_timestamp_ms:
                    raise AuditFailure(f"cross-object backwards timestamp {prev.key} -> {a.key}")

            audits.append(a)
            total_records += a.record_count
            total_dups += a.duplicate_timestamp_transitions
            prev = a
            prev_hour = current_hour
            if (idx + 1) % 250 == 0:
                print(json.dumps({"objects_audited": idx + 1, "records": total_records}, sort_keys=True), flush=True)

        # 8784 expected hourly keys - 8707 present = exactly 77 missing.
        gap_total = sum(int(x["missing_hours"]) for x in segment_breaks)
        if gap_total != 77:
            raise AuditFailure(f"missing-hour segmentation total {gap_total} != 77")

        receipt.update({
            "classification": "SOURCE_SCHEMA_PASS",
            "objects_expected": EXPECTED_OBJECTS,
            "objects_audited": len(audits),
            "compressed_bytes_verified": total_bytes,
            "total_records": total_records,
            "duplicate_timestamp_transitions": total_dups,
            "source_segment_count": segment_count,
            "missing_hours_total": gap_total,
            "segment_breaks": segment_breaks,
            "object_summaries": [asdict(a) for a in audits],
            "violations": {
                "raw_byte_binding": 0,
                "decompression": 0,
                "json_schema": 0,
                "wrong_coin_channel": 0,
                "timestamp_outside_hour": 0,
                "backward_timestamp": 0,
                "top5_structure": 0,
                "crossed_book": 0,
            },
            "next_gate": "SEPARATE_PRE_DISCOVERY_EVENT_CONSTRUCTION_PROTOCOL",
        })
        rc = 0
    except Exception as exc:
        receipt.update({
            "classification": "SOURCE_SCHEMA_FAIL_CLOSED",
            "failure": f"{type(exc).__name__}: {str(exc)[:2000]}",
            "next_gate": None,
        })
        rc = 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "objects_audited": receipt.get("objects_audited"),
        "total_records": receipt.get("total_records"),
        "missing_hours_total": receipt.get("missing_hours_total"),
        "sweep_events_computed": False,
        "returns_computed": False,
        "pnl_computed": False,
    }, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
