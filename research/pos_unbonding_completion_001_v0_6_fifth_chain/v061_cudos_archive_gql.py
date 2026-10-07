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
  o=post("{__type(name:\"block\"){fields{name type{kind name ofType{kind name}}}}}")
  rec["status"]="PASS";rec["block_fields"]=o.get("data",{}).get("__type",{}).get("fields",[])
 except Exception as e:rec["status"]="FAIL";rec["error"]=type(e).__name__+": "+str(e)[:1000]
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()

# trigger
