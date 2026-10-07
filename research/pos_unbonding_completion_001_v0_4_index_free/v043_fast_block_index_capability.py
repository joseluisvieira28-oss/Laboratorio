#!/usr/bin/env python3
import json,hashlib,urllib.parse,urllib.request,urllib.error,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_4_index_free/BLOCK_INDEX_CAPABILITY_V043.json"
UA="CryptoLab-Unbonding-V043/1.0"
CHAINS=[
("cosmoshub",20000000,[("citizenweb3","https://rpc.cosmoshub-4-archive.citizenweb3.com"),("cryptocrew","https://rpc.cosmoshub-main.ccvalidators.com")]),
("osmosis",15000000,[("osmosis","https://rpc.osmosis.zone"),("validatus","https://rpc.archive.osmosis.validatus.com")]),
("celestia",2500000,[("kjnodes","http://136.243.94.113:26667"),("numia","https://public-celestia-rpc.numia.xyz")]),
("dydx",15000000,[("kingnodes","https://dydx-ops-archive-rpc.kingnodes.com"),("polkachu","https://dydx-dao-archive-rpc.polkachu.com")])]
def get(url,t=12):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=t) as r:return r.read()
def call(base,path,params):
 u=base.rstrip("/")+path+"?"+urllib.parse.urlencode(params)
 raw=get(u);o=json.loads(raw)
 if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
 return u,raw,o.get("result") or {}
def main():
 rec={"parent_amendment":"6b7debcd7797cbbc1005c44c3762fc7202a4b6a2","generated_utc":datetime.now(timezone.utc).isoformat(),"purpose":"fast capability only; no event census","chains":[]}
 for chain,h,sources in CHAINS:
  ce={"chain":chain,"anchor":h,"sources":{}}
  for name,base in sources:
   se={"base":base}
   for label,q in [("exact",f"block.height = {h}"),("exists",f"complete_unbonding.amount EXISTS AND block.height >= {h-10000} AND block.height <= {h+10000}")]:
    try:
     u,raw,rr=call(base,"/block_search",{"query":json.dumps(q),"page":"1","per_page":"1","order_by":json.dumps("asc")})
     se[label]={"status":"PASS","total_count":int(rr.get("total_count") or 0),"returned":len(rr.get("blocks") or []),"sha256":hashlib.sha256(raw).hexdigest()}
    except Exception as e:se[label]={"status":"FAIL","error":type(e).__name__+": "+str(e)[:500]}
   ce["sources"][name]=se
  ce["two_provider_index_capability"]=sum(1 for s in ce["sources"].values() if s["exact"]["status"]=="PASS" and s["exists"]["status"]=="PASS")>=2
  rec["chains"].append(ce)
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()
