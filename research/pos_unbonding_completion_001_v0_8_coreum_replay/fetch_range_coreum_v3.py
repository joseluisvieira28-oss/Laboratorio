#!/usr/bin/env python3
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.request

BASE = "https://archive.rpc.mainnet-1.tx.org"
UA = "Laboratorio-Coreum-Replay-V08-RangeV3"
MAX_RETRIES = 4

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

def parse_utc(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

def fetch_one(h):
    url = f"{BASE}/block?height={h}"
    attempts = []
    for attempt in range(1, MAX_RETRIES + 1):
        started = utc_now()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
                status = int(r.status)
            attempts.append({
                "attempt": attempt,
                "requested_at_utc": started,
                "http_status": status,
                "error": None,
            })
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            obj = json.loads(raw)
            if obj.get("error"):
                raise RuntimeError(f"RPC error: {obj['error']}")
            res = obj["result"]
            header = res["block"]["header"]
            got_h = int(header["height"])
            if got_h != h:
                raise RuntimeError(f"height mismatch expected={h} got={got_h}")
            if header["chain_id"] != "coreum-mainnet-1":
                raise RuntimeError(f"chain-id mismatch H={h}")
            return {
                "height": h,
                "url": url,
                "raw": raw,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "raw_bytes": len(raw),
                "block_hash": res["block_id"]["hash"],
                "last_hash": header["last_block_id"]["hash"],
                "block_time": header["time"],
                "tx_count": len(res["block"]["data"].get("txs") or []),
                "evidence_count": len(res["block"].get("evidence", {}).get("evidence") or []),
                "attempts": attempts,
            }
        except Exception as exc:
            if not attempts or attempts[-1]["attempt"] != attempt:
                status = getattr(exc, "code", None) if isinstance(exc, urllib.error.HTTPError) else None
                attempts.append({
                    "attempt": attempt,
                    "requested_at_utc": started,
                    "http_status": status,
                    "error": f"{type(exc).__name__}: {exc}",
                })
            else:
                attempts[-1]["error"] = f"{type(exc).__name__}: {exc}"
            if attempt == MAX_RETRIES:
                raise RuntimeError(json.dumps({
                    "height": h,
                    "url": url,
                    "terminal_failure": True,
                    "attempts": attempts,
                }, sort_keys=True))
            time.sleep(min(2 ** (attempt - 1), 8))
    raise AssertionError("unreachable")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", required=True, type=int)
    ap.add_argument("--end", required=True, type=int)
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    applied = a.end - a.start + 1
    if a.start < 1 or a.end < a.start or applied > 10000:
        raise SystemExit("invalid range; max 10000 applied blocks")
    if a.workers < 1 or a.workers > 64:
        raise SystemExit("--workers must be 1..64")

    root = pathlib.Path(a.out)
    root.mkdir(parents=True, exist_ok=True)
    heights = list(range(a.start, a.end + 2))
    run_started = utc_now()
    wall_started = time.time()

    got = {}
    terminal_failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futures = {ex.submit(fetch_one, h): h for h in heights}
        for fut in concurrent.futures.as_completed(futures):
            h = futures[fut]
            try:
                row = fut.result()
                got[h] = row
            except Exception as exc:
                terminal_failures.append({"height": h, "error": str(exc)})

    if terminal_failures:
        failure = {
            "source": BASE,
            "chain_id": "coreum-mainnet-1",
            "run_started_at_utc": run_started,
            "run_finished_at_utc": utc_now(),
            "start_applied_height": a.start,
            "end_applied_height": a.end,
            "terminal_failures": sorted(terminal_failures, key=lambda x: x["height"]),
        }
        (root / "failure_receipt.json").write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n")
        raise SystemExit("terminal acquisition failures; see failure_receipt.json")

    files = []
    anchors = []
    transport_receipts = []
    previous_hash = None
    previous_time = None

    for h in heights:
        row = got[h]
        if previous_hash is not None and row["last_hash"] != previous_hash:
            raise RuntimeError(f"silent predecessor gap H={h}: last={row['last_hash']} want={previous_hash}")
        if previous_time is not None and parse_utc(row["block_time"]) < parse_utc(previous_time):
            raise RuntimeError(f"non-monotonic block time H={h}")

        p = root / f"block_{h}.json"
        p.write_bytes(row["raw"])
        if hashlib.sha256(p.read_bytes()).hexdigest() != row["raw_sha256"]:
            raise RuntimeError(f"post-write hash mismatch H={h}")

        files.append({
            "height": h,
            "file": p.name,
            "sha256": row["raw_sha256"],
            "bytes": row["raw_bytes"],
        })
        anchors.append({
            "height": h,
            "hash": row["block_hash"],
            "time": row["block_time"],
            "tx_count": row["tx_count"],
            "evidence_count": row["evidence_count"],
        })
        transport_receipts.append({
            "height": h,
            "url": row["url"],
            "raw_sha256": row["raw_sha256"],
            "raw_bytes": row["raw_bytes"],
            "attempts": row["attempts"],
        })
        previous_hash = row["block_hash"]
        previous_time = row["block_time"]

    elapsed = time.time() - wall_started
    out = {
        "schema": "coreum-v08-raw-range-v3",
        "source": BASE,
        "chain_id": "coreum-mainnet-1",
        "run_started_at_utc": run_started,
        "run_finished_at_utc": utc_now(),
        "start_applied_height": a.start,
        "end_applied_height": a.end,
        "next_header_height": a.end + 1,
        "contiguous_predecessor_links": True,
        "monotonic_block_time": True,
        "block_results_requested": False,
        "tx_count_total": sum(x["tx_count"] for x in anchors[:-1]),
        "evidence_count_total": sum(x["evidence_count"] for x in anchors[:-1]),
        "raw_bytes_total": sum(x["bytes"] for x in files),
        "elapsed_seconds": elapsed,
        "blocks_per_second": len(heights) / elapsed,
        "bytes_per_applied_block": sum(x["bytes"] for x in files) / applied,
        "files": files,
        "anchors": anchors,
        "transport_receipts": transport_receipts,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

    summary = {
        "schema": out["schema"],
        "chain_id": out["chain_id"],
        "start_applied_height": a.start,
        "end_applied_height": a.end,
        "next_header_height": a.end + 1,
        "contiguous_predecessor_links": True,
        "block_results_requested": False,
        "tx_count_total": out["tx_count_total"],
        "evidence_count_total": out["evidence_count_total"],
        "raw_bytes_total": out["raw_bytes_total"],
        "elapsed_seconds": elapsed,
        "blocks_per_second": out["blocks_per_second"],
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
