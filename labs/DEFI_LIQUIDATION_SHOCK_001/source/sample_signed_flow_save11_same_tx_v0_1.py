#!/usr/bin/env python3
import hashlib,json,time,urllib.error,urllib.request
from collections import Counter
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
SRC=Path("event_source/save11-202407.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SIGNED_FLOW_SAVE11_SAME_TX_PROGRAM_SAMPLE_RECEIPT_V0.1.json")
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"

def addr_key(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def rank(r):return hashlib.sha256((r["signature"]+"|"+addr_key(r["instructionAddress"])).encode()).hexdigest()
def req(slot,retries=8):
    body={"type":"solana","fromBlock":slot,"toBlock":slot,
      "fields":{"transaction":{"transactionIndex":True,"signatures":True,"err":True},
                "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                               "instructionAddress":True,"isCommitted":True,"error":True}},
      "instructions":[{"transaction":True}]}
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={"Accept":"application/x-ndjson,application/json","Content-Type":"application/json","User-Agent":"crypto-lab-dls-save11-same-tx/0.1"},method="POST")
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

src=json.loads(SRC.read_text())
assert src["classification"]=="FIELD_ENRICHMENT_PARTITION_PASS"
rows=sorted(src["enriched_rows"],key=lambda r:(rank(r),r["signature"],addr_key(r["instructionAddress"])))[:64]
results=[];all_program=Counter();after_program=Counter();seqs=Counter();conflicts=0
for n,e in enumerate(rows,1):
  st,raw=req(int(e["slot"]))
  rr={"sample_index":n,"rank":rank(e),"signature":e["signature"],"slot":e["slot"],"instructionAddress":e["instructionAddress"],
      "http_status":st,"classification":"SOURCE_EVIDENCE_INCOMPLETE","instructions":[]}
  if st!=200:
    rr["transport_error"]=raw[:500].decode("utf-8","replace");results.append(rr);continue
  ti=None;txerr=None;ins=[]
  for line in raw.decode("utf-8","replace").splitlines():
    if not line.strip():continue
    b=json.loads(line)
    for pos,tx in enumerate(b.get("transactions") or []):
      idx=tx.get("transactionIndex",tx.get("index",pos));sigs=tx.get("signatures") or []
      if sigs and sigs[0]==e["signature"]:
        if ti is not None and ti!=idx:conflicts+=1;rr["identity_error"]="multiple_transaction_indices"
        ti=idx;txerr=tx.get("err")
    ins += b.get("instructions") or []
  if ti is None or txerr is not None:
    conflicts+=1;rr["identity_error"]="canonical_transaction_not_recovered_successfully";results.append(rr);continue
  txins=[x for x in ins if x.get("transactionIndex")==ti]
  exact=[x for x in txins if x.get("programId")==PROGRAM and x.get("instructionAddress")==e["instructionAddress"]]
  if len(exact)!=1:
    conflicts+=1;rr["identity_error"]="canonical_instruction_match_count_"+str(len(exact));results.append(rr);continue
  ca=e["instructionAddress"]
  ordered=sorted(txins,key=lambda x:tuple(x.get("instructionAddress") or []))
  for x in ordered:
    a=x.get("instructionAddress") or []
    rel="AT" if a==ca else ("BEFORE" if tuple(a)<tuple(ca) else "AFTER")
    item={"programId":x.get("programId"),"instructionAddress":a,"relation":rel,"isCommitted":x.get("isCommitted"),"error":x.get("error")}
    rr["instructions"].append(item)
    if x.get("programId"):all_program[x["programId"]]+=1
    if rel=="AFTER" and x.get("programId"):after_program[x["programId"]]+=1
  seqs[">".join(x.get("programId") or "NULL" for x in ordered)]+=1
  rr["classification"]="SAME_TX_INSTRUCTION_CENSUS_COMPLETE"
  rr["instruction_count"]=len(ordered);rr["after_instruction_count"]=sum(1 for x in rr["instructions"] if x["relation"]=="AFTER")
  results.append(rr)

complete=sum(r["classification"]=="SAME_TX_INSTRUCTION_CENSUS_COMPLETE" for r in results)
classification="SAVE11_SAME_TX_PROGRAM_SAMPLE_PASS" if complete==64 and conflicts==0 else "SAVE11_SAME_TX_PROGRAM_SAMPLE_BLOCKED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "population_partition":"save11-202407","population_count":len(src["enriched_rows"]),"sample_count":64,
 "complete_count":complete,"identity_conflict_count":conflicts,
 "program_frequency":[{"programId":p,"count":n} for p,n in all_program.most_common()],
 "after_liquidation_program_frequency":[{"programId":p,"count":n} for p,n in after_program.most_common()],
 "ordered_program_sequence_frequency":[{"sequence":s,"count":n} for s,n in seqs.most_common()],
 "results":results,"program_semantics_labeled":False,"market_direction_proven":False,
 "firewall":{"prices":False,"returns":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"complete":complete,"identity_conflicts":conflicts,
 "top_after":receipt["after_liquidation_program_frequency"][:15]},indent=2))
if classification!="SAVE11_SAME_TX_PROGRAM_SAMPLE_PASS":raise SystemExit(2)
