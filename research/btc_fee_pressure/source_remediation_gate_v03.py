#!/usr/bin/env python3
"""BTC-FEE-PRESSURE-001 V0.3 technical source-remediation gate. No market outcomes."""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import struct
import sys
import time
import urllib.error
import urllib.request

LAB = "BTC-FEE-PRESSURE-001"
GATE = "BFP-SOURCE-REMEDIATION-V0.3"
BASE = "https://mempool.space"
START_TS = 1609459200  # 2021-01-01T00:00:00Z
END_TS = 1735689599    # 2024-12-31T23:59:59Z
START_DAY = dt.date(2021, 1, 1)
END_DAY = dt.date(2024, 12, 31)
OUT = pathlib.Path(os.environ.get("BFP_OUT", "btc_fee_pressure_source_remediation_v03_artifact"))
OUT.mkdir(parents=True, exist_ok=True)
HEADERS = {"Accept": "application/json", "User-Agent": "Laboratorio-Research-SourceGate/0.3"}
MAX_WORKERS = int(os.environ.get("BFP_WORKERS", "16"))
HTTP_TIMEOUT = int(os.environ.get("BFP_HTTP_TIMEOUT", "30"))
RETRIES = int(os.environ.get("BFP_RETRIES", "5"))

transport: list[dict] = []
raw_index: list[dict] = []


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str, retries: int = RETRIES):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                return r.status, dict(r.headers.items()), r.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 429 or e.code >= 500:
                last = (e.code, dict(e.headers.items()), body[:256])
                time.sleep(min(12, 2 ** attempt))
                continue
            return e.code, dict(e.headers.items()), body
        except Exception as e:
            last = e
            time.sleep(min(12, 2 ** attempt))
    raise RuntimeError(repr(last))


def height_at(ts: int):
    url = f"{BASE}/api/v1/mining/blocks/timestamp/{ts}"
    status, headers, body = get(url)
    if status in (401, 403):
        raise PermissionError(status)
    if status != 200:
        raise RuntimeError(f"height_http_{status}:{body[:200]!r}")
    obj = json.loads(body)
    if isinstance(obj, int):
        return obj, url, body, headers
    if isinstance(obj, dict) and isinstance(obj.get("height"), int):
        return obj["height"], url, body, headers
    raise ValueError(f"height_schema:{obj!r}")


def parse_batch(anchor: int, body: bytes):
    low = body.lower()
    if any(x in low for x in (b'"usd"', b'"price"', b'"market_price"')):
        raise RuntimeError("PROVENANCE_MARKET_FIELD")
    arr = json.loads(body)
    if not isinstance(arr, list) or not arr:
        raise ValueError("batch_not_nonempty_list")
    heights = [b.get("height") for b in arr]
    if not all(isinstance(h, int) for h in heights):
        raise ValueError("batch_height_schema")
    if heights[0] != anchor:
        raise ValueError(f"batch_anchor_mismatch:{anchor}:{heights[0]}")
    for a, b in zip(heights, heights[1:]):
        if b != a - 1:
            raise ValueError(f"batch_noncontiguous:{a}:{b}")
    return arr


def fetch_batch(anchor: int):
    url = f"{BASE}/api/v1/blocks/{anchor}"
    status, headers, body = get(url)
    return anchor, url, status, headers, body


verdict = None
start_h = end_h = None
all_blocks: dict[int, dict] = {}
batch_width = None
request_count = 0
started = time.time()

