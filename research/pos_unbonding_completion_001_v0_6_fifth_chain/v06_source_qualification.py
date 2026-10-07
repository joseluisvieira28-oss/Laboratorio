#!/usr/bin/env python3
import json,hashlib,urllib.request,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_6_fifth_chain/V06_SOURCE_QUALIFICATION.json"
C=[
("cro","crypto-org-chain-mainnet-1",[5000000,10000000,15000000],[("official","https://rpc.mainnet.crypto.org"),("ecostake","https://rpc-cryptoorgchain.ecostake.com"),("publicnode","https://cro-chain-rpc.publicnode.com"),("polkachu","https://cryptocom-rpc.polkachu.com")]),
("evmos","evmos_9001-2",[5000000,10000000,15000000],[("lavenderfive","https://rpc.lavenderfive.com/evmos"),("blockdaemon","https://tendermint.bd.evmos.org:26657"),("publicnode","https://evmos-rpc.publicnode.com"),("citizenweb3","https://rpc.evmos.citizenweb3.com")]),
("juno","juno-1",[5000000,10000000,15000000],[("lavenderfive","https://rpc.lavenderfive.com/juno"),("validatus","https://rpc.juno.validatus.com"),("publicnode","https://juno-rpc.publicnode.com"),("polkachu","https://juno-rpc.polkachu.com")])]
def get(u,t=12):
 req=urllib.request.Request(u,headers={"User-Agent":"CryptoLab-Unbonding-V06/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=t) as r:return r.read()
def main():
 rec={"freeze_commit":"e8a3e4b4eb07142d40abc781230235f7ea9d3c53","event_counts_opened":False,"generated_utc":datetime.now(timezone.utc).isoformat(),"results":[]}
 for chain,cid,hs,srcs in C:
  ce={"chain":chain,"sources":{},"pairs":[]}
  for n,b in srcs:
   se={}
   for h in hs:
    try:
     raw=get(b.rstrip("/")+"/block?height="+str(h));o=json.loads(raw);rr=o.get("result") or {};hd=((rr.get("block") or {}).get("header") or {});bh=((rr.get("block_id") or {}).get("hash"))
     se[str(h)]={"status":"PASS" if hd.get("chain_id")==cid else "WRONG_CHAIN","hash":bh,"app_hash":hd.get("app_hash"),"time":hd.get("time"),"sha256":hashlib.sha256(raw).hexdigest()}
    except Exception as e:se[str(h)]={"status":"FAIL","error":type(e).__name__+": "+str(e)[:350]}
   ce["sources"][n]=se
  ns=list(ce["sources"])
  for i in range(len(ns)):
   for j in range(i+1,len(ns)):
    mm=[]
    for h in hs:
     a=ce["sources"][ns[i]][str(h)];b=ce["sources"][ns[j]][str(h)]
     if a.get("status")=="PASS" and b.get("status")=="PASS" and a.get("hash")==b.get("hash") and a.get("app_hash")==b.get("app_hash") and a.get("time")==b.get("time"):mm.append(h)
    if mm:ce["pairs"].append({"a":ns[i],"b":ns[j],"matching_heights":mm})
  ce["two_source_pass"]=any(len(p["matching_heights"])>=2 for p in ce["pairs"])
  rec["results"].append(ce)
  if ce["two_source_pass"]:break
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()
