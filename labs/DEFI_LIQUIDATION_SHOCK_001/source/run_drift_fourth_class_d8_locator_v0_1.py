#!/usr/bin/env python3
import argparse, datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
CLASS="liquidate_borrow_for_perp_pnl"
PREFIX="a911205acf94d11b"
CAL=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_SQD_SINGLE_D8_CALIBRATION_RECEIPT_V0.1.json")
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw
def iso_dt(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm_ts(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-drift-fourth-locator/0.1"}
    if data is not None: headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=120) as r:return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(60,2**i));continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")
def ts_slot(s):
    unix=int(iso_dt(s).timestamp());st,h,raw=req(f"{TSROOT}/{unix}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    obj=json.loads(raw)
    if isinstance(obj,int):return obj
    if isinstance(obj,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(obj.get(k),int):return obj[k]
    raise RuntimeError("timestamp_resolver_schema")

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True);ap.add_argument("--end",required=True);ap.add_argument("--out",required=True)
args=ap.parse_args()

if not CAL.exists(): raise SystemExit("missing_calibration_receipt")
cal=json.loads(CAL.read_text())
if cal.get("classification")!="DRIFT_SQD_SINGLE_D8_EXACT_EQUIVALENCE_PASS":
    raise SystemExit("calibration_not_pass")

lo=iso_dt(args.start);hi=iso_dt(args.end);LO=int(lo.timestamp());HI=int(hi.timestamp())
from_slot=ts_slot(args.start);to_slot=ts_slot(args.end)+16;current=from_slot
rows=[];term=[];requests=0
while current<=to_slot:
    body={"type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{"block":{"number":True,"timestamp":True},
                    "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                    "instruction":{"programId":True,"data":True,"transactionIndex":True,
                                   "instructionAddress":True,"isCommitted":True,"error":True}},
          "instructions":[{"programId":[PROGRAM],"d8":["0x"+PREFIX],"transaction":True}]}
    st,h,raw=req(STREAM,body);requests+=1
    if st==204:
        term.append({"http_status":204,"reason":"NO_CONTENT_DOCUMENTED_STREAM_TERMINATION","from_slot":current});break
    if st!=200:raise RuntimeError(f"stream_http_{st}")
    lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
    if not lines:
        term.append({"http_status":200,"reason":"EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION","from_slot":current});break
    batch=[json.loads(x) for x in lines];last=None
    for b in batch:
        hdr=b.get("header") or {};slot=hdr.get("number");ts=norm_ts(hdr.get("timestamp"))
        if isinstance(slot,int):last=slot if last is None else max(last,slot)
        if ts is None:continue
        bt=int(iso_dt(ts).timestamp())
        if not (LO<=bt<HI):continue
        tx_by={}
        for pos,tx in enumerate(b.get("transactions") or []):
            tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM:continue
            try:dec=b58decode(ix.get("data",""))
            except Exception:dec=b""
            if not dec.startswith(bytes.fromhex(PREFIX)):continue
            ti=ix.get("transactionIndex");tx=tx_by.get(ti)
            if not isinstance(tx,dict):
                rows.append({"class":CLASS,"slot":slot,"timestamp":ts,"instructionAddress":ix.get("instructionAddress"),
                             "classification":"SOURCE_ANOMALY_FAIL_CLOSED","anomaly":"missing_parent_transaction"});continue
            sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            terr=tx.get("err");committed=ix.get("isCommitted");ierr=ix.get("error")
            if sig is None or not isinstance(ix.get("instructionAddress"),list):state="SOURCE_ANOMALY_FAIL_CLOSED"
            elif terr is None and committed is True and ierr is None:state="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
            elif terr is not None or committed is False or ierr is not None:
                consistent=not (terr is None and (committed is False or ierr is not None)) and not (terr is not None and committed is True)
                state="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED" if consistent else "SOURCE_ANOMALY_FAIL_CLOSED"
            else:state="SOURCE_ANOMALY_FAIL_CLOSED"
            rows.append({"class":CLASS,"signature":sig,"slot":slot,"timestamp":ts,"transactionIndex":ti,
                         "instructionAddress":ix.get("instructionAddress"),"transactionErr":terr,
                         "isCommitted":committed,"instructionError":ierr,"decoded_prefix_hex":dec[:8].hex(),
                         "classification":state})
    if last is None:raise RuntimeError("no_block_number")
    if last<current:raise RuntimeError("non_advancing_stream")
    current=last+1

ded={}
for r in rows:
    k=(r.get("signature"),json.dumps(r.get("instructionAddress"),separators=(",",":")))
    if k in ded and ded[k]!=r:raise RuntimeError("dedup_collision")
    ded[k]=r
rows=sorted(ded.values(),key=lambda r:(r.get("timestamp") or "",r.get("slot") or -1,r.get("signature") or ""))
succ=[r for r in rows if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
failed=[r for r in rows if r.get("classification")=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
anom=[r for r in rows if r.get("classification")=="SOURCE_ANOMALY_FAIL_CLOSED"]
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","class":CLASS,"prefix":PREFIX,
         "start":args.start,"end":args.end,"stream_complete":True,"request_count":requests,
         "termination_evidence":term,"successful_instruction_count":len(succ),"failed_attempt_count":len(failed),
         "anomaly_count":len(anom),"earliest_success_candidate":succ[0] if succ else None,
         "classification":"DRIFT_FOURTH_CLASS_LOCATOR_PARTITION_PASS" if not anom else "DRIFT_FOURTH_CLASS_LOCATOR_PARTITION_FAIL_CLOSED",
         "rows":rows,
         "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
                     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
                     "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["start","end","classification","successful_instruction_count","failed_attempt_count","anomaly_count","earliest_success_candidate"]},indent=2))
if receipt["classification"]!="DRIFT_FOURTH_CLASS_LOCATOR_PARTITION_PASS":raise SystemExit(2)
