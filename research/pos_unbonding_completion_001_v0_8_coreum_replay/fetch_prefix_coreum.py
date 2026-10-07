#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib
import urllib.request

BASE = "https://archive.rpc.mainnet-1.tx.org"

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Laboratorio-Coreum-Replay-V08-Prefix"})
    with urllib.request.urlopen(req, timeout=45) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status} {url}")
        return r.read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--end", required=True, type=int)
    args = ap.parse_args()
    if args.end < 1 or args.end > 512:
        raise SystemExit("--end must be 1..512 for this bounded pilot")
    root = pathlib.Path(args.out)
    root.mkdir(parents=True, exist_ok=True)

    manifest = []
    rows = []
    previous_hash = None
    previous_time = None
    for h in range(1, args.end + 2):
        url = f"{BASE}/block?height={h}"
        raw = fetch(url)
        obj = json.loads(raw)
        if obj.get("error"):
            raise RuntimeError(f"RPC error H={h}: {obj['error']}")
        result = obj["result"]
        block = result["block"]
        header = block["header"]
        got_h = int(header["height"])
        if got_h != h:
            raise RuntimeError(f"height mismatch expected={h} got={got_h}")
        if header["chain_id"] != "coreum-mainnet-1":
            raise RuntimeError(f"chain-id mismatch H={h}: {header['chain_id']}")
        bh = result["block_id"]["hash"]
        if h > 1:
            last_hash = header["last_block_id"]["hash"]
            if last_hash != previous_hash:
                raise RuntimeError(f"silent predecessor gap H={h}: last={last_hash} want={previous_hash}")
            if previous_time is not None and header["time"] < previous_time:
                raise RuntimeError(f"non-monotonic block time H={h}")
        p = root / f"block_{h}.json"
        p.write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        manifest.append({"height": h, "file": p.name, "url": url, "sha256": sha, "bytes": len(raw)})
        rows.append({"height": h, "hash": bh, "time": header["time"], "app_hash": header["app_hash"]})
        previous_hash = bh
        previous_time = header["time"]

    out = {
        "source": BASE,
        "chain_id": "coreum-mainnet-1",
        "end_applied_height": args.end,
        "next_header_height": args.end + 1,
        "block_results_requested": False,
        "contiguous_predecessor_links": True,
        "files": manifest,
        "anchors": rows,
    }
    (root / "manifest.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "chain_id": out["chain_id"],
        "end_applied_height": args.end,
        "blocks_acquired": len(rows),
        "contiguous_predecessor_links": True,
        "block_results_requested": False,
        "first_hash": rows[0]["hash"],
        "last_hash": rows[-1]["hash"],
    }, indent=2))

if __name__ == "__main__":
    main()
