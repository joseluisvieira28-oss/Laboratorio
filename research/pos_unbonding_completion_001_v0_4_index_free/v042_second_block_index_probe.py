#!/usr/bin/env python3
import json, hashlib, os, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/SECOND_BLOCK_INDEX_PROBE_V042.json"
UA="CryptoLab-Unbonding-V042-SecondIndex/1.0"

CHAINS=[
 {"chain":"osmosis","anchor":15000000,"reference":["validatus","https://rpc.archive.osmosis.validatus.com"],"candidates":[
   ["polkachu","https://osmosis-rpc.polkachu.com"],
   ["imperator","https://rpc-osmosis.imperator.co"],
   ["lavenderfive","https://rpc.lavenderfive.com/osmosis"],
   ["pocket","https://osmosis.api.pocket.network"],
   ["stakely","https://osmosis-rpc.stakely.io"]]},
 {"chain":"celestia","anchor":2500000,"reference":["kjnodes","http://136.243.94.113:26667"],"candidates":[
   ["polkachu_archive","https://celestia-archive-rpc.polkachu.com"],
   ["polkachu_public","https://celestia-rpc.polkachu.com"],
   ["pops","https://rpc.celestia.pops.one"],
   ["itrocket","https://celestia-mainnet-rpc.itrocket.net"],
   ["denodes","https://celestia-mainnet-rpc.denodes.xyz"]]}
]
def get(url,timeout=15):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
 except urllib.error.HTTPError as e:
  raise RuntimeError(f"HTTP {e.code}: "+e.read().decode("utf-8","replace")[:700])
def search(base,q):
 params={"query":json.dumps(q),"page":"1","per_page":"100","order_by":json.dumps("asc")}
 url=base.rstrip("/")+"/block_search?"+urllib.parse.urlencode(params)
 raw=get(url);obj=json.loads(raw.decode())
 if obj.get("error"):raise RuntimeError(json.dumps(obj["error"]))
 rr=obj.get("result") or {}
 return {"total_count":int(rr.get("total_count") or 0),"heights":[int(((x.get("block") or {}).get("header") or {})["height"]) for x in (rr.get("blocks") or [])],"sha256":hashlib.sha256(raw).hexdigest()}
def probe(base,a):
 out={"base":base}
 try:out["anchor"]=search(base,f"block.height = {a}")
 except Exception as e:out["anchor_error"]=type(e).__name__+": "+str(e)
 try:out["completion"]=search(base,f"complete_unbonding.amount EXISTS AND block.height >= {a} AND block.height <= {a+1023}")
 except Exception as e:out["completion_error"]=type(e).__name__+": "+str(e)
 return out
def main():
 rec={"amendment_commit":"6b7debcd7797cbbc1005c44c3762fc7202a4b6a2","generated_utc":datetime.now(timezone.utc).isoformat(),"chains":[]}
 for s in CHAINS:
  rn,rb=s["reference"];ref=probe(rb,s["anchor"])
  e={"chain":s["chain"],"anchor":s["anchor"],"reference":{"provider":rn,**ref},"candidates":[]}
  refh=ref.get("completion",{}).get("heights")
  for n,b in s["candidates"]:
   p=probe(b,s["anchor"]);p["provider"]=n
   p["matches_reference"]=refh is not None and p.get("completion",{}).get("heights")==refh and p.get("anchor",{}).get("heights")==[s["anchor"]]
   e["candidates"].append(p)
  rec["chains"].append(e)
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=="__main__":main()
