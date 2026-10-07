#!/usr/bin/env python3
import json,hashlib,urllib.parse,urllib.request,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_4_index_free/BLOCK_INDEX_CAPABILITY_V043.json"
UA="CryptoLab-Unbonding-V043/1.1"
CHAINS=[
("cosmoshub",20000000,[("citizenweb3","https://rpc.cosmoshub-4-archive.citizenweb3.com"),("cryptocrew","https://rpc.cosmoshub-main.ccvalidators.com")]),
("osmosis",15000000,[("osmosis","https://rpc.osmosis.zone"),("validatus","https://rpc.archive.osmosis.validatus.com")]),
("celestia",2500000,[("kjnodes","http://136.243.94.113:26667"),("numia","https://public-celestia-rpc.numia.xyz")]),
("dydx",15000000,[("kingnodes","https://dydx-ops-archive-rpc.kingnodes.com"),("polkachu","https://dydx-dao-archive-rpc.polkachu.com")])]
def get(url,t=12):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=t) as r:return r.read()
def call(base,q):
 u=base.rstrip("/")+"/block_search?"+urllib.parse.urlencode({"query":json.dumps(q),"page":"1","per_page":"1","order_by":json.dumps("asc")})
 raw=get(u);o=json.loads(raw)
 if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
 rr=o.get("result") or {}; blocks=rr.get("blocks") or []
 first=None
 if blocks:
  x=blocks[0]; hd=((x.get("block") or {}).get("header") or {})
  first={"height":int(hd["height"]),"time":hd.get("time"),"hash":((x.get("block_id") or {}).get("hash"))}
 return {"status":"PASS","total_count":int(rr.get("total_count") or 0),"returned":len(blocks),
         "first":first,"sha256":hashlib.sha256(raw).hexdigest(),"url":u}
def main():
 rec={"parent_amendment":"6b7debcd7797cbbc1005c44c3762fc7202a4b6a2",
      "generated_utc":datetime.now(timezone.utc).isoformat(),
      "purpose":"strict dual block-index capability only; no census/materiality aggregation",
      "chains":[]}
 for chain,h,sources in CHAINS:
  ce={"chain":chain,"anchor":h,"window":[h-10000,h+10000],"sources":{}}
  for name,base in sources:
   se={"base":base}
   try: se["exact"]=call(base,f"block.height = {h}")
   except Exception as e: se["exact"]={"status":"FAIL","error":type(e).__name__+": "+str(e)[:500]}
   try: se["exists"]=call(base,f"complete_unbonding.amount EXISTS AND block.height >= {h-10000} AND block.height <= {h+10000}")
   except Exception as e: se["exists"]={"status":"FAIL","error":type(e).__name__+": "+str(e)[:500]}
   ce["sources"][name]=se
  vals=list(ce["sources"].items())
  strict=False; reasons=[]
  if len(vals)>=2:
   (n1,a),(n2,b)=vals[0],vals[1]
   anchor_ok=(a["exact"].get("status")=="PASS" and b["exact"].get("status")=="PASS" and
              a["exact"].get("total_count")==1 and b["exact"].get("total_count")==1 and
              a["exact"].get("first")==b["exact"].get("first"))
   event_ok=(a["exists"].get("status")=="PASS" and b["exists"].get("status")=="PASS" and
             a["exists"].get("total_count",0)>0 and
             a["exists"].get("total_count")==b["exists"].get("total_count") and
             a["exists"].get("first")==b["exists"].get("first"))
   strict=bool(anchor_ok and event_ok)
   reasons={"anchor_match":anchor_ok,"event_count_and_first_match":event_ok,
            "provider_a":n1,"provider_b":n2}
  ce["strict_two_provider_index_capability"]=strict
  ce["strict_details"]=reasons
  rec["chains"].append(ce)
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w",encoding="utf-8") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=="__main__":main()
