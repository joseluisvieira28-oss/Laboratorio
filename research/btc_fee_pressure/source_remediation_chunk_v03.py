#!/usr/bin/env python3
"""BTC-FEE-PRESSURE-001 V0.3 deterministic source shard. No market outcomes."""
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
START_TS = 1609459200
END_TS = 1735689599
SHARD_COUNT = 4
SHARD_INDEX = int(os.environ["BFP_SHARD_INDEX"])
if SHARD_INDEX not in range(SHARD_COUNT):
    raise SystemExit("invalid BFP_SHARD_INDEX")
OUT = pathlib.Path(os.environ.get("BFP_OUT", f"btc_fee_pressure_v03_chunk_{SHARD_INDEX}"))
OUT.mkdir(parents=True, exist_ok=True)
HEADERS = {"Accept": "application/json", "User-Agent": "Laboratorio-Research-SourceGate/0.3"}
transport = []
raw_index = []

def get(url: str, retries: int = 4):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.status, dict(r.headers.items()), r.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 429 or e.code >= 500:
                last = (e.code, dict(e.headers.items()), body)
                time.sleep(min(8, 2 ** attempt))
                continue
            return e.code, dict(e.headers.items()), body
        except Exception as e:
            last = e
            time.sleep(min(8, 2 ** attempt))
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
        return obj, body, headers, url
    if isinstance(obj, dict) and isinstance(obj.get("height"), int):
        return obj["height"], body, headers, url
    raise ValueError(f"height_schema:{obj!r}")

def deterministic_slice(items, index, count):
    q, r = divmod(len(items), count)
    lo = index * q + min(index, r)
    hi = lo + q + (1 if index < r else 0)
    return items[lo:hi]

