#!/usr/bin/env python3
import json,hashlib,urllib.request,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_5_source_expansion/COREUM_SOURCE_B_PROBE_V051.json"
H=[5000000,10000000,15000000]
REF={5000000:"D8A6B584C70FE38CD7D160A7F5151974E595AD9E241700F80D45AF15F53B0FF9",10000000:"227EE3C00731C6544D88478F9022100214767E0DF8779C66433BF5C0BB810F47",15000000:"DE285C3282D4EAC0EA6AF0FDAB0EF3F45273D5BB96289A76EA501CEDB52B1516"}
S=[("nownodes","https://public-coreum.nownodes.io"),("official_full","https://full-node.mainnet-1.coreum.dev:26657"),("stakewolle","https://public.stakewolle.com/cosmos/coreum/rpc"),("chainroot","https://coreum-rpc.chainroot.io"),("ibs","https://coreum.ibs.team/rpc"),("genznodes","https://coreum-rpc.genznodes.dev")]
def get(u,t=15):
 req=urllib.request.Request(u,headers={"User-Agent":"CryptoLab-Unbonding-V051/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=t) as r:return r.read()
def main():
 rec={"generated_utc":datetime.now(timezone.utc).isoformat(),"reference":"TX Foundation archive fixed-height hashes from V0.5","sources":{}}
 for n,b in S:
  se={}
  for h in H:
   try:
    raw=get(b.rstrip("/")+"/block?height="+str(h));o=json.loads(raw);rr=o.get("result") or {};hd=((rr.get("block") or {}).get("header") or {});bh=((rr.get("block_id") or {}).get("hash"))
    se[str(h)]={"status":"PASS" if hd.get("chain_id")=="coreum-mainnet-1" else "WRONG_CHAIN","hash":bh,"matches_reference":bh==REF[h],"time":hd.get("time"),"sha256":hashlib.sha256(raw).hexdigest()}
   except Exception as e:se[str(h)]={"status":"FAIL","error":type(e).__name__+": "+str(e)[:500]}
  rec["sources"][n]=se
 rec["passing_source_b"]=[n for n,se in rec["sources"].items() if all(se[str(h)].get("matches_reference") for h in H)]
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()

# trigger
