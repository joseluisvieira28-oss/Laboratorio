#!/usr/bin/env python3
import datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
START="2022-11-07T00:00:00Z"; END="2022-11-08T00:00:00Z"
CLASSES={
 "liquidate_perp":"4b2377f7bf128b02",
 "liquidate_spot":"6b00802923e5fb12",
 "liquidate_perp_pnl_for_deposit":"ed4bc6ebe9ba4b23",
}
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_SQD_SINGLE_D8_CALIBRATION_RECEIPT_V0.1.json")
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
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-d8-cal/0.1"}
    if data is not None: headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=120) as r:
                return int(r.status),dict(r.headers),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code}; time.sleep(min(60,2**i)); continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}; time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")
def ts_slot(s):
    unix=int(iso_dt(s).timestamp()); st,h,raw=req(f"{TSROOT}/{unix}/block")
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}")
    obj=json.loads(raw)
    if isinstance(obj,int): return obj
    if isinstance(obj,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(obj.get(k),int): return obj[k]
    raise RuntimeError("timestamp_resolver_schema")

FROM=ts_slot(START); TO=ts_slot(END)+16
LO=int(iso_dt(START).timestamp()); HI=int(iso_dt(END).timestamp())

def classify_row(ix,tx,slot,ts,prefix,cls):
    try: dec=b58decode(ix.get("data",""))
    except Exception: return None
    if not dec.startswith(bytes.fromhex(prefix)): return None
    sigs=tx.get("signatures") or []; sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
    addr=ix.get("instructionAddress")
    terr=tx.get("err"); committed=ix.get("isCommitted"); ierr=ix.get("error")
    if sig is None or not isinstance(addr,list): state="SOURCE_ANOMALY_FAIL_CLOSED"
    elif terr is None and committed is True and ierr is None: state="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
    elif terr is not None or committed is False or ierr is not None:
        consistent=not (terr is None and (committed is False or ierr is not None)) and not (terr is not None and committed is True)
        state="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED" if consistent else "SOURCE_ANOMALY_FAIL_CLOSED"
    else: state="SOURCE_ANOMALY_FAIL_CLOSED"
    return {"class":cls,"signature":sig,"instructionAddress":addr,"slot":slot,"timestamp":ts,"classification":state}

def collect(d8=None):
    current=FROM; rows=[]; terms=[]; requests=0
    while current<=TO:
        filt={"programId":[PROGRAM],"transaction":True}
        if d8 is not None: filt["d8"]=["0x"+d8]
        body={"type":"solana","fromBlock":current,"toBlock":TO,
              "fields":{"block":{"number":True,"timestamp":True},
                        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                        "instruction":{"programId":True,"data":True,"transactionIndex":True,
                                       "instructionAddress":True,"isCommitted":True,"error":True}},
              "instructions":[filt]}
        st,h,raw=req(STREAM,body); requests+=1
        if st==204:
            terms.append({"http_status":204,"reason":"NO_CONTENT_DOCUMENTED_STREAM_TERMINATION"}); break
        if st!=200: raise RuntimeError(f"stream_http_{st}")
        lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not lines:
            terms.append({"http_status":200,"reason":"EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION"}); break
        batch=[json.loads(x) for x in lines]; last=None
        for b in batch:
            hdr=b.get("header") or {}; slot=hdr.get("number"); ts=norm_ts(hdr.get("timestamp"))
            if isinstance(slot,int): last=slot if last is None else max(last,slot)
            if ts is None: continue
            bt=int(iso_dt(ts).timestamp())
            if not (LO<=bt<HI): continue
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=PROGRAM: continue
                ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
                if not isinstance(tx,dict): continue
                if d8 is None:
                    for cls,prefix in CLASSES.items():
                        r=classify_row(ix,tx,slot,ts,prefix,cls)
                        if r: rows.append(r); break
                else:
                    cls=next(k for k,v in CLASSES.items() if v==d8)
                    r=classify_row(ix,tx,slot,ts,d8,cls)
                    if r: rows.append(r)
        if last is None: raise RuntimeError("no_block_number")
        if last<current: raise RuntimeError("non_advancing_stream")
        current=last+1
    ded={}
    for r in rows:
        key=(r["class"],r["signature"],json.dumps(r["instructionAddress"],separators=(",",":")),r["slot"],r["timestamp"])
        if key in ded and ded[key]!=r: raise RuntimeError("dedup_collision")
        ded[key]=r
    return ded,requests,terms

base,base_req,base_term=collect(None)
report={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","slice_start":START,"slice_end":END,
        "classification":"DRIFT_SQD_SINGLE_D8_EXACT_EQUIVALENCE_PASS","classes":{},
        "base_program_only_count":len(base),"base_request_count":base_req,"base_termination":base_term,
        "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
                    "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
                    "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
for cls,prefix in CLASSES.items():
    sub={k:v for k,v in base.items() if v["class"]==cls}
    d8rows,reqs,terms=collect(prefix)
    missing=sorted(set(sub)-set(d8rows)); extras=sorted(set(d8rows)-set(sub))
    conflicts=[k for k in set(sub)&set(d8rows) if sub[k]["classification"]!=d8rows[k]["classification"]]
    ok=not missing and not extras and not conflicts and len(sub)>0
    report["classes"][cls]={"prefix":prefix,"program_only_count":len(sub),"d8_count":len(d8rows),
                            "missing_count":len(missing),"extra_count":len(extras),"classification_conflict_count":len(conflicts),
                            "request_count":reqs,"termination":terms,"pass":ok}
    if not ok: report["classification"]="DRIFT_SQD_SINGLE_D8_CALIBRATION_FAIL_CLOSED"
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,indent=2,sort_keys=True))
if report["classification"]!="DRIFT_SQD_SINGLE_D8_EXACT_EQUIVALENCE_PASS": raise SystemExit(2)
