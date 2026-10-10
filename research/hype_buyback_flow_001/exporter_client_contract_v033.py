#!/usr/bin/env python3
"""Public JS client transport-contract inspection only. No wallet, export job or market outcomes."""
import hashlib,json,os,re,time
from urllib import request
from datetime import datetime,timezone
from pathlib import Path

URL="https://trade-export.hypedexer.com/_next/static/chunks/1a4537d13be41f02.js"
OUT=Path("research/hype_buyback_flow_001/receipts/export_client_contract_v033")
OUT.mkdir(parents=True,exist_ok=True)
now=lambda:datetime.now(timezone.utc).isoformat()
r={"phase":"SOURCE_ONLY","candidate_id":"HYPE-BUYBACK-FLOW-001","url":URL,"method":"GET",
   "export_jobs_created":0,"address_requests":0,"keys_used":0,"paid_data":0,
   "market_outcomes_opened":0,"trading_authority":"NONE",
   "run_id":os.environ.get("GITHUB_RUN_ID","LOCAL"),"head_sha":os.environ.get("GITHUB_SHA","UNSET"),
   "requested_at_utc":now()}
tic=time.monotonic()
req=request.Request(URL,headers={"User-Agent":"CryptoLab-Research-StaticClientRead/0.3.3"})
with request.urlopen(req,timeout=14) as res:
    b=res.read(200001)
    r["status"]=res.status
r["bytes"]=len(b)
r["sha256"]=hashlib.sha256(b).hexdigest()
r["received_utc"]=now()
r["roundtrip_ms"]=round(1000*(time.monotonic()-tic),2)
if len(b)>200000:raise ValueError("public_static_asset_too_large")
text=b.decode("utf-8","replace")
tokens=("https://api.hypedexer.com/fills/export/jobs/","https://api.hypedexer.com/fills/user/",
        "/export/csv","exportUrl","downloadUrl","quota","429","POST","startDate","endDate")
out={}
for tok in tokens:
    occ=[m.start() for m in re.finditer(re.escape(tok),text,re.I)]
    out[tok]={"occurrences":len(occ),"contexts":[text[max(0,at-350):min(len(text),at+650)] for at in occ[:2]]}
r["PUBLIC_CODE_CONTEXTS"]=out
(OUT/"SOURCE_EXPORT_CLIENT_CONTRACT_V033.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print(json.dumps(r,indent=2,sort_keys=True))
