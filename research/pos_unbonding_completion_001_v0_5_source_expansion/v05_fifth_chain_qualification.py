#!/usr/bin/env python3
import json,hashlib,urllib.request,urllib.error,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_5_source_expansion/V05_FIFTH_CHAIN_QUALIFICATION.json"
UA="CryptoLab-Unbonding-V05/1.0"
C=[
 {"chain":"terra2","chain_id":"phoenix-1","heights":[5000000,8000000,10000000],"sources":[
  ["allthatnode","https://terra-mainnet-archive.allthatnode.com:26657"],
  ["lavenderfive","https://rpc.lavenderfive.com/terra2"],
  ["publicnode","https://terra-rpc.publicnode.com"],
  ["polkachu","https://terra-rpc.polkachu.com"]]},
 {"chain":"archway","chain_id":"archway-1","heights":[1000000,3000000,5000000],"sources":[
  ["allthatnode","https://archway-mainnet-archive.allthatnode.com:26657"],
  ["foundation","https://rpc.mainnet.archway.io"],
  ["kjnodes","https://archway.rpc.kjnodes.com"],
  ["lavenderfive","https://rpc.lavenderfive.com/archway"]]},
 {"chain":"coreum","chain_id":"coreum-mainnet-1","heights":[5000000,10000000,15000000],"sources":[
  ["foundation_archive","https://archive.rpc.mainnet-1.tx.org"],
  ["publicnode","https://coreum-rpc.publicnode.com"],
  ["ecostake","https://rpc-coreum.ecostake.com"],
  ["polkachu","https://coreum-rpc.polkachu.com"]]}]
def get(url,t=15):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=t) as r:return r.read()
def block(base,h):
 raw=get(base.rstrip("/")+"/block?height="+str(h));o=json.loads(raw)
 if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
 rr=o.get("result") or {};hd=((rr.get("block") or {}).get("header") or {})
 if not hd:raise RuntimeError("no block header")
 return {"height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),"hash":((rr.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),"sha256":hashlib.sha256(raw).hexdigest()}
def main():
 rec={"freeze_commit":"9b63d80833ca7524343dbb33c3caaee0aae1b5af","generated_utc":datetime.now(timezone.utc).isoformat(),"event_counts_opened":False,"results":[]}
 selected=None
 for spec in C:
  ce={"chain":spec["chain"],"chain_id":spec["chain_id"],"sources":{},"pairs":[]}
  for name,base in spec["sources"]:
   se={"base":base,"blocks":{}}
   for h in spec["heights"]:
    try:
     b=block(base,h)
     se["blocks"][str(h)]={"status":"PASS",**b} if b["chain_id"]==spec["chain_id"] else {"status":"WRONG_CHAIN",**b}
    except Exception as e:se["blocks"][str(h)]={"status":"FAIL","error":type(e).__name__+": "+str(e)[:500]}
   ce["sources"][name]=se
  names=list(ce["sources"])
  for i in range(len(names)):
   for j in range(i+1,len(names)):
    a,b=names[i],names[j];matches=[]
    for h in spec["heights"]:
     x=ce["sources"][a]["blocks"][str(h)];y=ce["sources"][b]["blocks"][str(h)]
     if x.get("status")=="PASS" and y.get("status")=="PASS" and x.get("hash")==y.get("hash") and x.get("app_hash")==y.get("app_hash") and x.get("time")==y.get("time"):matches.append(h)
    if matches:ce["pairs"].append({"a":a,"b":b,"matching_heights":matches})
  ce["two_source_fixed_height_pass"]=any(len(p["matching_heights"])>=2 for p in ce["pairs"])
  rec["results"].append(ce)
  if ce["two_source_fixed_height_pass"]:
   selected=spec["chain"];break
 rec["selected_first_passing_chain"]=selected
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()
