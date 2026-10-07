#!/usr/bin/env python3
import json, hashlib, os, re, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/FIFTH_CHAIN_EXTENSION_QUALIFICATION_V043.json"
UA="CryptoLab-Unbonding-V043-SourceQual/1.0"
TARGET=datetime(2024,6,1,12,0,0,tzinfo=timezone.utc)

CANDIDATES=[
 {"chain":"akash","sources":[
   ["uquad","https://akash.rpc.uquad.org"],
   ["publicnode","https://akash-rpc.publicnode.com"],
   ["polkachu","https://akash-rpc.polkachu.com"],
   ["akashnet","https://rpc.akashnet.net"]]},
 {"chain":"secretnetwork","sources":[
   ["mario_archive","https://rpc.archive.scrt.marionode.com"],
   ["lavenderfive","https://rpc.lavenderfive.com/secretnetwork"],
   ["secretsaturn","https://rpc.mainnet.secretsaturn.net"],
   ["stakewolle","https://public.stakewolle.com/cosmos/secretnetwork/rpc"],
   ["one_rpc","https://1rpc.io/scrt-rpc"]]},
 {"chain":"axelar","sources":[
   ["imperator","https://rpc-axelar.imperator.co"],
   ["quickapi","https://axelar-rpc.quickapi.com"],
   ["pops","https://axelar-rpc.pops.one"],
   ["lavenderfive","https://rpc.lavenderfive.com/axelar"],
   ["publicnode","https://axelar-rpc.publicnode.com"]]}
]

def get(url,timeout=12):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
 except urllib.error.HTTPError as e:
  body=e.read().decode("utf-8","replace")[:900]
  raise RuntimeError(f"HTTP {e.code}: {body}")

def block(base,h=None):
 url=base.rstrip("/")+"/block"
 if h is not None:url+=f"?height={h}"
 raw=get(url);obj=json.loads(raw.decode())
 if obj.get("error"):raise RuntimeError(json.dumps(obj["error"]))
 rr=obj.get("result") or {};b=rr.get("block") or {};hd=b.get("header") or {}
 if not hd.get("height"):raise RuntimeError("no block header")
 return {"height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),
   "hash":((rr.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
   "sha256":hashlib.sha256(raw).hexdigest()}

def dt(s):return datetime.fromisoformat(s.replace("Z","+00:00"))

def floor_from_error(s):
 m=re.search(r"(?:lowest|earliest) height(?: is)?\s*[:=]?\s*(\d+)",s,re.I)
 return int(m.group(1)) if m else None

def find_target(base):
 try:latest=block(base)
 except Exception as e:return {"status":"UNAVAILABLE","error":type(e).__name__+": "+str(e)}
 lo=1;hi=latest["height"];floor=None
 try:first=block(base,1)
 except Exception as e:
  floor=floor_from_error(str(e))
  if floor:lo=floor
  else:
   # exponential probes to discover a retained floor without assuming pruning format
   for probe in (100000,1000000,5000000,10000000,20000000,40000000,80000000):
    if probe>=hi:break
    try:
     first=block(base,probe);lo=probe;break
    except Exception:continue
   else:return {"status":"NO_HISTORICAL_FLOOR","latest":latest}
 try:first=block(base,lo)
 except Exception as e:return {"status":"UNAVAILABLE_AT_FLOOR","floor":lo,"error":str(e),"latest":latest}
 if dt(first["time"])>TARGET:return {"status":"PRUNED_BEYOND_TARGET","lowest":first,"latest":latest}

 best=None
 while lo<=hi:
  mid=(lo+hi)//2
  try:b=block(base,mid)
  except Exception as e:
   f=floor_from_error(str(e))
   if f and f>mid:lo=f;continue
   # If a sparse/pruned gap is hit, move upward conservatively.
   lo=mid+1;continue
  if dt(b["time"])<TARGET:lo=mid+1
  else:best=b;hi=mid-1
 if not best:return {"status":"NO_TARGET_BLOCK","latest":latest}
 prev=None
 try:prev=block(base,best["height"]-1)
 except Exception:pass
 return {"status":"PASS","first_at_or_after":best,"previous":prev}

def reconcile(sources):
 good=[]
 for n,r in sources.items():
  if r.get("status")=="PASS":good.append((n,r["first_at_or_after"]))
 pairs=[]
 for i in range(len(good)):
  for k in range(i+1,len(good)):
   a,x=good[i];b,y=good[k]
   p={"a":a,"b":b,"height_match":x["height"]==y["height"],"hash_match":x["hash"]==y["hash"],
      "time_match":x["time"]==y["time"],"app_hash_match":x["app_hash"]==y["app_hash"]}
   p["pass"]=all(p[z] for z in ("height_match","hash_match","time_match","app_hash_match"))
   pairs.append(p)
 return {"successful_sources":len(good),"pairs":pairs,"two_source_pass":any(p["pass"] for p in pairs)}

def main():
 rec={"amendment_commit":"ef3133672c74770409b269ebef950dbe97cb4e22",
 "target_utc":TARGET.isoformat(),"generated_utc":datetime.now(timezone.utc).isoformat(),
 "order":["akash","secretnetwork","axelar"],"selected":None,"results":[]}
 for spec in CANDIDATES:
  e={"chain":spec["chain"],"sources":{}}
  for name,base in spec["sources"]:
   r=find_target(base);r["base"]=base;e["sources"][name]=r
  e["reconciliation"]=reconcile(e["sources"]);rec["results"].append(e)
  if e["reconciliation"]["two_source_pass"]:
   rec["selected"]=spec["chain"];break
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=="__main__":main()
