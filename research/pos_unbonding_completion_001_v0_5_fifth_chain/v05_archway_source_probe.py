#!/usr/bin/env python3
import json, hashlib, urllib.request, urllib.parse, urllib.error, os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT="research/pos_unbonding_completion_001_v0_5_fifth_chain/ARCHWAY_SOURCE_QUALIFICATION_V05.json"
UA="CryptoLab-Unbonding-V05-ArchwaySource/1.0"
TARGET="2024-06-01T12:00:00+00:00"
TARGET_DT=datetime.fromisoformat(TARGET)

SOURCES=[
 ("allthatnode_archive","https://archway-mainnet-archive.allthatnode.com:26657"),
 ("foundation","https://rpc.mainnet.archway.io"),
 ("nodesguru","https://rpc-1.archway.nodes.guru"),
 ("kjnodes","https://archway.rpc.kjnodes.com"),
 ("lavenderfive","https://rpc.lavenderfive.com/archway"),
 ("validatrium","https://rpc-archway.mainnet.validatrium.club"),
 ("chainroot","https://archway-rpc.chainroot.io"),
 ("noders","https://archway-rpc.noders.services"),
 ("stakeup","https://rpc.archway.stakeup.tech")
]

def get(url,timeout=15):
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
  except urllib.error.HTTPError as e:
    body=e.read().decode("utf-8","replace")[:900]
    raise RuntimeError(f"HTTP {e.code}: {body}")

def ptime(s):return datetime.fromisoformat(s.replace("Z","+00:00"))

def block(base,h=None):
  raw=get(base.rstrip("/")+"/block"+(f"?height={h}" if h is not None else ""))
  o=json.loads(raw.decode())
  if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
  r=o.get("result") or {}; hd=((r.get("block") or {}).get("header") or {})
  if not hd.get("height"):raise RuntimeError("no block header")
  return {"height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),
          "block_hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
          "sha256":hashlib.sha256(raw).hexdigest()}

def status(base):
  raw=get(base.rstrip("/")+"/status");o=json.loads(raw.decode())
  if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
  s=((o.get("result") or {}).get("sync_info") or {})
  return {"earliest":int(s.get("earliest_block_height") or 0),"latest":int(s.get("latest_block_height") or 0),
          "earliest_time":s.get("earliest_block_time"),"latest_time":s.get("latest_block_time")}

def first_at_or_after(base):
  st=status(base);lo=max(1,st["earliest"]);hi=st["latest"]
  blo=block(base,lo);bhi=block(base,hi)
  if ptime(blo["time"])>TARGET_DT:raise RuntimeError(f"PRUNED_BEYOND_TARGET earliest={lo} time={blo['time']}")
  if ptime(bhi["time"])<TARGET_DT:raise RuntimeError("target after latest")
  while lo<hi:
    mid=(lo+hi)//2
    bm=block(base,mid)
    if ptime(bm["time"])<TARGET_DT:lo=mid+1
    else:hi=mid
  return st,block(base,lo)

def block_results(base,h):
  raw=get(base.rstrip("/")+f"/block_results?height={h}");o=json.loads(raw.decode())
  if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
  return {"height":int((o.get("result") or {}).get("height") or h),"sha256":hashlib.sha256(raw).hexdigest()}

def bsearch(base,q):
  params={"query":json.dumps(q),"page":"1","per_page":"100","order_by":json.dumps("asc")}
  raw=get(base.rstrip("/")+"/block_search?"+urllib.parse.urlencode(params));o=json.loads(raw.decode())
  if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
  r=o.get("result") or {}
  hs=[int(((x.get("block") or {}).get("header") or {}).get("height")) for x in (r.get("blocks") or [])]
  return {"total_count":int(r.get("total_count") or 0),"heights":hs,"sha256":hashlib.sha256(raw).hexdigest()}

def probe(name,base):
  x={"provider":name,"base":base}
  try:
    st,b=first_at_or_after(base);x["status_bounds"]=st;x["target_block"]=b
    x["block_results"]=block_results(base,b["height"]);x["historical_target_status"]="PASS"
  except Exception as e:
    x["historical_target_status"]="FAIL";x["error"]=type(e).__name__+": "+str(e);return x
  try:x["exact_index"]=bsearch(base,f"block.height = {b['height']}")
  except Exception as e:x["exact_index_error"]=type(e).__name__+": "+str(e)
  try:x["completion_index_1024"]=bsearch(base,f"complete_unbonding.amount EXISTS AND block.height >= {b['height']} AND block.height <= {b['height']+1023}")
  except Exception as e:x["completion_index_error"]=type(e).__name__+": "+str(e)
  return x

def main():
  rec={"freeze_commit":"c77013a5da826498c936b86a42902aed61c7dcd4","candidate":"archway",
       "chain_id":"archway-1","target_utc":TARGET,"generated_utc":datetime.now(timezone.utc).isoformat(),"sources":[]}
  with ThreadPoolExecutor(max_workers=len(SOURCES)) as ex:
    futs={ex.submit(probe,n,b):n for n,b in SOURCES};by={}
    for fut in as_completed(futs):by[futs[fut]]=fut.result()
  rec["sources"]=[by[n] for n,_ in SOURCES]
  good=[x for x in rec["sources"] if x.get("historical_target_status")=="PASS"]
  groups={}
  for x in good:
    b=x["target_block"];key=(b["height"],b["block_hash"],b["time"],b["app_hash"],b["chain_id"])
    groups.setdefault(key,[]).append(x["provider"])
  best=max(groups.items(),key=lambda kv:len(kv[1])) if groups else (None,[])
  rec["reconciliation"]={"successful_sources":len(good),"largest_matching_group":best[1],
    "two_source_fixed_height_pass":len(best[1])>=2,"canonical_tuple":best[0]}
  rec["index_capability"]={"completion_index_sources":[x["provider"] for x in good if "completion_index_1024" in x],
    "exact_height_index_sources":[x["provider"] for x in good if "exact_index" in x]}
  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
  print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__":main()
