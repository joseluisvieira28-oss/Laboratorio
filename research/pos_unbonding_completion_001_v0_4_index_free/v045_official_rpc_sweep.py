#!/usr/bin/env python3
import concurrent.futures, hashlib, json, os, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/OFFICIAL_RPC_SWEEP_V045.json"
UA="CryptoLab-Unbonding-V045-RPCSweep/1.0"
REGISTRY_COMMIT="c9d65b60bc0229c06d49ded805ba528f316bd9c7"

SPECS=[
 {
  "chain":"terra2","chain_id":"phoenix-1",
  "registry":"terra2",
  "anchors":{
    "start":{"height":3128548,"time":"2023-01-01T00:00:04.983278349Z","hash":"4F58CA5EAB4CF8674A4E251EDA1389DF626D1825F86A1D443074B301BF5DF751","app_hash":"5D36AEDF05D85FC59ED718C9569E4510E5251F41A388EAB372B250071628F774"},
    "end":{"height":13646942}
  },
  "authority":"http://15.204.43.42:26657",
  "extras":["https://pho1-rpc.blockpane.com"]
 },
 {
  "chain":"archway","chain_id":"archway-1",
  "registry":"archway",
  "anchors":{
    "fixed":{"height":3554500,"time":"2024-03-04T14:19:15.221993843Z","hash":"34A783870D4D4292B8D54A37A02CA1BCA868E274F949265E0B9BE299B99B6A14","app_hash":"9562F5DF73EE58E8612FC4FBD0A57460538C7E3EFC749246493EBD1437AB859A"}
  },
  "authority":null,
  "extras":[
    "https://archway-mainnet-archive.allthatnode.com:26657",
    "http://148.251.124.58:26657"
  ]
 }
]

def get(url,timeout=10):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")[:500]
        raise RuntimeError(f"HTTP {e.code}: {body}")

def parse_block(raw):
    o=json.loads(raw.decode()); 
    if o.get("error"): raise RuntimeError(json.dumps(o["error"]))
    r=o.get("result") or {}; b=r.get("block") or {}; h=b.get("header") or {}
    if not h.get("height"): raise RuntimeError("no block header")
    return {"height":int(h["height"]),"time":h.get("time"),"chain_id":h.get("chain_id"),
            "hash":((r.get("block_id") or {}).get("hash")),"app_hash":h.get("app_hash"),
            "sha256":hashlib.sha256(raw).hexdigest()}

def probe(base,chain_id,anchors):
    out={"base":base,"anchors":{}}
    try:
      for label,a in anchors.items():
        h=a["height"]
        br=get(base.rstrip("/") + f"/block?height={h}")
        rr=get(base.rstrip("/") + f"/block_results?height={h}")
        b=parse_block(br); ro=json.loads(rr.decode())
        if ro.get("error"): raise RuntimeError(json.dumps(ro["error"]))
        rh=int(((ro.get("result") or {}).get("height")) or 0)
        if b["chain_id"]!=chain_id or rh!=h: raise RuntimeError("chain/results mismatch")
        out["anchors"][label]={"block":b,"block_results_sha256":hashlib.sha256(rr).hexdigest()}
      out["status"]="PASS"
    except Exception as e:
      out["status"]="FAIL"; out["error"]=type(e).__name__+": "+str(e)[:1000]
    return out

def registry_rpcs(name):
    url=f"https://raw.githubusercontent.com/cosmos/chain-registry/{REGISTRY_COMMIT}/{name}/chain.json"
    j=json.loads(get(url,15).decode())
    return [x["address"].rstrip("/") for x in ((j.get("apis") or {}).get("rpc") or []) if x.get("address")]

def main():
    rec={"amendment_commit":"3bdfe66c8f8597a4772ec87b68810d1b51e2eb94",
         "registry_commit":REGISTRY_COMMIT,
         "generated_utc":datetime.now(timezone.utc).isoformat(),
         "scope":"source-only fixed historical anchors; no event census/outcomes","chains":[]}
    for spec in SPECS:
      ce={"chain":spec["chain"],"chain_id":spec["chain_id"],"anchors":spec["anchors"],"providers":{}}
      # For Terra, fill exact end authority bytes before comparing candidates.
      anchors=json.loads(json.dumps(spec["anchors"]))
      if spec["authority"]:
        auth=probe(spec["authority"],spec["chain_id"],anchors)
        ce["authority"]={"name":"known_archive","result":auth}
        if auth.get("status")=="PASS":
          for label,v in auth["anchors"].items():
            anchors[label].update({"time":v["block"]["time"],"hash":v["block"]["hash"],"app_hash":v["block"]["app_hash"]})
      endpoints=[]
      try:endpoints.extend(registry_rpcs(spec["registry"]))
      except Exception as e:ce["registry_error"]=str(e)
      endpoints.extend(spec["extras"])
      # deterministic unique order
      endpoints=list(dict.fromkeys(endpoints))
      with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        futs={ex.submit(probe,b,spec["chain_id"],anchors):b for b in endpoints}
        for fut in concurrent.futures.as_completed(futs):
          b=futs[fut]
          try:p=fut.result()
          except Exception as e:p={"base":b,"status":"FAIL","error":str(e)}
          if p.get("status")=="PASS":
            ok=True
            for label,a in anchors.items():
              got=p["anchors"][label]["block"]
              ok=ok and got["height"]==a["height"]
              for k in ("time","hash","app_hash"):
                if a.get(k): ok=ok and got.get(k)==a.get(k)
            p["canonical_match"]=bool(ok)
          ce["providers"][b]=p
      ce["canonical_matches"]=[b for b,p in ce["providers"].items() if p.get("canonical_match")]
      ce["independent_second_source_pass"]=len(ce["canonical_matches"])>=1
      rec["chains"].append(ce)
      # frozen order: if Terra finds second source, Archway is not eligible for selection.
      if spec["chain"]=="terra2" and ce["independent_second_source_pass"]:
        rec["selected_candidate"]="terra2"; break
    if "selected_candidate" not in rec:
      for c in rec["chains"]:
        if c["chain"]=="archway" and c["independent_second_source_pass"]:
          rec["selected_candidate"]="archway"; break
      else: rec["selected_candidate"]=None
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__":main()
