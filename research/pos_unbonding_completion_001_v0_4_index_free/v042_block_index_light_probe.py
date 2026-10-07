#!/usr/bin/env python3
import json, hashlib, os, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/BLOCK_INDEX_LIGHT_PROBE_V042.json"
UA="CryptoLab-Unbonding-V042-LightProbe/1.0"
CHAINS=[
 {"chain":"cosmoshub","anchor":20000000,"sources":[["citizenweb3","https://rpc.cosmoshub-4-archive.citizenweb3.com"],["cryptocrew","https://rpc.cosmoshub-main.ccvalidators.com"]]},
 {"chain":"osmosis","anchor":15000000,"sources":[["osmosis","https://rpc.osmosis.zone"],["validatus","https://rpc.archive.osmosis.validatus.com"]]},
 {"chain":"celestia","anchor":2500000,"sources":[["kjnodes","http://136.243.94.113:26667"],["numia","https://public-celestia-rpc.numia.xyz"]]},
 {"chain":"dydx","anchor":15000000,"sources":[["kingnodes","https://dydx-ops-archive-rpc.kingnodes.com"],["polkachu","https://dydx-dao-archive-rpc.polkachu.com"]]}
]
def get(url,timeout=15):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
 except urllib.error.HTTPError as e:
  raise RuntimeError(f"HTTP {e.code}: "+e.read().decode("utf-8","replace")[:600])
def search(base,q):
 params={"query":json.dumps(q),"page":"1","per_page":"100","order_by":json.dumps("asc")}
 url=base.rstrip("/")+"/block_search?"+urllib.parse.urlencode(params)
 raw=get(url);obj=json.loads(raw.decode())
 if obj.get("error"):raise RuntimeError(json.dumps(obj["error"]))
 rr=obj.get("result") or {}
 return {"url":url,"sha256":hashlib.sha256(raw).hexdigest(),"total_count":int(rr.get("total_count") or 0),
 "heights":[int(((x.get("block") or {}).get("header") or {})["height"]) for x in (rr.get("blocks") or [])]}
def main():
 rec={"amendment_commit":"6b7debcd7797cbbc1005c44c3762fc7202a4b6a2","generated_utc":datetime.now(timezone.utc).isoformat(),"chains":[]}
 for s in CHAINS:
  e={"chain":s["chain"],"anchor":s["anchor"],"sources":{}}
  for n,b in s["sources"]:
   x={"base":b}
   try:x["exact_anchor"]=search(b,f"block.height = {s['anchor']}")
   except Exception as z:x["exact_anchor_error"]=type(z).__name__+": "+str(z)
   try:x["completion_1024"]=search(b,f"complete_unbonding.amount EXISTS AND block.height >= {s['anchor']} AND block.height <= {s['anchor']+1023}")
   except Exception as z:x["completion_1024_error"]=type(z).__name__+": "+str(z)
   e["sources"][n]=x
  good=[(n,v.get("completion_1024",{}).get("heights")) for n,v in e["sources"].items() if "completion_1024" in v]
  e["match"]=len(good)>=2 and good[0][1]==good[1][1]
  rec["chains"].append(e)
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=="__main__":main()
