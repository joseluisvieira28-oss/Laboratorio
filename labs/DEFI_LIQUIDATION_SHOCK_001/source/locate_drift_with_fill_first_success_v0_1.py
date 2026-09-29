#!/usr/bin/env python3
import datetime as dt,json,time,urllib.error,urllib.request
from pathlib import Path
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
D8="5f6f7c6956a9bb22"
START="2022-11-04T15:17:54Z";END="2025-01-01T00:00:00Z"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_WITH_FILL_FIRST_SUCCESS_LOCATOR_RECEIPT_V0.1.json")
def iso(s):return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def req(url,body=None,retries=10):
 data=None if body is None else json.dumps(body,separators=(",",":")).encode()
 h={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-drift-with-fill-locator/0.1"}
 if data is not None:h["Content-Type"]="application/json"
 q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
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
def ts_slot(s):
 st,raw=req(f"{TSROOT}/{int(iso(s).timestamp())}/block")
 if st!=200:raise RuntimeError(f"timestamp_http_{st}")
 o=json.loads(raw)
 if isinstance(o,int):return o
 for k in ("block","block_number","number","slot"):
  if isinstance(o.get(k),int):return o[k]
 raise RuntimeError("timestamp_schema")
lo=int(iso(START).timestamp());hi=int(iso(END).timestamp())
current=ts_slot(START);to=ts_slot(END)+16;requests=0;found=None;terms=[]
while current<=to and found is None:
 body={"type":"solana","fromBlock":current,"toBlock":to,
  "fields":{"block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"data":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True}},
  "instructions":[{"programId":[PROGRAM],"d8":["0x"+D8],"transaction":True}]}
 st,raw=req(STREAM,body);requests+=1
 if st==204:terms.append({"http_status":204,"from_slot":current});break
 if st!=200:raise RuntimeError(f"stream_http_{st}")
 docs=[json.loads(x) for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
 if not docs:terms.append({"http_status":200,"from_slot":current,"reason":"empty"});break
 last=None
 candidates=[]
 for b in docs:
  hdr=b.get("header") or {};slot=hdr.get("number");ts=hdr.get("timestamp")
  if isinstance(slot,int):last=slot if last is None else max(last,slot)
  if isinstance(ts,(int,float)):ts=dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat().replace("+00:00","Z")
  if not isinstance(ts,str):continue
  bt=int(iso(ts).timestamp())
  if not(lo<=bt<hi):continue
  tx_by={}
  for pos,tx in enumerate(b.get("transactions") or []):tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
  for ix in b.get("instructions") or []:
   ti=ix.get("transactionIndex");tx=tx_by.get(ti)
   if not isinstance(tx,dict) or tx.get("err") is not None or ix.get("isCommitted") is not True or ix.get("error") is not None:continue
   sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
   addr=ix.get("instructionAddress")
   if sig and isinstance(addr,list):
    candidates.append({"signature":sig,"slot":slot,"timestamp":ts,"transactionIndex":ti,"instructionAddress":addr,"instruction_data_base58":ix.get("data")})
 if candidates:
  found=sorted(candidates,key=lambda x:(x["timestamp"],x["slot"],x["signature"],json.dumps(x["instructionAddress"],separators=(",",":"))))[0]
  break
 if last is None:raise RuntimeError("no_block_number")
 if last<current:raise RuntimeError("non_advancing_stream")
 current=last+1
classification="DRIFT_WITH_FILL_FIRST_SUCCESS_FOUND_PENDING_RAW_SEMANTICS" if found else "DRIFT_WITH_FILL_FIRST_SUCCESS_NOT_FOUND"
rec={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "discriminator_hex":D8,"window":{"start":START,"end_exclusive":END},"request_count":requests,
 "candidate":found,"termination_evidence":terms,
 "census_authority":False,
 "firewall":{"prices":False,"returns":False,"market_2025_opened":False,"market_2026_opened":False,
 "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,indent=2,sort_keys=True))
