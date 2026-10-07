#!/usr/bin/env python3
import gzip, hashlib, json, os, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/KYVE_TRUSTLESS_SOURCE_PROBE_V045.json"
UA="CryptoLab-Unbonding-V045/1.0"
KYVE="https://api.kyve.network"
STORAGE={"1":"https://arweave.net","2":"https://arweave.net","3":"https://storage.kyve.network","4":"https://arweave.net"}

# Heights are fixed source anchors known before this probe; they are not selected from event counts.
SPECS=[
 {"chain":"osmosis","chain_id":"osmosis-1","pool":1,"height":15000000,
  "archives":[["validatus","https://rpc.archive.osmosis.validatus.com"]]},
 {"chain":"archway","chain_id":"archway-1","pool":2,"height":3554500,
  "archives":[["allthatnode","https://archway-mainnet-archive.allthatnode.com:26657"],
              ["cosmowiz_archive_ip","http://148.251.124.58:26657"],
              ["am_solutions","https://rpc-archway.theamsolutions.info"],
              ["architectnodes","https://rpc-archway.architectnodes.com"],
              ["nodersteam","https://archway-rpc.noders.services"],
              ["foundation","https://rpc.mainnet.archway.io"],
              ["kjnodes","https://archway.rpc.kjnodes.com"],
              ["validatrium","https://rpc-archway.mainnet.validatrium.club"]]},
 {"chain":"axelar","chain_id":"axelar-dojo-1","pool":3,"height":9151750,
  "archives":[["imperator","https://rpc-axelar.imperator.co"],
              ["pops","https://axelar-rpc.pops.one"],
              ["lavenderfive","https://rpc.lavenderfive.com/axelar"],
              ["polkachu","https://axelar-rpc.polkachu.com"]]},
 {"chain":"celestia","chain_id":"celestia","pool":9,"height":2500000,
  "archives":[["kjnodes","http://136.243.94.113:26667"],
              ["numia","https://public-celestia-rpc.numia.xyz"]]}
]

def get(url,timeout=30):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")[:1000]
        raise RuntimeError(f"HTTP {e.code}: {body}")

def js(raw): return json.loads(raw.decode("utf-8"))

def rpc_pair(base,h):
    out={"base":base}
    try:
        br=get(base.rstrip("/") + f"/block?height={h}",15)
        rr=get(base.rstrip("/") + f"/block_results?height={h}",15)
        bo=js(br)
        if bo.get("error"): raise RuntimeError(json.dumps(bo["error"]))
        ro=js(rr)
        if ro.get("error"): raise RuntimeError(json.dumps(ro["error"]))
        r=bo.get("result") or {}; b=r.get("block") or {}; hd=b.get("header") or {}
        if not hd.get("height"): raise RuntimeError("no block header")
        res=ro.get("result") or {}
        out.update({"status":"PASS","height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),
                    "block_hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
                    "block_sha256":hashlib.sha256(br).hexdigest(),
                    "block_results_height":int(res.get("height") or 0),
                    "block_results_sha256":hashlib.sha256(rr).hexdigest()})
    except Exception as e:
        out.update({"status":"FAIL","error":type(e).__name__+": "+str(e)[:1200]})
    return out

def kyve_pool(pool):
    raw=get(f"{KYVE}/kyve/query/v1beta1/pool/{pool}",20)
    o=js(raw); p=(o.get("pool") or {}); d=(p.get("data") or {})
    return {"id":p.get("id"),"runtime":d.get("runtime"),"start_key":d.get("start_key"),
            "current_key":d.get("current_key"),"total_bundles":d.get("total_bundles"),
            "sha256":hashlib.sha256(raw).hexdigest()}