verdict = None
start_h = end_h = None
request_heights = []
assigned = []
all_blocks = {}
try:
    start_h, start_body, start_headers, start_url = height_at(START_TS)
    end_h, end_body, end_headers, end_url = height_at(END_TS)
    if not (0 < start_h <= end_h):
        raise ValueError("height_order")

    with (OUT / "raw_boundaries.bin").open("wb") as f:
        for url, body in ((start_url, start_body), (end_url, end_body)):
            ub = url.encode()
            offset = f.tell()
            f.write(struct.pack(">II", len(ub), len(body)))
            f.write(ub)
            f.write(body)
            raw_index.append({
                "url": url, "container": "raw_boundaries.bin", "offset": offset,
                "body_bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "status": 200
            })

    request_heights = list(range(end_h, start_h - 1, -10))
    assigned = deterministic_slice(request_heights, SHARD_INDEX, SHARD_COUNT)
    if not assigned:
        raise ValueError("empty_shard")

    for h in (end_h, (start_h + end_h) // 2, start_h):
        url = f"{BASE}/api/v1/blocks/{h}"
        status, headers, body = get(url)
        if status in (401, 403):
            verdict = "SOURCE_AUTH_BLOCKED"
            break
        if status != 200:
            raise RuntimeError(f"probe_http_{status}")
        low = body.lower()
        if any(x in low for x in (b'\"usd\"', b'\"price\"', b'\"market_price\"')):
            verdict = "PROVENANCE_FAILURE"
            break
        arr = json.loads(body)
        if not isinstance(arr, list) or not arr:
            verdict = "DATA_FAILURE"
            break
        target = next((b for b in arr if b.get("height") == h), None)
        if (
            not target
            or not isinstance(target.get("id"), str)
            or not isinstance(target.get("timestamp"), int)
            or not isinstance(target.get("extras"), dict)
            or not isinstance(target["extras"].get("totalFees"), (int, float))
        ):
            verdict = "DATA_FAILURE"
            break

    if verdict is None:
        def fetch_batch(h):
            url = f"{BASE}/api/v1/blocks/{h}"
            status, headers, body = get(url)
            return h, url, status, headers, body

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            for item in ex.map(fetch_batch, assigned):
                results.append(item)

        with (OUT / f"raw_block_batches_shard_{SHARD_INDEX}.bin").open("wb") as f:
            for h, url, status, headers, body in results:
                if status in (401, 403):
                    verdict = "SOURCE_AUTH_BLOCKED"
                    break
                if status != 200:
                    transport.append({"height": h, "status": status})
                    verdict = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
                    break
                if any(x in body.lower() for x in (b'\"usd\"', b'\"price\"', b'\"market_price\"')):
                    verdict = "PROVENANCE_FAILURE"
                    break
                ub = url.encode()
                offset = f.tell()
                f.write(struct.pack(">II", len(ub), len(body)))
                f.write(ub)
                f.write(body)
                raw_index.append({
                    "url": url, "container": f"raw_block_batches_shard_{SHARD_INDEX}.bin",
                    "offset": offset, "body_bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(), "status": status
                })
                arr = json.loads(body)
                if not isinstance(arr, list):
                    verdict = "DATA_FAILURE"
                    break
                for b in arr:
                    h2 = b.get("height")
                    if isinstance(h2, int) and start_h <= h2 <= end_h:
                        if h2 in all_blocks and all_blocks[h2].get("id") != b.get("id"):
                            verdict = "PROVENANCE_FAILURE"
                            break
                        all_blocks[h2] = b
                if verdict:
                    break
except PermissionError:
    verdict = "SOURCE_AUTH_BLOCKED"
except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
    transport.append({"type": type(e).__name__, "message": str(e)})
    verdict = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
except Exception as e:
    transport.append({"type": type(e).__name__, "message": str(e)})
    verdict = "DATA_FAILURE"

malformed = []
block_rows = []
if verdict is None:
    for h, b in sorted(all_blocks.items()):
        try:
            if b.get("height") != h or not isinstance(b.get("id"), str) or len(b["id"]) != 64:
                raise ValueError("identity")
            ts = int(b["timestamp"])
            fees = float(b["extras"]["totalFees"])
            if not math.isfinite(fees) or fees < 0:
                raise ValueError("fees")
            block_rows.append({"height": h, "id": b["id"], "timestamp": ts, "totalFees": fees})
        except Exception as e:
            malformed.append({"height": h, "reason": str(e)})
    verdict = "DATA_FAILURE" if malformed else "CHUNK_PASS"

(OUT / "requested_heights.json").write_text(json.dumps(assigned, separators=(",", ":")) + "\n")
with (OUT / "block_index.jsonl").open("w") as f:
    for row in block_rows:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

for fn in ("raw_boundaries.bin", f"raw_block_batches_shard_{SHARD_INDEX}.bin", "requested_heights.json", "block_index.jsonl"):
    p = OUT / fn
    if p.exists():
        raw_index.append({"container_file": fn, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})

manifest = {
    "lab": LAB, "gate": GATE, "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    "shard_index": SHARD_INDEX, "shard_count": SHARD_COUNT, "verdict": verdict,
    "source": BASE, "start_timestamp": START_TS, "end_timestamp": END_TS,
    "start_height": start_h, "end_height": end_h,
    "global_request_count": len(request_heights), "assigned_request_count": len(assigned),
    "assigned_first": assigned[0] if assigned else None, "assigned_last": assigned[-1] if assigned else None,
    "blocks_indexed": len(block_rows), "malformed_count": len(malformed), "malformed": malformed[:100],
    "transport_failures": transport, "raw_index": raw_index,
    "firewall": {
        "btc_price_values_opened": False, "eth_price_values_opened": False,
        "returns_computed": False, "pnl_computed": False,
        "performance_statistics_computed": False, "access_2025": False,
        "access_2026": False, "live_trading": False,
        "exchange_mutation": False, "discovery": False
    }
}
mb = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
(OUT / "chunk_manifest.json").write_bytes(mb)
(OUT / "chunk_manifest.sha256").write_text(hashlib.sha256(mb).hexdigest() + "  chunk_manifest.json\n")
(OUT / "verdict.txt").write_text(verdict + "\n")
print(json.dumps({
    "run_id": manifest["run_id"], "shard_index": SHARD_INDEX, "verdict": verdict,
    "start_height": start_h, "end_height": end_h,
    "assigned_request_count": len(assigned), "blocks_indexed": len(block_rows)
}, sort_keys=True))
print("CHUNK_MANIFEST_SHA256", hashlib.sha256(mb).hexdigest())
sys.exit(0)
