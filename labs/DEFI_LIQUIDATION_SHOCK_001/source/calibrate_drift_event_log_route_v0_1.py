#!/usr/bin/env python3
import hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
SRC=Path("drift_source/drift-202301.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_LIQUIDATION_EVENT_LOG_ROUTE_CALIBRATION_RECEIPT_V0.1.json")
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"

def ak(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def rk(r):return hashlib.sha256((r["signature"]+"|"+ak(r["instructionAddress"])).encode()).hexdigest()
def req(slot,retries=8):
 body={"type":"solana","fromBlock":slot,"toBlock":slot,
  "fields":{
   "transaction":{"transactionIndex":True,"signatures":True,"err":True},
   "log":{"programId":True,"message":True,"kind":True,"transactionIndex":True,"instructionAddress":True}
  },
  "transactions":[{}],"logs":[{}]}
 data=json.dumps(body,separators=(",",":")).encode()
 q=urllib.request.Request(STREAM,data=data,headers={"Accept":"application/x-ndjson,application/json","Content-Type":"application/json","User-Agent":"crypto-lab-dls-drift-event-log/0.1"},method="POST")
 last=None
 for i in range(retries):
  try:
   with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
  except urllib.error.HTTPError as e:
   raw=e.read()
   if e.code==429 or 500<=e.code<600:last={"http":e.code};time.sleep(min(45,2**i));continue
   return int(e.code),raw
  except Exception as e:last={"error":type(e).__name__,"detail":str(e)[:200]};time.sleep(min(45,2**i))
 raise RuntimeError(f"transport_exhausted:{last}")

o=json.loads(SRC.read_text())
assert o["classification"]=="FIELD_ENRICHMENT_PARTITION_PASS"
cand=[r for r in o["enriched_rows"] if r.get("class")=="liquidate_perp"]
refs=sorted(cand,key=lambda r:(rk(r),r["signature"],ak(r["instructionAddress"])))[:3]
results=[];conflicts=0
for ref in refs:
 st,raw=req(int(ref["slot"]))
 rr={"rank":rk(ref),"signature":ref["signature"],"slot":ref["slot"],"instructionAddress":ref["instructionAddress"],"http_status":st,"exact_transaction_found":False,"drift_log_count":0,"logs":[],"pass":False}
 if st!=200:rr["error"]=raw[:800].decode("utf-8","replace");results.append(rr);continue
 ti=None
 all_logs=[]
 for line in raw.decode("utf-8","replace").splitlines():
  if not line.strip():continue
  b=json.loads(line)
  for pos,tx in enumerate(b.get("transactions") or []):
   idx=tx.get("transactionIndex",tx.get("index",pos));sigs=tx.get("signatures") or []
   if sigs and sigs[0]==ref["signature"] and tx.get("err") is None:
    if ti is not None and ti!=idx:conflicts+=1;rr["identity_error"]="signature_multiple_transaction_indices"
    ti=idx
  all_logs += b.get("logs") or []
 if ti is None:
  conflicts+=1;rr["identity_error"]="exact_transaction_not_found";results.append(rr);continue
 rr["exact_transaction_found"]=True;rr["transactionIndex"]=ti
 for lg in all_logs:
  if lg.get("transactionIndex")!=ti:continue
  item={"programId":lg.get("programId"),"kind":lg.get("kind"),"message":lg.get("message"),"instructionAddress":lg.get("instructionAddress")}
  rr["logs"].append(item)
 rr["drift_log_count"]=sum(1 for x in rr["logs"] if x["programId"]==PROGRAM)
 rr["pass"]=rr["drift_log_count"]>0
 results.append(rr)
passed=sum(1 for x in results if x["pass"])
classification="DRIFT_LIQUIDATION_EVENT_LOG_ROUTE_3_OF_3_PASS" if passed==3 and conflicts==0 else "DRIFT_LIQUIDATION_EVENT_LOG_ROUTE_BLOCKED"
rec={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,"reference_count":3,"pass_count":passed,"identity_conflict_count":conflicts,"results":results,"direction_decoded":False,
"firewall":{"prices":False,"returns":False,"market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,"merge_main":False}}
OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"pass_count":passed,"identity_conflicts":conflicts,"summaries":[{"signature":x["signature"],"drift_log_count":x["drift_log_count"],"log_count":len(x["logs"]),"kinds":sorted(set(str(y["kind"]) for y in x["logs"]))} for x in results]},indent=2))
if classification!="DRIFT_LIQUIDATION_EVENT_LOG_ROUTE_3_OF_3_PASS":raise SystemExit(2)
