#!/usr/bin/env python3
import concurrent.futures, gzip, hashlib, json, os, ssl, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_8_final_kyve/V08_FINAL_KYVE_QUALIFICATION.json"
UA="CryptoLab-Unbonding-V08/1.0"
KYVE="https://api.kyve.network"
STORAGE={"1":"https://arweave.net","2":"https://arweave.net","3":"https://storage.kyve.network","4":"https://arweave.net"}
CHAIN_REGISTRY_COMMIT="c9d65b60bc0229c06d49ded805ba528f316bd9c7"
SOURCE_REGISTRY_COMMIT="7cb8e3abd7fb5788b299c270380f1ea36715e2a0"
FREEZE_DOCUMENT_BLOB_SHA="eaf6e5e211c7302561f6d2ba4437c06a52a06d1a"\nPARENT_V07_CLOSEOUT_COMMIT="f1a5a563054563f16605c468fd14dc93d4a71334"

# Archway/Axelar were already tested under the immediately preceding V0.7 freeze and
# are inherited as frozen failures. V0.8 tests the previously untested members of
# the prospectively frozen KYVE universe in their fixed order.
SPECS=[
 {"chain":"andromeda","chain_id":"andromeda-1","registry":"andromeda","pool":14,
  "anchors":[2410000,3632075,4854150]},
 {"chain":"lava","chain_id":"lava-mainnet-1","registry":"lava","pool":18,
  "anchors":[1,451000,888500]},
 {"chain":"source","chain_id":"source-1","registry":"source","pool":11,
  "anchors":[1,2000000,4000000]},
 {"chain":"xion","chain_id":"xion-mainnet-1","registry":"xion","pool":16,
  "anchors":[1,100000,200000]}
]

def req(url,timeout=25,insecure=False):
    ctx=ssl._create_unverified_context() if insecure and url.startswith("https://") else None
    r=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(r,timeout=timeout,context=ctx) as x:return x.read()
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")[:1000]
        raise RuntimeError(f"HTTP {e.code}: {body}")

def j(raw):return json.loads(raw.decode("utf-8"))

def registry_chain(name):
    url=f"https://raw.githubusercontent.com/cosmos/chain-registry/{CHAIN_REGISTRY_COMMIT}/{name}/chain.json"
    raw=req(url,20); o=j(raw)
    rpcs=[x["address"].rstrip("/") for x in ((o.get("apis") or {}).get("rpc") or []) if x.get("address")]
    staking=((o.get("staking") or {}).get("staking_tokens") or [])
    return {"sha256":hashlib.sha256(raw).hexdigest(),"chain_id":o.get("chain_id"),
            "status":o.get("status"),"network_type":o.get("network_type"),
            "staking_tokens":staking,"rpcs":rpcs}

def pool_meta(pool):
    raw=req(f"{KYVE}/kyve/query/v1beta1/pool/{pool}",20); o=j(raw); p=o.get("pool") or {}; d=p.get("data") or {}
    return {"id":str(p.get("id")),"runtime":d.get("runtime"),"start_key":int(d.get("start_key") or 0),
            "current_key":int(d.get("current_key") or 0),"total_bundles":str(d.get("total_bundles")),
            "sha256":hashlib.sha256(raw).hexdigest()}

