#!/usr/bin/env python3
import json, hashlib, os, re, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/FIFTH_CHAIN_SOURCE_QUALIFICATION_V04.json"
UA="CryptoLab-Unbonding-V04-SourceQual/1.0"
TARGET=datetime(2024,6,1,12,0,0,tzinfo=timezone.utc)

CANDIDATES=[
  {
    "chain":"kava","mode":"fixed","height":9500000,
    "sources":[
      ["kava_labs","https://rpc.data.kava.io"],
      ["chainstack","https://rpc.data.kava.chainstacklabs.com"],
      ["ibs_team","https://kava-rpc.ibs.team"]
    ]
  },
  {
    "chain":"injective","mode":"time",
    "sources":[
      ["polkachu","https://injective-rpc.polkachu.com"],
      ["lavenderfive","https://rpc.lavenderfive.com/injective"],
      ["publicnode","https://injective-rpc.publicnode.com"],
      ["highstakes","https://injective-rpc.highstakes.ch"]
    ]
  },
  {
    "chain":"sei","mode":"time",
    "sources":[
      ["rhino","https://rpc.sei-apis.com"],
      ["polkachu","https://sei-rpc.polkachu.com"],
      ["lavenderfive","https://rpc.lavenderfive.com/sei"],
      ["kjnodes","https://sei.rpc.kjnodes.com"],
      ["publicnode","https://sei-rpc.publicnode.com"]
    ]
  }
]

def get(url,timeout=15):
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r:
      return r.read()
  except urllib.error.HTTPError as e:
    body=e.read().decode("utf-8","replace")[:1200]
    raise RuntimeError(f"HTTP {e.code}: {body}")

def parse_time(s):
  if not s:return None
  return datetime.fromisoformat(s.replace("Z","+00:00"))

def block(base,h=None):
  url=base.rstrip("/")+"/block"
  if h is not None:url+=f"?height={h}"
  raw=get(url)
  obj=json.loads(raw.decode())
  if obj.get("error"): raise RuntimeError(json.dumps(obj["error"]))
  r=obj.get("result") or {}; b=r.get("block") or {}; hd=b.get("header") or {}
  if not hd.get("height"): raise RuntimeError("no block header")
  return {
    "height":int(hd["height"]),"time":hd.get("time"),
    "block_hash":((r.get("block_id") or {}).get("hash")),
    "app_hash":hd.get("app_hash"),"chain_id":hd.get("chain_id"),
    "sha256":hashlib.sha256(raw).hexdigest()
  }

def lowest_from_error(s):
  m=re.search(r"lowest height is\s+(\d+)",s,re.I)
  return int(m.group(1)) if m else None

def find_target(base):
  try:
    latest=block(base)
  except Exception as e:
    return {"status":"UNAVAILABLE","error":type(e).__name__+": "+str(e)}
  hi=latest["height"]; lo=1
  # Discover retained floor if provider reports pruning.
  try:
    block(base,1)
  except Exception as e:
    floor=lowest_from_error(str(e))
    if floor: lo=floor
  try:
    first=block(base,lo)
  except Exception as e:
    return {"status":"UNAVAILABLE","error":str(e),"latest":latest}
  if parse_time(first["time"])>TARGET:
    return {"status":"PRUNED_BEYOND_TARGET","lowest":first,"latest":latest}

  best=None
  while lo<=hi:
    mid=(lo+hi)//2
    try:
      b=block(base,mid)
    except Exception as e:
      floor=lowest_from_error(str(e))
      if floor and floor>mid:
        lo=floor
        continue
      return {"status":"SEARCH_ERROR","height":mid,"error":str(e),"latest":latest}
    t=parse_time(b["time"])
    if t<TARGET:
      lo=mid+1
    else:
      best=b; hi=mid-1
  if best is None:
    return {"status":"NO_BLOCK_AT_OR_AFTER_TARGET","latest":latest}
  prev=None
  if best["height"]>1:
    try: prev=block(base,best["height"]-1)
    except Exception: pass
  return {"status":"PASS","target":TARGET.isoformat(),"first_at_or_after":best,"previous":prev}

def fixed(base,h):
  try:return {"status":"PASS","block":block(base,h)}
  except Exception as e:return {"status":"FAIL","error":str(e)}

def reconcile(chain,srcs):
  good=[]
  for name,res in srcs.items():
    if res.get("status")!="PASS":continue
    b=res.get("block") or res.get("first_at_or_after")
    if b and b.get("block_hash"):good.append((name,b))
  pairs=[]
  for i in range(len(good)):
    for j in range(i+1,len(good)):
      a,ba=good[i]; c,bc=good[j]
      pairs.append({
        "a":a,"b":c,
        "height_match":ba["height"]==bc["height"],
        "block_hash_match":ba["block_hash"]==bc["block_hash"],
        "time_match":ba["time"]==bc["time"],
        "app_hash_match":ba.get("app_hash")==bc.get("app_hash")
      })
  passed=[p for p in pairs if all(p[k] for k in ("height_match","block_hash_match","time_match","app_hash_match"))]
  return {"chain":chain,"successful_sources":len(good),"pairs":pairs,"two_source_pass":bool(passed)}

def main():
  receipt={
    "freeze_commit":"71ac365e709b0e0d7074caed7e842f513207aa85",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "selection_order":["kava","injective","sei"],
    "results":[],
    "selected_fifth_chain":None
  }
  for spec in CANDIDATES:
    entry={"chain":spec["chain"],"mode":spec["mode"],"sources":{}}
    for name,base in spec["sources"]:
      if spec["mode"]=="fixed":res=fixed(base,spec["height"])
      else:res=find_target(base)
      res["base"]=base
      entry["sources"][name]=res
    entry["reconciliation"]=reconcile(spec["chain"],entry["sources"])
    receipt["results"].append(entry)
    if entry["reconciliation"]["two_source_pass"]:
      receipt["selected_fifth_chain"]=spec["chain"]
      break
  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f:
    json.dump(receipt,f,indent=2,sort_keys=True);f.write("\n")
  print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":main()
