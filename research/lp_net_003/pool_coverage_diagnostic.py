#!/usr/bin/env python3
"""Secondary unranked source diagnostic for two immutable LP-NET-003 pools.

Explains absent pool from one market-data provider; does NOT change frozen
eligibility, pool universe, fee economics or prior as-of snapshot.
"""
import argparse,json,hashlib
from pathlib import Path
from urllib.request import Request,urlopen
from frozen_pool_snapshot import POOLS

def get(url):
 try:
  r=Request(url,headers={"Accept":"application/json","User-Agent":"LP-NET-003-source-diagnostic/0.1"})
  with urlopen(r,timeout=14) as res:raw=res.read(800000)
  j=json.loads(raw)
  return {"status":"RECEIVED","sha256":hashlib.sha256(raw).hexdigest(),"payload":j}
 except Exception as e:
  return {"status":"SOURCE_BLOCKED","error_type":type(e).__name__,"error":str(e)[:140]}

def main():
 p=argparse.ArgumentParser();p.add_argument("--output",required=True,type=Path)
 a=p.parse_args()
 results=[]
 for name,obj in POOLS.items():
  addr=obj["address"]
  urls={
   "geckoterminal":"https://api.geckoterminal.com/api/v2/networks/eth/pools/"+addr,
   "dexscreener":"https://api.dexscreener.com/latest/dex/pairs/ethereum/"+addr}
  out={"pool":name,"address":addr}
  for provider,url in urls.items():
   x=get(url);record={"status":x["status"],"sha256":x.get("sha256")}
   if x["status"]=="RECEIVED":
    body=x["payload"]
    if provider=="geckoterminal":
     dat=body.get("data") if isinstance(body,dict) else None
     attr=dat.get("attributes",{}) if isinstance(dat,dict) else {}
     record.update({"pair_address":attr.get("address"),"api_errors":body.get("errors"),
       "reserve_in_usd":attr.get("reserve_in_usd"),"volume_usd_h24":attr.get("volume_usd",{}).get("h24")})
    else:
     pairs=body.get("pairs") if isinstance(body,dict) else None
     record.update({"pairs_count":len(pairs) if isinstance(pairs,list) else None,
        "pair_addresses":[z.get("pairAddress") for z in (pairs or [])[:5]],
        "chain_ids":[z.get("chainId") for z in (pairs or [])[:5]]})
   else:record["error"]=x.get("error")
   out[provider]=record
  results.append(out)
 obj={"study":"LP-NET-003-POOL-COVERAGE-DIAGNOSTIC","research_only":True,
    "changes_prior_selection":False,"pool_coverage":results,"economic_verdict":"NO_LIVE_GO"}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(obj,indent=2),encoding="utf-8")
 print(json.dumps({"coverage":[{k:row[k] for k in ("pool","geckoterminal","dexscreener")} for row in results],
                  "economic_verdict":obj["economic_verdict"]}))
if __name__=="__main__":main()
