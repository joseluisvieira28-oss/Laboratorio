#!/usr/bin/env python3
import hashlib,json,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
SRC=Path("event_source/save0c-202205.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SIGNED_FLOW_SAVE0C_POPULATION_SAMPLE_RECEIPT_V0.1.json")
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"

def addr_key(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def rank(r):return hashlib.sha256((r["signature"]+"|"+addr_key(r["instructionAddress"])).encode()).hexdigest()
def as_int(v):
    try:return int(v) if v is not None else None
    except Exception:return None
def req(slot,retries=8):
    filt={"programId":[PROGRAM],"d1":["0x0c"],"isCommitted":True,"transaction":True,"transactionTokenBalances":True}
    body={"type":"solana","fromBlock":slot,"toBlock":slot,
      "fields":{
        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
        "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True},
        "tokenBalance":{"transactionIndex":True,"account":True,"preMint":True,"postMint":True,"preDecimals":True,"postDecimals":True,"preAmount":True,"postAmount":True}
      },"instructions":[filt]}
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={"Accept":"application/x-ndjson,application/json","Content-Type":"application/json","User-Agent":"crypto-lab-dls-signed-flow-sample/0.1"},method="POST")
    last=None
    for i in range(retries):
      try:
        with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
      except urllib.error.HTTPError as e:
        raw=e.read()
        if e.code==429 or 500<=e.code<600:
          last={"http":e.code};time.sleep(min(45,2**i));continue
        return int(e.code),raw
      except Exception as e:
        last={"error":type(e).__name__,"detail":str(e)[:200]};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

src=json.loads(SRC.read_text())
assert src["classification"]=="FIELD_ENRICHMENT_PARTITION_PASS"
rows=sorted(src["enriched_rows"],key=lambda r:(rank(r),r["signature"],addr_key(r["instructionAddress"])))[:64]
results=[];identity_conflicts=0

for n,e in enumerate(rows,1):
  sem=e["semantic_accounts"]
  roles={
   "debt_source":sem["source_liquidity_token_account"],
   "debt_reserve":sem["repay_reserve_liquidity_supply"],
   "collateral_reserve":sem["withdraw_reserve_collateral_supply"],
   "collateral_destination":sem["destination_collateral_token_account"]
  }
  st,raw=req(int(e["slot"]))
  rr={"sample_index":n,"rank":rank(e),"signature":e["signature"],"slot":e["slot"],"instructionAddress":e["instructionAddress"],"http_status":st,"roles":roles,"deltas":{},"classification":"SOURCE_EVIDENCE_INCOMPLETE"}
  if st!=200:
    rr["transport_error"]=raw[:500].decode("utf-8","replace");results.append(rr);continue
  exact=None;matching=[]
  balance_rows=[]
  for line in raw.decode("utf-8","replace").splitlines():
    if not line.strip():continue
    b=json.loads(line);tx_by={}
    for pos,tx in enumerate(b.get("transactions") or []):
      tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
    for ix in b.get("instructions") or []:
      tx=tx_by.get(ix.get("transactionIndex")) or {}
      sigs=tx.get("signatures") or [];sig=sigs[0] if sigs else None
      if ix.get("programId")==PROGRAM and tx.get("err") is None and ix.get("isCommitted") is True and ix.get("error") is None:
        item={"signature":sig,"instructionAddress":ix.get("instructionAddress"),"transactionIndex":ix.get("transactionIndex"),"accounts":ix.get("accounts") or []}
        matching.append(item)
        if sig==e["signature"] and ix.get("instructionAddress")==e["instructionAddress"]:exact=item
    balance_rows += b.get("tokenBalances") or []
  if exact is None:
    rr["identity_error"]="canonical_event_not_recovered";identity_conflicts+=1;results.append(rr);continue

  # Canonical role-account uniqueness among all successful matching liquidation instructions.
  role_accounts=set(roles.values())
  for role,account in roles.items():
    owner_instr=[m for m in matching if account in set(m["accounts"])]
    unique_to_event=(len(owner_instr)==1 and owner_instr[0]["signature"]==e["signature"] and owner_instr[0]["instructionAddress"]==e["instructionAddress"])
    vals=[]
    for tb in balance_rows:
      if tb.get("account")!=account:continue
      ti=tb.get("transactionIndex")
      if ti is not None and ti!=exact.get("transactionIndex"):continue
      if ti is None and not unique_to_event:continue
      vals.append(tb)
    merged={}
    for tb in vals:
      for k in ("preAmount","postAmount","preMint","postMint","preDecimals","postDecimals"):
        if tb.get(k) is not None:merged[k]=tb.get(k)
    pre=as_int(merged.get("preAmount"));post=as_int(merged.get("postAmount"))
    rr["deltas"][role]={"account":account,"pre":pre,"post":post,"delta_raw":(post-pre if pre is not None and post is not None else None),"unique_to_event":unique_to_event}

  ds={k:v["delta_raw"] for k,v in rr["deltas"].items()}
  complete=(set(ds)==set(roles) and all(v is not None for v in ds.values()))
  if complete:
    expected=(ds["debt_source"]<=0 and ds["debt_reserve"]>=0 and ds["collateral_reserve"]<=0 and ds["collateral_destination"]>=0 and any(v!=0 for v in ds.values()))
    rr["classification"]="AMOUNT_TRANSFER_PATTERN_PROVEN" if expected else "AMOUNT_EVIDENCE_COMPLETE_PATTERN_OTHER"
  results.append(rr)

complete=sum(1 for r in results if r["classification"]!="SOURCE_EVIDENCE_INCOMPLETE")
pattern=sum(1 for r in results if r["classification"]=="AMOUNT_TRANSFER_PATTERN_PROVEN")
coverage=complete/len(results)
classification="SAVE0C_SIGNED_FLOW_SAMPLE_SOURCE_PASS" if coverage>=0.95 and identity_conflicts==0 else "SAVE0C_SIGNED_FLOW_SAMPLE_SOURCE_BLOCKED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "population_partition":"save0c-202205","population_count":len(src["enriched_rows"]),"sample_count":len(results),
 "complete_amount_evidence_count":complete,"complete_amount_evidence_coverage":coverage,
 "expected_transfer_pattern_count":pattern,"identity_conflict_count":identity_conflicts,
 "results":results,"market_direction_proven":False,
 "firewall":{"prices":False,"returns":False,"market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"sample_count":len(results),"complete":complete,"coverage":coverage,"expected_pattern":pattern,"identity_conflicts":identity_conflicts},indent=2))
if classification!="SAVE0C_SIGNED_FLOW_SAMPLE_SOURCE_PASS":raise SystemExit(2)