def kyve_item(pool,h):
    meta=kyve_pool(pool)
    start=int(meta["start_key"]); current=int(meta["current_key"])
    if not (start <= h <= current):
        raise RuntimeError(f"height {h} outside KYVE pool coverage {start}..{current}")
    index=h-start
    raw=get(f"{KYVE}/kyve/v1/bundles/{pool}?index={index}",30)
    o=js(raw); bundles=o.get("finalized_bundles") or []
    if len(bundles)!=1:
        raise RuntimeError(f"expected exactly one finalized bundle, got {len(bundles)}")
    b=bundles[0]
    sid=str(b.get("storage_provider_id")); storage_id=b.get("storage_id")
    if sid not in STORAGE or not storage_id:
        raise RuntimeError(f"unsupported storage provider/id {sid} {storage_id}")
    compressed=get(STORAGE[sid].rstrip("/")+"/"+storage_id,60)
    actual=hashlib.sha256(compressed).hexdigest()
    expected=b.get("data_hash")
    if actual != expected:
        raise RuntimeError(f"bundle hash mismatch expected={expected} actual={actual}")
    if str(b.get("compression_id"))!="1":
        raise RuntimeError(f"unsupported compression_id {b.get('compression_id')}")
    data=gzip.decompress(compressed)
    items=json.loads(data.decode("utf-8"))
    target=None
    for item in items:
        if str(item.get("key"))==str(h):
            target=item; break
    if target is None: raise RuntimeError(f"height {h} not found inside verified bundle")
    val=target.get("value") or {}
    block=val.get("block") or {}; inner=block.get("block") or {}; hd=inner.get("header") or {}
    results=val.get("block_results") or {}
    if int(hd.get("height") or 0)!=h: raise RuntimeError("KYVE block height mismatch")
    if int(results.get("height") or 0)!=h: raise RuntimeError("KYVE block_results height mismatch")
    completion=[]
    for phase in ("begin_block_events","end_block_events","finalize_block_events"):
        for e in results.get(phase) or []:
            if e.get("type")=="complete_unbonding":
                completion.append({"phase":phase,"attributes":e.get("attributes") or []})
    return {"status":"PASS","pool":meta,"bundle":{"id":b.get("id"),"storage_provider_id":sid,
            "storage_id":storage_id,"from_key":b.get("from_key"),"to_key":b.get("to_key"),
            "data_hash":expected,"compressed_bytes":len(compressed),"decompressed_bytes":len(data)},
            "height":h,"time":hd.get("time"),"chain_id":hd.get("chain_id"),
            "block_hash":((block.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
            "block_results_height":int(results.get("height") or 0),
            "fixed_anchor_complete_unbonding_events":completion}

def main():
    rec={"amendment_commit":"3bdfe66c8f8597a4772ec87b68810d1b51e2eb94",
         "generated_utc":datetime.now(timezone.utc).isoformat(),
         "scope":"source-only fixed anchors; no census/materiality/market outcomes","chains":[]}
    for spec in SPECS:
        ce={"chain":spec["chain"],"chain_id":spec["chain_id"],"pool":spec["pool"],"height":spec["height"],"archives":{}}
        try:
            ce["kyve"]=kyve_item(spec["pool"],spec["height"])
        except Exception as e:
            ce["kyve"]={"status":"FAIL","error":type(e).__name__+": "+str(e)[:1500]}
        for name,base in spec["archives"]:
            ce["archives"][name]=rpc_pair(base,spec["height"])
        matches=[]
        if ce["kyve"].get("status")=="PASS":
            k=ce["kyve"]
            for name,a in ce["archives"].items():
                if a.get("status")!="PASS": continue
                m=(a.get("height")==k.get("height") and a.get("time")==k.get("time") and
                   a.get("block_hash")==k.get("block_hash") and a.get("app_hash")==k.get("app_hash") and
                   a.get("block_results_height")==k.get("block_results_height"))
                matches.append({"archive":name,"canonical_match":m})
        ce["independent_matches"]=matches
        ce["trustless_two_path_fixed_anchor_pass"]=any(x["canonical_match"] for x in matches)
        rec["chains"].append(ce)
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__":main()
