#!/usr/bin/env python3
import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import time
import urllib.request

BASE = "https://archive.rpc.mainnet-1.tx.org"

def fetch_one(h):
    url = f"{BASE}/block?height={h}"
    req = urllib.request.Request(url, headers={"User-Agent": "Laboratorio-Coreum-Replay-V08-RangeV2"})
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
        status = r.status
    if status != 200:
        raise RuntimeError(f"HTTP {status} H={h}")
    obj = json.loads(raw)
    if obj.get("error"):
        raise RuntimeError(f"RPC error H={h}: {obj['error']}")
    res = obj["result"]
    header = res["block"]["header"]
    if int(header["height"]) != h:
        raise RuntimeError(f"height mismatch expected={h} got={header['height']}")
    if header["chain_id"] != "coreum-mainnet-1":
        raise RuntimeError(f"chain-id mismatch H={h}")
    return {
        "height": h,
        "raw": raw,
        "hash": res["block_id"]["hash"],
        "last_hash": header["last_block_id"]["hash"],
        "time": header["time"],
        "tx_count": len(res["block"]["data"].get("txs") or []),
        "evidence_count": len(res["block"].get("evidence", {}).get("evidence") or []),
    }

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

    root = pathlib.Path(a.out)
    root.mkdir(parents=True, exist_ok=True)
    heights = list(range(a.start, a.end + 2))
    started = time.time()

    got = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futures = {ex.submit(fetch_one, h): h for h in heights}
        for fut in concurrent.futures.as_completed(futures):
            row = fut.result()
            got[row["height"]] = row

    files = []
    anchors = []
    prev_hash = None
    for h in heights:
        row = got[h]
        if prev_hash is not None and row["last_hash"] != prev_hash:
            raise RuntimeError(f"silent predecessor gap H={h}")
        p = root / f"block_{h}.json"
        p.write_bytes(row["raw"])
        files.append({
            "height": h,
            "file": p.name,
            "sha256": hashlib.sha256(row["raw"]).hexdigest(),
            "bytes": len(row["raw"]),
        })
        anchors.append({
            "height": h,
            "hash": row["hash"],
            "time": row["time"],
            "tx_count": row["tx_count"],
            "evidence_count": row["evidence_count"],
        })
        prev_hash = row["hash"]

    elapsed = time.time() - started
    out = {
        "source": BASE,
        "chain_id": "coreum-mainnet-1",
        "start_applied_height": a.start,
        "end_applied_height": a.end,
        "next_header_height": a.end + 1,
        "contiguous_predecessor_links": True,
        "block_results_requested": False,
        "tx_count_total": sum(x["tx_count"] for x in anchors[:-1]),
        "evidence_count_total": sum(x["evidence_count"] for x in anchors[:-1]),
        "raw_bytes_total": sum(x["bytes"] for x in files),
        "elapsed_seconds": elapsed,
        "blocks_per_second": len(heights) / elapsed,
        "bytes_per_applied_block": sum(x["bytes"] for x in files) / applied,
        "files": files,
        "anchors": anchors,
    }
    (root / "manifest.json").write_text(json.dumps(out, indent=2) + "\n")
    summary = {k: out[k] for k in (
        "chain_id", "start_applied_height", "end_applied_height", "next_header_height",
        "contiguous_predecessor_links", "block_results_requested", "tx_count_total",
        "evidence_count_total", "raw_bytes_total", "elapsed_seconds",
        "blocks_per_second", "bytes_per_applied_block"
    )}
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
