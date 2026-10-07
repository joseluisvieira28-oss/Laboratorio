#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, time, urllib.request

BASE = "https://archive.rpc.mainnet-1.tx.org"
HEIGHTS = (1, 2, 5_000_000, 5_000_001, 10_000_000, 10_000_001, 15_000_000, 15_000_001)

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Laboratorio-Coreum-Replay-V08"})
    with urllib.request.urlopen(req, timeout=45) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status} {url}")
        return r.read()

def save(root: pathlib.Path, name: str, data: bytes, manifest: list[dict]):
    p = root / name
    p.write_bytes(data)
    manifest.append({
        "file": name,
        "url": None,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })

def get_and_save(root, name, url, manifest):
    data = fetch(url)
    p = root / name
    p.write_bytes(data)
    manifest.append({
        "file": name,
        "url": url,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })
    return json.loads(data)

def fetch_validators(root, height, manifest):
    vals = []
    page = 1
    total = None
    block_height = None
    while total is None or len(vals) < total:
        url = f"{BASE}/validators?height={height}&per_page=100&page={page}"
        obj = get_and_save(root, f"validators_{height}_p{page}.json", url, manifest)
        if obj.get("error"):
            raise RuntimeError(f"validator RPC error H={height} p={page}: {obj['error']}")
        res = obj["result"]
        if block_height is None:
            block_height = res["block_height"]
        page_vals = res.get("validators") or []
        vals.extend(page_vals)
        total = int(res["total"])
        if not page_vals and len(vals) < total:
            raise RuntimeError(f"silent validator pagination gap H={height} p={page} {len(vals)}/{total}")
        page += 1
    merged = {
        "jsonrpc": "2.0",
        "id": -1,
        "result": {
            "block_height": str(block_height),
            "validators": vals,
            "count": str(len(vals)),
            "total": str(total),
        },
    }
    raw = (json.dumps(merged, separators=(",", ":")) + "\n").encode()
    save(root, f"validators_{height}_merged.json", raw, manifest)
    return len(vals)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = pathlib.Path(args.out)
    root.mkdir(parents=True, exist_ok=True)
    manifest = []
    summary = {"source": BASE, "heights": {}, "block_results_requested": False}
    for h in HEIGHTS:
        block = get_and_save(root, f"block_{h}.json", f"{BASE}/block?height={h}", manifest)
        if block.get("error"):
            raise RuntimeError(f"block RPC error H={h}: {block['error']}")
        r = block["result"]
        summary["heights"][str(h)] = {
            "hash": r["block_id"]["hash"],
            "chain_id": r["block"]["header"]["chain_id"],
            "time": r["block"]["header"]["time"],
            "app_hash": r["block"]["header"]["app_hash"],
        }
    for h in (1, 5_000_000, 10_000_000, 15_000_000):
        commit = get_and_save(root, f"commit_{h}.json", f"{BASE}/commit?height={h}", manifest)
        if commit.get("error"):
            raise RuntimeError(f"commit RPC error H={h}: {commit['error']}")
        summary["heights"][str(h)]["validator_count"] = fetch_validators(root, h, manifest)
        summary["heights"][str(h)]["next_validator_count"] = fetch_validators(root, h + 1, manifest)
    manifest_obj = {
        "source": BASE,
        "created_unix": int(time.time()),
        "block_results_requested": False,
        "files": manifest,
    }
    (root / "manifest.json").write_text(json.dumps(manifest_obj, indent=2) + "\n")
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
