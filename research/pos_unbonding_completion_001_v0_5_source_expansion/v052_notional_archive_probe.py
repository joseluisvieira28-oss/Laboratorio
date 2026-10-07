#!/usr/bin/env python3
import json,urllib.request,hashlib,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_5_source_expansion/NOTIONAL_ARCHIVE_PROBE_V052.json"
T=[
("terra2",5000000,"phoenix-1","https://terra2.validator.network"),
("terra",5000000,"phoenix-1","https://terra.validator.network"),
("coreum",5000000,"coreum-mainnet-1","https://coreum.validator.network")]
def main():
 rec={"generated_utc":datetime.now(timezone.utc).isoformat(),"event_counts_opened":False,"probes":[]}
 for n,h,c,b in T:
  x={"name":n,"base":b,"height":h}
  try:
   req=urllib.request.Request(b+f"/block?height={h}",headers={"User-Agent":"CryptoLab-V052/1.0"})
   with urllib.request.urlopen(req,timeout=20) as r:raw=r.read()
   o=json.loads(raw);rr=o.get("result") or {};hd=((rr.get("block") or {}).get("header") or {})
   x.update(status="PASS" if hd.get("chain_id")==c else "WRONG_CHAIN",chain_id=hd.get("chain_id"),time=hd.get("time"),hash=((rr.get("block_id") or {}).get("hash")),sha256=hashlib.sha256(raw).hexdigest())
  except Exception as e:x.update(status="FAIL",error=type(e).__name__+": "+str(e)[:500])
  rec["probes"].append(x)
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()

# trigger
