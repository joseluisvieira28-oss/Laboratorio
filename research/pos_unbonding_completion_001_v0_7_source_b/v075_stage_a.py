#!/usr/bin/env python3
import json,time,urllib.request,urllib.parse,urllib.error,os
from datetime import datetime,timezone

OUT="research/pos_unbonding_completion_001_v0_7_source_b/V075_STAGE_A_INDEX_COUNTS.json"
UA="CryptoLab-Unbonding-V075-StageA/1.0"
START=datetime.fromisoformat("2023-01-01T00:00:00+00:00")
END=datetime.fromisoformat("2025-01-01T00:00:00+00:00")

CHAINS=[
 {"chain":"ATOM","id":"cosmoshub-4","a":"https://rpc.cosmoshub-4-archive.citizenweb3.com","b":"https://rpc.cosmoshub-main.ccvalidators.com"},
 {"chain":"OSMO","id":"osmosis-1","a":"https://rpc.archive.osmosis.validatus.com"},
 {"chain":"TIA","id":"celestia","a":"http://136.243.94.113:26667"},
 {"chain":"DYDX","id":"dydx-mainnet-1","a":"https://dydx-ops-archive-rpc.kingnodes.com","b":"https://dydx-dao-archive-rpc.polkachu.com"},
 {"chain":"COREUM","id":"coreum-mainnet-1","a":"https://archive.rpc.mainnet-1.tx.org"},
]

def fetch(url,timeout=25,retries=5):
 last=None
 for i in range(retries):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
   with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())
  except Exception as e:
   last=e;time.sleep(min(2**i,8))
 raise last

def rpc(base,path,params=None):
 u=base.rstrip("/")+"/"+path.lstrip("/")
 if params:u+="?"+urllib.parse.urlencode(params)
 o=fetch(u)
 if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
 return o.get("result") or {}

def status(base):
 r=rpc(base,"status");return int((r.get("sync_info") or {}).get("latest_block_height"))

def block(base,h):
 r=rpc(base,"block",{"height":str(h)})
 hd=((r.get("block") or {}).get("header") or {})
 if not hd:raise RuntimeError("no block header")
 return {"height":int(hd["height"]),"time":hd["time"],"chain_id":hd.get("chain_id"),"hash":((r.get("block_id") or {}).get("hash"))}

def dt(s):return datetime.fromisoformat(s.replace("Z","+00:00"))

def first_at_or_after(base,target):
 hi=status(base);lo=1
 # If genesis is later than target, return genesis.
 b1=block(base,1)
 if dt(b1["time"])>=target:return 1,b1
 while lo<hi:
  m=(lo+hi)//2
  try:b=block(base,m)
  except Exception:
   lo=m+1;continue
  if dt(b["time"])<target:lo=m+1
  else:hi=m
 b=block(base,lo);return lo,b

def last_before(base,target_exclusive):
 h,b=first_at_or_after(base,target_exclusive)
 if dt(b["time"])>=target_exclusive and h>1:
  h-=1;b=block(base,h)
 return h,b

def count(base,lo,hi):
 q=f"complete_unbonding.amount EXISTS AND block.height >= {lo} AND block.height <= {hi}"
 p={"query":json.dumps(q),"page":"1","per_page":"1","order_by":json.dumps("asc")}
 r=rpc(base,"block_search",p)
 return {"total_count":int(r.get("total_count") or 0),"query":q,
         "first_returned_height":int((((r.get("blocks") or [{}])[0].get("block") or {}).get("header") or {}).get("height") or 0) if (r.get("blocks") or []) else None}

def main():
 rec={"freeze_branch":"unbonding-v075-census-freeze-7d2ee458-2026-10-07",
      "freeze_sha256":"7d2ee45837d7b6e07365a90db922815f63a183906e59f15a223acf891de6c8d5",
      "market_outcomes_opened":False,"generated_utc":datetime.now(timezone.utc).isoformat(),"chains":[]}
 for spec in CHAINS:
  ce={"chain":spec["chain"],"chain_id":spec["id"],"sources":{}}
  try:
   lo,lb=first_at_or_after(spec["a"],START)
   hi,hb=last_before(spec["a"],END)
   ce["bounds"]={"lo":lo,"lo_block":lb,"hi":hi,"hi_block":hb}
   if lb.get("chain_id")!=spec["id"] or hb.get("chain_id")!=spec["id"]:raise RuntimeError("chain_id mismatch")
   for label in ("a","b"):
    if label not in spec:continue
    base=spec[label]
    se={"base":base}
    try:
     # exact-bound canonical checks plus completion count
     se["lo_block"]=block(base,lo);se["hi_block"]=block(base,hi)
     se["completion_index"]=count(base,lo,hi)
     se["status"]="PASS"
    except Exception as e:
     se["status"]="FAIL";se["error"]=type(e).__name__+": "+str(e)[:800]
    ce["sources"][label]=se
   ce["stage_a_pass"]=ce["sources"].get("a",{}).get("status")=="PASS"
   if "b" in spec:
    a=ce["sources"].get("a",{});b=ce["sources"].get("b",{})
    ce["dual_count_match"]=a.get("status")=="PASS" and b.get("status")=="PASS" and a["completion_index"]["total_count"]==b["completion_index"]["total_count"]
  except Exception as e:
   ce["stage_a_pass"]=False;ce["error"]=type(e).__name__+": "+str(e)[:1000]
  rec["chains"].append(ce)
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()

# trigger\n