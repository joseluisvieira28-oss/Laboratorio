#!/usr/bin/env python3
import concurrent.futures, gzip, hashlib, json, os, ssl, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_7_kyve/V07_FIFTH_CHAIN_QUALIFICATION.json"
UA="CryptoLab-Unbonding-V07/1.0"
KYVE="https://api.kyve.network"
STORAGE={"1":"https://arweave.net","2":"https://arweave.net","3":"https://storage.kyve.network","4":"https://arweave.net"}
CHAIN_REGISTRY_COMMIT="c9d65b60bc0229c06d49ded805ba528f316bd9c7"

SPECS=[
 {"chain":"archway","chain_id":"archway-1","registry":"archway","pool":2,
  "anchors":[1215711,3554500,6836450],
  "extras":["https://archway-mainnet-archive.allthatnode.com:26657","https://rpc-archway.theamsolutions.info",
            "https://archway-mainnet.rpc.l0vd.com","https://archway-rpc.openbitlab.com"]},
 {"chain":"axelar","chain_id":"axelar-dojo-1","registry":"axelar","pool":3,
  "anchors":[9151750,14231100,15890800],
  "extras":["https://public.1rpc.io/axelar-rpc","https://rpc.axelar.posthuman.digital",
            "https://axelar-rpc.synergynodes.com","https://rpc.axelar.aknodes.net",
            "https://axelar-rpc.publicnode.com"]}
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

def registry_rpcs(name):
    url=f"https://raw.githubusercontent.com/cosmos/chain-registry/{CHAIN_REGISTRY_COMMIT}/{name}/chain.json"
    o=j(req(url,20))
    return [x["address"].rstrip("/") for x in ((o.get("apis") or {}).get("rpc") or []) if x.get("address")]

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
    br=req(base.rstrip("/")+f"/block?height={h}",12,insecure)
    rr=req(base.rstrip("/")+f"/block_results?height={h}",12,insecure)
    bo=j(br); ro=j(rr)
    if bo.get("error"):raise RuntimeError(json.dumps(bo["error"]))
    if ro.get("error"):raise RuntimeError(json.dumps(ro["error"]))
    r=bo.get("result") or {}; b=r.get("block") or {}; hd=b.get("header") or {}; res=ro.get("result") or {}
    if not hd.get("height"):raise RuntimeError("no block header")
    return {"height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),
            "hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
            "block_results_height":int(res.get("height") or 0),
            "block_sha256":hashlib.sha256(br).hexdigest(),"block_results_sha256":hashlib.sha256(rr).hexdigest()}

def probe_provider(base,chain_id,anchors,kyve):
    out={"base":base,"anchors":{},"transport":"verified_tls_or_http"}
    modes=[False]
    if base.startswith("https://"):modes.append(True)
    last=None
    for insecure in modes:
      try:
        vals={}
        for h in anchors: vals[str(h)]=rpc_one(base,h,insecure)
        if any(x["chain_id"]!=chain_id for x in vals.values()):raise RuntimeError("wrong chain")
        out["anchors"]=vals;out["status"]="PASS";out["tls_verification_disabled"]=bool(insecure)
        match=True
        for h in anchors:
          a=vals[str(h)];k=kyve[str(h)]
          match=match and all([a["height"]==k["height"],a["time"]==k["time"],a["hash"]==k["hash"],
                               a["app_hash"]==k["app_hash"],a["block_results_height"]==k["block_results_height"]])
        out["canonical_all_anchor_match"]=bool(match)
        return out
      except Exception as e:
        last=type(e).__name__+": "+str(e)[:1000]
    out["status"]="FAIL";out["error"]=last
    return out

def main():
    rec={"freeze_commit":"c8b39998a239f0a54aa32f521e3da953e956c055",
         "source_registry_commit":"7cb8e3abd7fb5788b299c270380f1ea36715e2a0",
         "chain_registry_commit":CHAIN_REGISTRY_COMMIT,
         "generated_utc":datetime.now(timezone.utc).isoformat(),
         "event_counts_opened":False,"market_outcomes_opened":False,
         "candidate_order":[x["chain"] for x in SPECS],"results":[],"selected":None}
    for spec in SPECS:
      ce={"chain":spec["chain"],"chain_id":spec["chain_id"],"pool":spec["pool"],"anchors":spec["anchors"]}
      try:
        meta=pool_meta(spec["pool"]);ce["kyve_pool"]=meta
        ky={}
        for h in spec["anchors"]:ky[str(h)]=kyve_height(spec["pool"],h,meta)
        ce["kyve"]=ky;ce["kyve_status"]="PASS"
      except Exception as e:
        ce["kyve_status"]="FAIL";ce["kyve_error"]=type(e).__name__+": "+str(e)[:1200]
        rec["results"].append(ce);continue
      endpoints=[]
      try:endpoints.extend(registry_rpcs(spec["registry"]))
      except Exception as e:ce["registry_error"]=str(e)
      endpoints.extend(spec["extras"]);endpoints=list(dict.fromkeys(endpoints))
      providers={}
      with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futs={ex.submit(probe_provider,b,spec["chain_id"],spec["anchors"],ky):b for b in endpoints}
        for f in concurrent.futures.as_completed(futs):
          b=futs[f]
          try:providers[b]=f.result()
          except Exception as e:providers[b]={"base":b,"status":"FAIL","error":str(e)}
      ce["providers"]=providers
      ce["canonical_independent_matches"]=[b for b,p in providers.items() if p.get("canonical_all_anchor_match")]
      ce["two_path_multi_anchor_pass"]=len(ce["canonical_independent_matches"])>=1
      rec["results"].append(ce)
      if ce["two_path_multi_anchor_pass"]:
        rec["selected"]=spec["chain"];break
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=="__main__":main()
