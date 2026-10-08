#!/usr/bin/env python3
import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import urllib.request

BASE = "https://archive.rpc.mainnet-1.tx.org"

def fetch_one(h: int):
    url = f"{BASE}/block?height={h}"
    req = urllib.request.Request(url, headers={"User-Agent": "Laboratorio-Coreum-Replay-V08-Range"})
    with urllib.request.urlopen(req, timeout=45) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status} H={h}")
        raw = r.read()
    obj = json.loads(raw)
    if obj.get("error"):
        raise RuntimeError(f"RPC error H={h}: {obj['error']}")
    res = obj["result"]
    header = res["block"]["header"]
    if int(header["height"]) != h:
        raise RuntimeError(f"height mismatch expected={h} got={header['height']}")
    if header["chain_id"] != "coreum-mainnet-1":
        raise RuntimeError(f"chain-id mismatch H={h}")
    return h, raw, res["block_id"]["hash"], header["last_block_id"]["hash"], header["time"], len(res["block"]["data"].get("txs") or []), len(res["block"].get("evidence", {}).get("evidence") or [])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", required=True, type=int)
    ap.add_argument("--end", required=True, type=int)
    ap.add_argument("--workers", type=int, default=16)
    a=ap.parse_args()
    if a.start < 1 or a.end < a.start or a.end-a.start+1 > 8192:
        raise SystemExit("invalid/bounded range; max 8192 applied blocks")
    root=pathlib.Path(a.out); root.mkdir(parents=True, exist_ok=True)
    heights=list(range(a.start, a.end+2))
    got={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs={ex.submit(fetch_one,h):h for h in heights}
        for fut in concurrent.futures.as_completed(futs):
            h,raw,bh,last,t,txc,evc=fut.result()
            got[h]=(raw,bh,last,t,txc,evc)
    rows=[]; files=[]
    prev_hash=None
    for h in heights:
        raw,bh,last,t,txc,evc=got[h]
        if prev_hash is not None and last != prev_hash:
            raise RuntimeError(f"silent predecessor gap H={h}: last={last} want={prev_hash}")
        p=root/f"block_{h}.json"; p.write_bytes(raw)
        files.append({"height":h,"file":p.name,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
        rows.append({"height":h,"hash":bh,"time":t,"tx_count":txc,"evidence_count":evc})
        prev_hash=bh
    out={
        "source":BASE,
        "chain_id":"coreum-mainnet-1",
        "start_applied_height":a.start,
        "end_applied_height":a.end,
        "next_header_height":a.end+1,
        "contiguous_predecessor_links":True,
        "block_results_requested":False,
        "tx_count_total":sum(x["tx_count"] for x in rows[:-1]),
        "evidence_count_total":sum(x["evidence_count"] for x in rows[:-1]),
        "files":files,
        "anchors":rows,
    }
    (root/"manifest.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({k:out[k] for k in (
        "chain_id","start_applied_height","end_applied_height","next_header_height",
        "contiguous_predecessor_links","block_results_requested","tx_count_total","evidence_count_total"
    )},indent=2))

if __name__=="__main__":
    main()
