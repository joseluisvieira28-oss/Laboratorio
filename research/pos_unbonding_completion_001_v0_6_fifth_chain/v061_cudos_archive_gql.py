#!/usr/bin/env python3
import json,urllib.request,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_6_fifth_chain/CUDOS_ARCHIVE_GQL_PROBE_V061.json"
URL="https://archive-explorer-gql.cudos.org/v1/graphql"
def post(q):
 raw=json.dumps({"query":q}).encode();req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-V061/1.0"})
 with urllib.request.urlopen(req,timeout=25) as r:return json.loads(r.read())
def main():
 rec={"generated_utc":datetime.now(timezone.utc).isoformat(),"event_counts_opened":False,"url":URL}
 try:
  o=post("{block_by_pk(height:15000000){height hash timestamp num_txs}}")
  rec["status"]="PASS";rec["block_15000000"]=o.get("data",{}).get("block_by_pk"); rec["cro_reference_hash"]="0E7F1A3C5CC92A1592828EA28594C23523CB56008EFAAAA30E405212082379D7"; rec["matches_cro_reference"]=((rec["block_15000000"] or {}).get("hash","").upper()==rec["cro_reference_hash"])
 except Exception as e:rec["status"]="FAIL";rec["error"]=type(e).__name__+": "+str(e)[:1000]
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()

# trigger
