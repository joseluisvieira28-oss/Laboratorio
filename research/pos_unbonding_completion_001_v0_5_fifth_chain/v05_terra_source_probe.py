#!/usr/bin/env python3
import json, hashlib, urllib.request, urllib.parse, urllib.error, os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT="research/pos_unbonding_completion_001_v0_5_fifth_chain/TERRA_SOURCE_QUALIFICATION_V05.json"
UA="CryptoLab-Unbonding-V05-TerraSource/1.0"
HEIGHT=10106846
SOURCES=[
 ("lavenderfive","https://rpc.lavenderfive.com/terra2"),
 ("stakely","https://terra-rpc.stakely.io"),
 ("publicnode","https://terra-rpc.publicnode.com"),
 ("highstakes","https://terra-phoenix-rpc.highstakes.ch"),
 ("polkachu","https://terra-rpc.polkachu.com"),
 ("cosmosrescue","https://terra-rpc.cosmosrescue.dev:8443"),
 ("tdrsys","https://terra2.tdrsys.com:2053")
]

def get(url,timeout=18):
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
  except urllib.error.HTTPError as e:
    body=e.read().decode("utf-8","replace")[:1000]
    raise RuntimeError(f"HTTP {e.code}: {body}")

def block(base,h):
  raw=get(base.rstrip("/") + f"/block?height={h}")
  o=json.loads(raw.decode())
  if o.get("error"): raise RuntimeError(json.dumps(o["error"]))
  r=o.get("result") or {}; b=r.get("block") or {}; hd=b.get("header") or {}
  return {"height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),
          "block_hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
          "sha256":hashlib.sha256(raw).hexdigest()}

def block_results(base,h):
  raw=get(base.rstrip("/") + f"/block_results?height={h}")
  o=json.loads(raw.decode())
  if o.get("error"): raise RuntimeError(json.dumps(o["error"]))
  r=o.get("result") or {}
  return {"height":int(r.get("height") or h),"sha256":hashlib.sha256(raw).hexdigest()}

def bsearch(base,q):
  params={"query":json.dumps(q),"page":"1","per_page":"100","order_by":json.dumps("asc")}
  url=base.rstrip("/")+"/block_search?"+urllib.parse.urlencode(params)
  raw=get(url)
  o=json.loads(raw.decode())
  if o.get("error"): raise RuntimeError(json.dumps(o["error"]))
  r=o.get("result") or {}
  hs=[int(((x.get("block") or {}).get("header") or {}).get("height")) for x in (r.get("blocks") or [])]
  return {"total_count":int(r.get("total_count") or 0),"heights":hs,"sha256":hashlib.sha256(raw).hexdigest()}

def probe(name,base):
  x={"provider":name,"base":base}
  try:
    x["block"]=block(base,HEIGHT)
    x["block_results"]=block_results(base,HEIGHT)
    x["fixed_height_status"]="PASS"
  except Exception as e:
    x["fixed_height_status"]="FAIL"; x["fixed_height_error"]=type(e).__name__+": "+str(e)
    return x
  try:
    x["exact_index"]=bsearch(base,f"block.height = {HEIGHT}")
  except Exception as e:
    x["exact_index_error"]=type(e).__name__+": "+str(e)
  try:
    x["completion_index_1024"]=bsearch(base,f"complete_unbonding.amount EXISTS AND block.height >= {HEIGHT} AND block.height <= {HEIGHT+1023}")
  except Exception as e:
    x["completion_index_error"]=type(e).__name__+": "+str(e)
  return x

def main():
  rec={"freeze_commit":"c77013a5da826498c936b86a42902aed61c7dcd4","candidate":"terra2",
       "chain_id":"phoenix-1","anchor_height":HEIGHT,
       "anchor_external_time_reference":"2024-04-29T14:59:31Z",
       "generated_utc":datetime.now(timezone.utc).isoformat(),"sources":[]}
  with ThreadPoolExecutor(max_workers=len(SOURCES)) as ex:
    futs={ex.submit(probe,n,b):n for n,b in SOURCES}
    by={}
    for fut in as_completed(futs): by[futs[fut]]=fut.result()
  rec["sources"]=[by[n] for n,_ in SOURCES]
  good=[x for x in rec["sources"] if x.get("fixed_height_status")=="PASS"]
  groups={}
  for x in good:
    b=x["block"]; key=(b.get("block_hash"),b.get("time"),b.get("app_hash"),b.get("chain_id"))
    groups.setdefault(key,[]).append(x["provider"])
  best=max(groups.items(),key=lambda kv:len(kv[1])) if groups else (None,[])
  rec["reconciliation"]={
    "successful_sources":len(good),
    "largest_matching_group":best[1],
    "two_source_fixed_height_pass":len(best[1])>=2,
    "canonical_tuple":best[0]
  }
  indexed=[x for x in good if (x.get("exact_index") or {}).get("heights")==[HEIGHT]]
  rec["index_capability"]={
    "exact_height_index_sources":[x["provider"] for x in indexed],
    "completion_index_sources":[x["provider"] for x in indexed if "completion_index_1024" in x]
  }
  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f: json.dump(rec,f,indent=2,sort_keys=True); f.write("\n")
  print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__":main()

# trigger: source-only qualification run
