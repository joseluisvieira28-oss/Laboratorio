#!/usr/bin/env python3
"""DLS Protected-2025 Route A2 boundary index. Source-only; no market outcomes."""
import datetime as dt,json,os,time,urllib.request,urllib.error
from pathlib import Path
PROGRAMS={"marginfi":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA","save":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","kamino":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"}
START=1735689600; END=1767225600
OUT=Path("route_a2_boundary"); OUT.mkdir(exist_ok=True)
url=("https://mainnet.helius-rpc.com/?api-key="+os.environ["HELIUS_API_KEY"]) if os.environ.get("HELIUS_API_KEY") else os.environ.get("DLS_RPC_URL")
if not url: raise SystemExit("credential_absent")
def call(method,params):
  payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
  for n in range(3):
    try:
      with urllib.request.urlopen(urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json"}),timeout=30) as r:o=json.loads(r.read())
      if o.get("error"): raise RuntimeError("rpc_error")
      time.sleep(.26); return o["result"]
    except (urllib.error.URLError,TimeoutError,OSError):
      if n==2: raise
      time.sleep(2**n)
def iso(ts): return dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat().replace("+00:00","Z")
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":"ROUTE_A2_BOUNDARY_INDEX_BLOCKED","programs":{},"firewall":{"economic_outcomes_opened":False,"prices_2025":False,"returns_2025":False,"pnl_2025":False,"data_2026_transactions_opened":False,"science_changed":False,"live_trading":False,"merge_main":False}}
errors=[]
for name,program in PROGRAMS.items():
  before=None; pages=0; rows=[]; crossed=False
  while pages<200:
    cfg={"limit":1000,"commitment":"finalized"}
    if before: cfg["before"]=before
    page=call("getSignaturesForAddress",[program,cfg]); pages+=1
    if not page: errors.append({"program":name,"reason":"history_exhausted_before_2025"}); break
    # Firewall: do not retain 2026 rows; only use them to advance cursor.
    for x in page:
      bt=x.get("blockTime")
      if isinstance(bt,int) and START<=bt<END: rows.append({"signature":x["signature"],"slot":x["slot"],"blockTime":bt})
    times=[x.get("blockTime") for x in page if isinstance(x.get("blockTime"),int)]
    if times and min(times)<START: crossed=True; break
    nxt=page[-1]["signature"]
    if nxt==before: errors.append({"program":name,"reason":"nonadvancing_cursor"}); break
    before=nxt
  if not crossed: errors.append({"program":name,"reason":"lower_boundary_not_reached","pages":pages})
  rows.sort(key=lambda x:(x["blockTime"],x["slot"],x["signature"]))
  boundaries={}
  for m in range(1,13):
    a=int(dt.datetime(2025,m,1,tzinfo=dt.timezone.utc).timestamp())
    b=int((dt.datetime(2026,1,1,tzinfo=dt.timezone.utc) if m==12 else dt.datetime(2025,m+1,1,tzinfo=dt.timezone.utc)).timestamp())
    month=[x for x in rows if a<=x["blockTime"]<b]
    boundaries[f"2025{m:02d}"]={"start":iso(a),"end":iso(b),"program_signature_count":len(month),"newest_signature":month[-1]["signature"] if month else None,"oldest_signature":month[0]["signature"] if month else None}
  receipt["programs"][name]={"program":program,"pages":pages,"in_2025_signature_count":len(rows),"boundaries":boundaries}
receipt["errors"]=errors
receipt["classification"]="ROUTE_A2_BOUNDARY_INDEX_PASS" if not errors else "ROUTE_A2_BOUNDARY_INDEX_BLOCKED"
(OUT/"DLS_ROUTE_A2_2025_BOUNDARY_INDEX_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"programs":{k:{"pages":v["pages"],"in_2025_signature_count":v["in_2025_signature_count"]} for k,v in receipt["programs"].items()},"errors":errors},indent=2))
if errors: raise SystemExit(2)