try:
    start_h, start_url, start_body, start_headers = height_at(START_TS)
    end_h, end_url, end_body, end_headers = height_at(END_TS)
    if not (0 < start_h <= end_h):
        raise ValueError("height_order")

    bounds_path = OUT / "raw_boundaries.bin"
    with bounds_path.open("wb") as f:
        for url, body in ((start_url, start_body), (end_url, end_body)):
            ub = url.encode()
            offset = f.tell()
            f.write(struct.pack(">II", len(ub), len(body)))
            f.write(ub)
            f.write(body)
            raw_index.append({
                "url": url,
                "container": bounds_path.name,
                "offset": offset,
                "body_bytes": len(body),
                "sha256": sha256_bytes(body),
            })

    # One frozen pre-2025 probe determines only transport batch width; it does not inspect market outcomes.
    probe_anchor = end_h
    probe_url = f"{BASE}/api/v1/blocks/{probe_anchor}"
    probe_status, probe_headers, probe_body = get(probe_url)
    if probe_status in (401, 403):
        verdict = "SOURCE_AUTH_BLOCKED"
    elif probe_status != 200:
        raise RuntimeError(f"probe_http_{probe_status}")
    else:
        probe_arr = parse_batch(probe_anchor, probe_body)
        batch_width = len(probe_arr)
        if batch_width < 2 or batch_width > 100:
            raise ValueError(f"unsafe_batch_width:{batch_width}")

        # Deterministic non-overlapping anchors. Full reconciliation below remains the actual gate.
        anchors = list(range(end_h, start_h - 1, -batch_width))
        request_count = len(anchors)
        raw_batches_path = OUT / "raw_block_batches.bin"
        with raw_batches_path.open("wb") as f, concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            for idx, item in enumerate(ex.map(fetch_batch, anchors), start=1):
                anchor, url, status, headers, body = item
                if status in (401, 403):
                    verdict = "SOURCE_AUTH_BLOCKED"
                    break
                if status != 200:
                    transport.append({"anchor": anchor, "status": status, "url": url})
                    verdict = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
                    break
                try:
                    arr = parse_batch(anchor, body)
                except RuntimeError as e:
                    if str(e) == "PROVENANCE_MARKET_FIELD":
                        verdict = "PROVENANCE_FAILURE"
                        break
                    raise
                except Exception as e:
                    transport.append({"anchor": anchor, "type": type(e).__name__, "message": str(e)})
                    verdict = "DATA_FAILURE"
                    break

                ub = url.encode()
                offset = f.tell()
                f.write(struct.pack(">II", len(ub), len(body)))
                f.write(ub)
                f.write(body)
                raw_index.append({
                    "url": url,
                    "container": raw_batches_path.name,
                    "offset": offset,
                    "body_bytes": len(body),
                    "sha256": sha256_bytes(body),
                    "status": status,
                    "anchor": anchor,
                })

                for block in arr:
                    h = block.get("height")
                    if not isinstance(h, int) or not (start_h <= h <= end_h):
                        continue
                    prior = all_blocks.get(h)
                    if prior is not None and prior.get("id") != block.get("id"):
                        verdict = "PROVENANCE_FAILURE"
                        break
                    all_blocks[h] = block
                if verdict:
                    break

                if idx % 1000 == 0:
                    print(json.dumps({
                        "progress_batches": idx,
                        "total_batches": request_count,
                        "blocks_collected": len(all_blocks),
                        "elapsed_seconds": round(time.time() - started, 1),
                    }, sort_keys=True), flush=True)

except PermissionError:
    verdict = "SOURCE_AUTH_BLOCKED"
except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
    if str(e) == "PROVENANCE_MARKET_FIELD":
        verdict = "PROVENANCE_FAILURE"
    else:
        transport.append({"type": type(e).__name__, "message": str(e)})
        verdict = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
except Exception as e:
    transport.append({"type": type(e).__name__, "message": str(e)})
    verdict = "DATA_FAILURE"

missing_heights: list[int] = []
malformed: list[dict] = []
outside: list[dict] = []
daily: dict[str, float] = {}
seen_hashes: dict[str, int] = {}
duplicate_hashes: list[dict] = []

if start_h is not None and end_h is not None:
    missing_heights = [h for h in range(start_h, end_h + 1) if h not in all_blocks]

