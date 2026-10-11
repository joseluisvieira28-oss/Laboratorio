#!/usr/bin/env python3
"""SOURCE-ONLY frozen technical probe: inspect shape of official 2026-10-10 fills."""
from datetime import datetime,timezone,timedelta
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import time
from collections import Counter
from decimal import Decimal
AF="0x"+"fe"*20
OUT=Path("research/hype_buyback_flow_001/receipts/official_diag_v041")
OUT.mkdir(parents=True,exist_ok=True)
start=datetime(2026,10,10,tzinfo=timezone.utc)
end=start+timedelta(days=1)-timedelta(milliseconds=1)
body={"type":"userFillsByTime","user":AF,"startTime":int(start.timestamp()*1000),"endTime":int(end.timestamp()*1000),"aggregateByTime":False}
request_bytes=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
t=time.monotonic()
requested=datetime.now(timezone.utc).isoformat()
with urllib.request.urlopen(urllib.request.Request("https://api.hyperliquid.xyz/info",data=request_bytes,headers={"Content-Type":"application/json"},method="POST"),timeout=16) as r:
    raw=r.read(2500000);status=r.status
rows=json.loads(raw)
if not isinstance(rows,list):raise ValueError("non-list")
records=[]
for r in rows:
    sec=datetime.fromtimestamp(r["time"]/1000,tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    records.append({"time_ms":r["time"],"time_second_utc":sec,"coin":r.get("coin"),"side":r.get("side"),"px":str(r.get("px")),"sz":str(r.get("sz")),"hash":r.get("hash"),"tid":r.get("tid")})
obj={"phase":"SOURCE_ONLY","market_outcomes":0,"status":"IDENTITY_DIAGNOSTIC_ONLY",
     "run_id":os.environ.get("GITHUB_RUN_ID","LOCAL"),"request_sha256":hashlib.sha256(request_bytes).hexdigest(),
     "raw_http_sha256":hashlib.sha256(raw).hexdigest(),"http_code":status,"raw_rows":len(rows),
     "requested_at_utc":requested,"received_at_utc":datetime.now(timezone.utc).isoformat(),
     "latency_ms":round((time.monotonic()-t)*1000,3),
     "first_three_official_fills":records[:3],"last_two_official_fills":records[-2:],
     "official_unique_tids":len(set(str(r.get("tid")) for r in rows)),
     "official_coin_side_groups":dict(Counter(str(r.get("coin"))+"|"+str(r.get("side")) for r in rows)),
     "csv_2026_10_10_expected_rows":420,"csv_zero_hash_expected":47,
     "export_exact_multiset_was_sha_mismatch":True,"no_source_promotion":True}
(OUT/"OFFICIAL_2026_10_10_TECH_IDENTITY_DIAG_V041.json").write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
print(json.dumps(obj,indent=2,sort_keys=True))
