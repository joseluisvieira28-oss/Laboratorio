#!/usr/bin/env python3
import gzip, hashlib, json, os, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_8_final_kyve/V081_LAVA_CENSUS_CAPABILITY.json"
POOL=18
CHAIN_ID="lava-mainnet-1"
RPC="https://lava.tendermintrpc.lava.build"
KYVE="https://api.kyve.network"
STORAGE={"1":"https://arweave.net","2":"https://arweave.net","3":"https://storage.kyve.network","4":"https://arweave.net"}
BOUNDARY="2025-01-01T00:00:00Z"
FREEZE_COMMIT="cec145e2f9040198f95f88f1532ec783646544c0"
UA="CryptoLab-Unbonding-V081/1.0"

def req(url, timeout=35):
    q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(q,timeout=timeout) as r:
        return r.read()

def jd(url,timeout=35):
    return json.loads(req(url,timeout).decode("utf-8"))

def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z","+00:00"))

def pool_meta():
    raw=req(f"{KYVE}/kyve/query/v1beta1/pool/{POOL}")
    o=json.loads(raw)
    p=o["pool"]; d=p["data"]
    return {
      "pool_id":int(p["id"]),
      "runtime":d["runtime"],
      "start_key":int(d["start_key"]),
      "current_key":int(d["current_key"]),
      "total_bundles":str(d.get("total_bundles")),
      "response_sha256":hashlib.sha256(raw).hexdigest()
    }

def rpc_block(h):
    raw=req(f"{RPC}/block?height={h}",25)
    o=json.loads(raw); r=o["result"]; b=r["block"]; hd=b["header"]
    return {"height":int(hd["height"]),"chain_id":hd["chain_id"],"time":hd["time"],
            "hash":r["block_id"]["hash"],"app_hash":hd["app_hash"],
            "raw_sha256":hashlib.sha256(raw).hexdigest()}

def rpc_results_meta(h):
    raw=req(f"{RPC}/block_results?height={h}",25)
    o=json.loads(raw); r=o["result"]
    return {"height":int(r["height"]),"raw_sha256":hashlib.sha256(raw).hexdigest(),
            "bytes":len(raw)}

def kyve_height(h, meta):
    if not(meta["start_key"] <= h <= meta["current_key"]):
        raise RuntimeError(f"height {h} outside KYVE pool coverage")
    idx=h-meta["start_key"]
    bo=jd(f"{KYVE}/kyve/v1/bundles/{POOL}?index={idx}",30)
    bundles=bo.get("finalized_bundles") or []
    if len(bundles)!=1:
        raise RuntimeError(f"bundle lookup H={h} returned {len(bundles)} bundles")
    b=bundles[0]; sp=str(b["storage_provider_id"]); sid=b["storage_id"]
    if sp not in STORAGE: raise RuntimeError(f"unsupported storage provider {sp}")
    comp=req(STORAGE[sp].rstrip("/")+"/"+sid,75)
    got=hashlib.sha256(comp).hexdigest()
    if got != b["data_hash"]: raise RuntimeError(f"bundle hash mismatch H={h}")
    if str(b.get("compression_id"))!="1": raise RuntimeError("unsupported compression")
    items=json.loads(gzip.decompress(comp).decode("utf-8"))
    item=next((x for x in items if int(x["key"])==h),None)
    if item is None: raise RuntimeError(f"H={h} missing from verified bundle")
    v=item["value"]; rb=v["block"]; rr=v["block_results"]; hd=rb["block"]["header"]
    if int(hd["height"])!=h or int(rr["height"])!=h: raise RuntimeError(f"height mismatch H={h}")
    return {
      "height":h,"chain_id":hd["chain_id"],"time":hd["time"],
      "hash":rb["block_id"]["hash"],"app_hash":hd["app_hash"],
      "block_results_height":int(rr["height"]),
      "bundle_id":int(b["id"]),"from_key":int(b["from_key"]),"to_key":int(b["to_key"]),
      "storage_provider_id":sp,"storage_id":sid,"data_hash":b["data_hash"],
      "compressed_sha256":got,"compressed_bytes":len(comp)
    }

def find_first_at_or_after(meta, target):
    lo=meta["start_key"]; hi=meta["current_key"]
    if parse_ts(rpc_block(lo)["time"]) >= target: return lo
    if parse_ts(rpc_block(hi)["time"]) < target:
        raise RuntimeError("pool current_key predates boundary")
    while lo+1<hi:
        mid=(lo+hi)//2
        t=parse_ts(rpc_block(mid)["time"])
        if t < target: lo=mid
        else: hi=mid
    return hi

def main():
    meta=pool_meta()
    target=parse_ts(BOUNDARY)
    first_2025=find_first_at_or_after(meta,target)
    end_2024=first_2025-1
    midpoint=(meta["start_key"]+end_2024)//2
    checkpoints=sorted(set([meta["start_key"],midpoint,end_2024,first_2025]))
    rows=[]
    all_match=True
    for h in checkpoints:
        k=kyve_height(h,meta)
        r=rpc_block(h); rr=rpc_results_meta(h)
        match=(
          k["height"]==r["height"]==rr["height"] and
          k["chain_id"]==r["chain_id"]==CHAIN_ID and
          k["time"]==r["time"] and k["hash"]==r["hash"] and
          k["app_hash"]==r["app_hash"] and k["block_results_height"]==rr["height"]
        )
        all_match &= match
        rows.append({"height":h,"kyve":k,"rpc":r,"rpc_block_results":rr,"canonical_match":match})
    end_t=parse_ts(rows[-2]["rpc"]["time"])
    first_t=parse_ts(rows[-1]["rpc"]["time"])
    boundary_bracket=(end_t < target <= first_t)
    pass_flag=bool(
      meta["runtime"]=="@kyvejs/tendermint" and meta["start_key"]==1 and
      meta["current_key"]>=first_2025 and boundary_bracket and all_match
    )
    out={
      "freeze_commit":FREEZE_COMMIT,
      "generated_utc":datetime.now(timezone.utc).isoformat(),
      "chain_id":CHAIN_ID,"kyve_pool":meta,"independent_rpc":RPC,
      "boundary_utc":BOUNDARY,"end_2024_height":end_2024,
      "first_2025_height":first_2025,"boundary_bracket_pass":boundary_bracket,
      "checkpoints":rows,
      "integer_height_enumeration_domain":{"from":1,"to":end_2024,"step":1},
      "complete_enumeration_algorithm":"For each integer H in [1,end_2024], resolve the finalized KYVE bundle by pool-key index, verify compressed SHA-256 against finalized data_hash, extract exact key H, require block.height == block_results.height == H; optionally reconcile canonical header metadata against the independently qualified archive RPC.",
      "source_route_complete_enumeration_capable":pass_flag,
      "event_counts_opened":False,"event_payload_fields_inspected":False,
      "market_values_opened_by_this_probe":False,"market_outcomes_opened":False
    }
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    if not pass_flag: raise SystemExit(2)

if __name__=="__main__": main()