for h, block in sorted(all_blocks.items()):
    try:
        if block.get("height") != h:
            raise ValueError("height_identity")
        block_id = block.get("id")
        if not isinstance(block_id, str) or len(block_id) != 64:
            raise ValueError("hash_identity")
        if block_id in seen_hashes and seen_hashes[block_id] != h:
            duplicate_hashes.append({"hash": block_id, "height_a": seen_hashes[block_id], "height_b": h})
        seen_hashes[block_id] = h
        stamp = dt.datetime.fromtimestamp(int(block["timestamp"]), tz=dt.timezone.utc)
        day = stamp.date()
        if not (START_DAY <= day <= END_DAY):
            outside.append({"height": h, "date": day.isoformat()})
            continue
        extras = block.get("extras")
        if not isinstance(extras, dict):
            raise ValueError("extras_schema")
        fees = float(extras["totalFees"])
        if not math.isfinite(fees) or fees < 0:
            raise ValueError("fees")
        daily[day.isoformat()] = daily.get(day.isoformat(), 0.0) + fees
    except Exception as e:
        malformed.append({"height": h, "reason": str(e)})

missing_days: list[str] = []
d = START_DAY
while d <= END_DAY:
    if d.isoformat() not in daily:
        missing_days.append(d.isoformat())
    d += dt.timedelta(days=1)

if verdict is None:
    if duplicate_hashes or outside or missing_heights:
        verdict = "PROVENANCE_FAILURE"
    elif malformed or missing_days:
        verdict = "DATA_FAILURE"
    elif len(daily) < 1400:
        verdict = "INSUFFICIENT_SAMPLE"
    else:
        verdict = "SOURCE_DATA_PASS"

for fn in ("raw_boundaries.bin", "raw_block_batches.bin"):
    p = OUT / fn
    if p.exists():
        raw_index.append({
            "container_file": fn,
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        })

manifest = {
    "lab": LAB,
    "gate": GATE,
    "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    "verdict": verdict,
    "source": BASE,
    "start_timestamp": START_TS,
    "end_timestamp": END_TS,
    "start_height": start_h,
    "end_height": end_h,
    "batch_width": batch_width,
    "request_count": request_count,
    "workers": MAX_WORKERS,
    "elapsed_seconds": round(time.time() - started, 3),
    "blocks": len(all_blocks),
    "unique_hashes": len(seen_hashes),
    "duplicate_hash_count": len(duplicate_hashes),
    "duplicate_hashes": duplicate_hashes[:100],
    "missing_height_count": len(missing_heights),
    "missing_height_sample": missing_heights[:100],
    "daily_observations": len(daily),
    "first_day": min(daily, default=None),
    "last_day": max(daily, default=None),
    "missing_day_count": len(missing_days),
    "missing_days": missing_days,
    "malformed_count": len(malformed),
    "malformed": malformed[:100],
    "outside_count": len(outside),
    "outside": outside[:100],
    "transport_failures": transport,
    "raw_index": raw_index,
    "firewall": {
        "btc_price_values_opened": False,
        "eth_price_values_opened": False,
        "returns_computed": False,
        "pnl_computed": False,
        "performance_statistics_computed": False,
        "access_2025": False,
        "access_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
        "discovery": False,
        "post_outcome_tuning": False,
    },
}

mb = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
(OUT / "manifest.json").write_bytes(mb)
(OUT / "manifest.sha256").write_text(hashlib.sha256(mb).hexdigest() + "  manifest.json\n")
(OUT / "verdict.txt").write_text(verdict + "\n")

summary_keys = (
    "run_id", "verdict", "start_height", "end_height", "batch_width", "request_count",
    "blocks", "unique_hashes", "missing_height_count", "daily_observations", "first_day",
    "last_day", "missing_day_count", "malformed_count", "outside_count", "elapsed_seconds",
)
print(json.dumps({k: manifest[k] for k in summary_keys}, sort_keys=True), flush=True)
print("MANIFEST_SHA256", hashlib.sha256(mb).hexdigest(), flush=True)
for x in raw_index:
    if "container_file" in x:
        print("RAW_CONTAINER", json.dumps(x, sort_keys=True), flush=True)

sys.exit(0)
