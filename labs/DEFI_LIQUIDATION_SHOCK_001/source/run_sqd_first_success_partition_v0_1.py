#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

CFG={
 "marginfi":{
   "program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
   "prefix":"d6a997d5fba756db",
   "lower":"2023-02-07T15:47:04Z",
   "upper":"2025-01-01T00:00:00Z",
   "server_filter":True
 },
 "save0c":{
   "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix":"0c",
   "lower":"2021-12-08T00:00:00Z",
   "upper":"2025-01-01T00:00:00Z",
   "server_filter":False
 }
}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def iso_dt(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-first-success-sqd/0.1"}
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
                last={"http":e.code,"body":raw[:500].decode("utf-8","replace")}
                time.sleep(min(60,2**i)); continue
            return int(e.code),dict(e.headers),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:500]}
            time.sleep(min(60,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def ts_slot(s):
    unix=int(iso_dt(s).timestamp())
    st,h,raw=req(f"{TSROOT}/{unix}/block")
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}:{raw[:300]!r}")
    obj=json.loads(raw)
    if isinstance(obj,int): return obj
    if isinstance(obj,dict):
        for k in ("block","block_number","number","slot"):
            if isinstance(obj.get(k),int): return obj[k]
    raise RuntimeError(f"timestamp_resolver_schema:{obj!r}")

def norm_ts(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None

def sha(o): return hashlib.sha256(json.dumps(o,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def run(protocol,start_iso,end_iso):
    c=CFG[protocol]
    lower=max(iso_dt(start_iso),iso_dt(c["lower"]))
    upper=min(iso_dt(end_iso),iso_dt(c["upper"]))
    if lower>=upper: raise ValueError("empty_effective_range")
    lower_s=lower.isoformat().replace("+00:00","Z")
    upper_s=upper.isoformat().replace("+00:00","Z")
    from_slot=ts_slot(lower_s)
    to_slot=ts_slot(upper_s)+16
    current=from_slot
    rows=[]; headers=[]; termination=[]; requests=0
    lower_ts=int(lower.timestamp()); upper_ts=int(upper.timestamp())
    while current<=to_slot:
        filt={"programId":[c["program"]],"transaction":True}
        if c["server_filter"]: filt["d8"]=["0x"+c["prefix"]]
        body={
          "type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True}
          },
          "instructions":[filt]
        }
        st,h,raw=req(STREAM,body); requests+=1; headers.append(h.get("x-sqd-data-source"))
        if st==204:
            termination.append({"http_status":204,"from_slot":current,"to_slot":to_slot,"reason":"NO_CONTENT_DOCUMENTED_STREAM_TERMINATION"}); break
        if st!=200: raise RuntimeError(f"stream_http_{st}:{raw[:500]!r}")
        lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not lines:
            termination.append({"http_status":200,"from_slot":current,"to_slot":to_slot,"reason":"EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION"}); break
        batch=[json.loads(x) for x in lines]
        last=None
        for b in batch:
            hdr=b.get("header") or {}; slot=hdr.get("number"); ts=norm_ts(hdr.get("timestamp"))
            if isinstance(slot,int): last=slot if last is None else max(last,slot)
            if ts is None: continue
            try: bt=int(iso_dt(ts).timestamp())
            except Exception: continue
            if not (lower_ts<=bt<upper_ts): continue
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                tx_by[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=c["program"]: continue
                try: dec=b58decode(ix.get("data",""))
                except Exception: dec=b""
                pref=bytes.fromhex(c["prefix"])
                if not dec.startswith(pref): continue
                ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
                if not isinstance(tx,dict):
                    rows.append({"protocol":protocol,"slot":slot,"timestamp":ts,"transactionIndex":ti,
                                 "instructionAddress":ix.get("instructionAddress"),
                                 "classification":"SOURCE_ANOMALY_FAIL_CLOSED","anomaly":"missing_parent_transaction"})
                    continue
                sigs=tx.get("signatures") or []; sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                terr=tx.get("err"); committed=ix.get("isCommitted"); ierr=ix.get("error")
                if sig is None or not isinstance(ix.get("instructionAddress"),list):
                    cls="SOURCE_ANOMALY_FAIL_CLOSED"
                elif terr is None and committed is True and ierr is None:
                    cls="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
                elif terr is not None or committed is False or ierr is not None:
                    consistent=not (terr is None and (committed is False or ierr is not None)) and not (terr is not None and committed is True)
                    cls="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED" if consistent else "SOURCE_ANOMALY_FAIL_CLOSED"
                else:
                    cls="SOURCE_ANOMALY_FAIL_CLOSED"
                rows.append({"protocol":protocol,"signature":sig,"slot":slot,"timestamp":ts,
                             "transactionIndex":ti,"instructionAddress":ix.get("instructionAddress"),
                             "transactionErr":terr,"isCommitted":committed,"instructionError":ierr,
                             "decoded_prefix_hex":dec[:len(pref)].hex(),"classification":cls})
        if last is None: raise RuntimeError("no_block_number")
        if last<current: raise RuntimeError("non_advancing_stream")
        current=last+1
    ded={}
    for r in rows:
        k=(protocol,r.get("signature"),json.dumps(r.get("instructionAddress"),separators=(",",":")))
        if k in ded and ded[k]!=r: raise RuntimeError("dedup_key_collision")
        ded[k]=r
    rows=sorted(ded.values(),key=lambda r:(r.get("timestamp") or "",r.get("slot") or -1,r.get("signature") or "",json.dumps(r.get("instructionAddress"))))
    success=[r for r in rows if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
    failed=[r for r in rows if r.get("classification")=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
    anomalies=[r for r in rows if r.get("classification")=="SOURCE_ANOMALY_FAIL_CLOSED" or r.get("anomaly")]
    return {
      "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":protocol,
      "effective_start":lower_s,"effective_end":upper_s,"from_slot":from_slot,"to_slot":to_slot,
      "stream_complete":True,"request_count":requests,"source_headers":headers,"termination_evidence":termination,
      "instruction_match_count":len(rows),"successful_instruction_count":len(success),
      "failed_attempt_count":len(failed),"anomaly_count":len(anomalies),
      "earliest_success_candidate":success[0] if success else None,
      "rows_sha256":sha(rows),"rows":rows,
      "classification":"SOURCE_PARTITION_PASS" if not anomalies else "SOURCE_PARTITION_ANOMALY_FAIL_CLOSED",
      "firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
                  "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
                  "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
                  "account_creation":False,"post_outcome_tuning":False,"merge_main":False}
    }

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=["marginfi","save0c"],required=True)
ap.add_argument("--start",required=True)
ap.add_argument("--end",required=True)
ap.add_argument("--out",required=True)
args=ap.parse_args()
out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
try:
    rec=run(args.protocol,args.start,args.end)
except Exception as e:
    rec={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":args.protocol,
         "effective_start":args.start,"effective_end":args.end,"stream_complete":False,
         "classification":"SOURCE_PARTITION_BLOCKED","error":type(e).__name__,"detail":str(e)[:1000]}
out.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:rec.get(k) for k in ["protocol","classification","effective_start","effective_end","successful_instruction_count","failed_attempt_count","anomaly_count","earliest_success_candidate"]},indent=2))
if rec.get("classification")!="SOURCE_PARTITION_PASS": raise SystemExit(2)