def kyve_height(pool,h,meta):
    if not(meta["start_key"]<=h<=meta["current_key"]): raise RuntimeError(f"height {h} outside pool")
    idx=h-meta["start_key"]
    raw=req(f"{KYVE}/kyve/v1/bundles/{pool}?index={idx}",30); o=j(raw); bundles=o.get("finalized_bundles") or []
    if len(bundles)!=1: raise RuntimeError(f"bundle lookup returned {len(bundles)}")
    b=bundles[0]; sp=str(b.get("storage_provider_id")); sid=b.get("storage_id")
    if sp not in STORAGE or not sid: raise RuntimeError("unsupported storage")
    comp=req(STORAGE[sp].rstrip("/")+"/"+sid,60)
    got=hashlib.sha256(comp).hexdigest()
    if got!=b.get("data_hash"): raise RuntimeError(f"data_hash mismatch {got} != {b.get('data_hash')}")
    if str(b.get("compression_id"))!="1": raise RuntimeError("unsupported compression")
    items=json.loads(gzip.decompress(comp).decode("utf-8"))
    item=next((x for x in items if str(x.get("key"))==str(h)),None)
    if item is None: raise RuntimeError("height absent from verified bundle")
    v=item.get("value") or {}; block=v.get("block") or {}; inner=block.get("block") or {}; hd=inner.get("header") or {}
    res=v.get("block_results") or {}
    if int(hd.get("height") or 0)!=h or int(res.get("height") or 0)!=h: raise RuntimeError("KYVE height mismatch")
    return {"height":h,"time":hd.get("time"),"chain_id":hd.get("chain_id"),
            "hash":((block.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
            "block_results_height":int(res.get("height") or 0),
            "bundle_id":str(b.get("id")),"from_key":str(b.get("from_key")),"to_key":str(b.get("to_key")),
            "storage_provider_id":sp,"storage_id":sid,"data_hash":b.get("data_hash"),
            "compressed_bytes":len(comp)}

def rpc_one(base,h,insecure=False):
    br=req(base.rstrip("/") + f"/block?height={h}",12,insecure)
    rr=req(base.rstrip("/") + f"/block_results?height={h}",12,insecure)
    bo=j(br); ro=j(rr)
    if bo.get("error"):raise RuntimeError(json.dumps(bo["error"]))
    if ro.get("error"):raise RuntimeError(json.dumps(ro["error"]))
    r=bo.get("result") or {}; b=r.get("block") or {}; hd=b.get("header") or {}; res=ro.get("result") or {}
    if not hd.get("height"):raise RuntimeError("no block header")
    return {"height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),
            "hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
            "block_results_height":int(res.get("height") or 0),
            "block_sha256":hashlib.sha256(br).hexdigest(),
            "block_results_sha256":hashlib.sha256(rr).hexdigest()}

def probe_provider(base,chain_id,anchors,kyve):
    out={"base":base,"anchors":{},"transport":"verified_tls_or_http"}
    modes=[False]
    if base.startswith("https://"):modes.append(True)
    last=None
    for insecure in modes:
        try:
            vals={str(h):rpc_one(base,h,insecure) for h in anchors}
            if any(x["chain_id"]!=chain_id for x in vals.values()):raise RuntimeError("wrong chain")
            match=True
            for h in anchors:
                a=vals[str(h)]; k=kyve[str(h)]
                match=match and all([
                    a["height"]==k["height"], a["time"]==k["time"], a["hash"]==k["hash"],
                    a["app_hash"]==k["app_hash"], a["block_results_height"]==k["block_results_height"]
                ])
            out.update({"anchors":vals,"status":"PASS","tls_verification_disabled":bool(insecure),
                        "canonical_all_anchor_match":bool(match)})
            return out
        except Exception as e:
            last=type(e).__name__+": "+str(e)[:1000]
    out.update({"status":"FAIL","error":last,"canonical_all_anchor_match":False})
    return out

def inherited_v07_failures():
    return [
      {"chain":"archway","chain_id":"archway-1","status":"INHERITED_V07_FAIL",
       "reason":"KYVE anchors passed; no independent public/free RPC returned block + block_results at all frozen anchors with canonical reconciliation."},
      {"chain":"axelar","chain_id":"axelar-dojo-1","status":"INHERITED_V07_FAIL",
       "reason":"KYVE anchors passed; no independent public/free RPC returned block + block_results at all frozen anchors with canonical reconciliation."}
    ]

def main():
    rec={"freeze_document_blob_sha":FREEZE_DOCUMENT_BLOB_SHA,"parent_v07_closeout_commit":PARENT_V07_CLOSEOUT_COMMIT,"source_registry_commit":SOURCE_REGISTRY_COMMIT,
         "chain_registry_commit":CHAIN_REGISTRY_COMMIT,"generated_utc":datetime.now(timezone.utc).isoformat(),
         "event_counts_opened":False,"market_values_opened":False,"market_outcomes_opened":False,
         "candidate_order":["andromeda","archway","axelar","lava","source","xion"],
         "inherited_v07":inherited_v07_failures(),"results":[],"selected_source_candidate":None}

    # Fixed order: Andromeda first; Archway/Axelar are already immutable failures; then Lava/Source/Xion.
    for spec in SPECS:
        ce={"chain":spec["chain"],"chain_id":spec["chain_id"],"pool":spec["pool"],"anchors":spec["anchors"]}
        try:
            reg=registry_chain(spec["registry"]); ce["registry"]=reg
            if reg["chain_id"]!=spec["chain_id"]: raise RuntimeError(f"chain-registry chain_id mismatch {reg['chain_id']}")
            ce["native_staking_metadata_present"]=bool(reg["staking_tokens"])
        except Exception as e:
            ce["registry_status"]="FAIL";ce["registry_error"]=type(e).__name__+": "+str(e)[:1200]
            rec["results"].append(ce)
            continue
        try:
            meta=pool_meta(spec["pool"]); ce["kyve_pool"]=meta
            ky={str(h):kyve_height(spec["pool"],h,meta) for h in spec["anchors"]}
            if any(x["chain_id"]!=spec["chain_id"] for x in ky.values()):raise RuntimeError("KYVE wrong chain")
            ce["kyve"]=ky;ce["kyve_status"]="PASS"
        except Exception as e:
            ce["kyve_status"]="FAIL";ce["kyve_error"]=type(e).__name__+": "+str(e)[:1200]
            rec["results"].append(ce)
            continue
        endpoints=list(dict.fromkeys(reg["rpcs"]))
        providers={}
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futs={ex.submit(probe_provider,b,spec["chain_id"],spec["anchors"],ky):b for b in endpoints}
            for f in concurrent.futures.as_completed(futs):
                b=futs[f]
                try:providers[b]=f.result()
                except Exception as e:providers[b]={"base":b,"status":"FAIL","error":str(e),"canonical_all_anchor_match":False}
        ce["providers"]=providers
        ce["canonical_independent_matches"]=[b for b,p in providers.items() if p.get("canonical_all_anchor_match")]
        ce["two_path_multi_anchor_pass"]=len(ce["canonical_independent_matches"])>=1
        rec["results"].append(ce)
        if spec["chain"]=="andromeda" and ce["two_path_multi_anchor_pass"]:
            rec["selected_source_candidate"]="andromeda"; break
        if spec["chain"] in ("lava","source","xion") and ce["two_path_multi_anchor_pass"]:
            rec["selected_source_candidate"]=spec["chain"]; break

    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__": main()
