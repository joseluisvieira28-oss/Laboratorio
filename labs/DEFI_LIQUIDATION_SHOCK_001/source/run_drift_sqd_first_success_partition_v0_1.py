#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
LOWER="2022-11-04T15:17:54Z"
UPPER="2025-01-01T00:00:00Z"
CLASSES={
 "liquidate_perp":"4b2377f7bf128b02",
 "liquidate_spot":"6b00802923e5fb12",
 "liquidate_borrow_for_perp_pnl":"a911205acf94d11b",
 "liquidate_perp_pnl_for_deposit":"ed4bc6ebe9ba4b23",
}
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

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
def sha_obj(o): return hashlib.sha256(json.dumps(o,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-drift-sqd/0.1"}
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

PREFIX_TO_CLASS={bytes.fromhex(v):k for k,v in CLASSES.items()}

def classify_prefix(dec):
    for pref,cls in PREFIX_TO_CLASS.items():
        if dec.startswith(pref): return cls,pref.hex()
    return None,None

def stream_slice(start_iso,end_iso):
    lo=iso_dt(start_iso); hi=iso_dt(end_iso)
    from_slot=ts_slot(start_iso); to_slot=ts_slot(end_iso)+16
    current=from_slot
    rows=[]; source_headers=[]; term=[]; request_count=0
    lo_ts=int(lo.timestamp()); hi_ts=int(hi.timestamp())
    while current<=to_slot:
        body={
          "type":"solana","fromBlock":current,"toBlock":to_slot,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True}
          },
          "instructions":[{"programId":[PROGRAM],"transaction":True}]
        }
        st,h,raw=req(STREAM,body); request_count+=1
        source_headers.append(h.get("x-sqd-data-source"))
        if st==204:
            term.append({"from_slot":current,"to_slot":to_slot,"http_status":204,
                         "reason":"NO_CONTENT_DOCUMENTED_STREAM_TERMINATION"}); break
        if st!=200: raise RuntimeError(f"stream_http_{st}:{raw[:500]!r}")
        lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not lines:
            term.append({"from_slot":current,"to_slot":to_slot,"http_status":200,
                         "reason":"EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION"}); break
        batch=[json.loads(x) for x in lines]
        last=None
        for b in batch:
            hdr=b.get("header") or {}; slot=hdr.get("number"); ts=norm_ts(hdr.get("timestamp"))
            if isinstance(slot,int): last=slot if last is None else max(last,slot)
            if ts is None: continue
            try: bt=int(iso_dt(ts).timestamp())
            except Exception: continue
            if not (lo_ts<=bt<hi_ts): continue
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                idx=tx.get("transactionIndex",tx.get("index",pos)); tx_by[idx]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=PROGRAM: continue
                try: dec=b58decode(ix.get("data",""))
                except Exception: dec=b""
                cls,phex=classify_prefix(dec)
                if cls is None: continue
                ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
                if not isinstance(tx,dict):
                    rows.append({"class":cls,"slot":slot,"timestamp":ts,"transactionIndex":ti,
                                 "instructionAddress":ix.get("instructionAddress"),
                                 "classification":"SOURCE_ANOMALY_FAIL_CLOSED","anomaly":"missing_parent_transaction"})
                    continue
                sigs=tx.get("signatures") or []
                sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                terr=tx.get("err"); committed=ix.get("isCommitted"); ierr=ix.get("error")
                if sig is None or not isinstance(ix.get("instructionAddress"),list):
                    state="SOURCE_ANOMALY_FAIL_CLOSED"
                elif terr is None and committed is True and ierr is None:
                    state="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
                elif terr is not None or committed is False or ierr is not None:
                    consistent=not (terr is None and (committed is False or ierr is not None)) and not (terr is not None and committed is True)
                    state="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED" if consistent else "SOURCE_ANOMALY_FAIL_CLOSED"
                else:
                    state="SOURCE_ANOMALY_FAIL_CLOSED"
                rows.append({
                  "protocol":"drift","class":cls,"signature":sig,"slot":slot,"timestamp":ts,
                  "transactionIndex":ti,"instructionAddress":ix.get("instructionAddress"),
                  "transactionErr":terr,"isCommitted":committed,"instructionError":ierr,
                  "decoded_prefix_hex":phex,"classification":state
                })
        if last is None: raise RuntimeError("no_block_number")
        if last<current: raise RuntimeError("non_advancing_stream")
        current=last+1

    ded={}
    for r in rows:
        key=(r.get("class"),r.get("signature"),json.dumps(r.get("instructionAddress"),separators=(",",":")))
        if key in ded and ded[key]!=r: raise RuntimeError("dedup_key_collision")
        ded[key]=r
    rows=sorted(ded.values(),key=lambda r:(r.get("timestamp") or "",r.get("slot") or -1,r.get("signature") or "",json.dumps(r.get("instructionAddress"))))
    succ=[r for r in rows if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
    failed=[r for r in rows if r.get("classification")=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
    anomalies=[r for r in rows if r.get("classification")=="SOURCE_ANOMALY_FAIL_CLOSED" or r.get("anomaly")]
    earliest={}
    for cls in CLASSES:
        xs=[r for r in succ if r.get("class")==cls]
        earliest[cls]=xs[0] if xs else None
    return {
      "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"drift",
      "slice_start":start_iso,"slice_end":end_iso,"from_slot":from_slot,"to_slot":to_slot,
      "stream_complete":True,"request_count":request_count,"source_headers":source_headers,
      "termination_evidence":term,"instruction_match_count":len(rows),
      "successful_instruction_count":len(succ),"failed_attempt_count":len(failed),
      "anomaly_count":len(anomalies),"earliest_success_by_class":earliest,
      "rows_sha256":sha_obj(rows),"rows":rows,
      "classification":"SOURCE_CHUNK_PASS" if not anomalies else "SOURCE_CHUNK_ANOMALY_FAIL_CLOSED"
    }

ap=argparse.ArgumentParser()
ap.add_argument("--start",required=True)
ap.add_argument("--end",required=True)
ap.add_argument("--out",required=True)
args=ap.parse_args()
start=max(iso_dt(args.start),iso_dt(LOWER)); end=min(iso_dt(args.end),iso_dt(UPPER))
if start>=end: raise SystemExit("empty_effective_range")
out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
manifest={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"drift",
          "requested_start":args.start,"requested_end":args.end,
          "effective_start":start.isoformat().replace("+00:00","Z"),
          "effective_end":end.isoformat().replace("+00:00","Z"),
          "chunks":[],"classification":"IN_PROGRESS",
          "frozen_classes":CLASSES,
          "firewall":{"prices":False,"balances":False,"token_amounts":False,"returns":False,"pnl":False,"direction":False,
                      "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
                      "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
                      "account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
cur=start
while cur<end:
    next_midnight=dt.datetime.combine(cur.date()+dt.timedelta(days=1),dt.time(0),tzinfo=dt.timezone.utc)
    nxt=min(next_midnight,end)
    s=cur.isoformat().replace("+00:00","Z"); e=nxt.isoformat().replace("+00:00","Z")
    print("CHUNK",s,e,flush=True)
    try:
        rec=stream_slice(s,e)
    except Exception as ex:
        rec={"schema_version":"0.1","protocol":"drift","slice_start":s,"slice_end":e,
             "stream_complete":False,"classification":"SOURCE_CHUNK_BLOCKED",
             "error":type(ex).__name__,"detail":str(ex)[:1000]}
    fname=cur.strftime("%Y-%m-%dT%H%M%SZ")+".json"
    p=out/fname; p.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    manifest["chunks"].append({"start":s,"end":e,"file":fname,"classification":rec["classification"],
                               "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                               "successful_instruction_count":rec.get("successful_instruction_count",0),
                               "failed_attempt_count":rec.get("failed_attempt_count",0),
                               "anomaly_count":rec.get("anomaly_count",0)})
    if rec["classification"]!="SOURCE_CHUNK_PASS":
        manifest["classification"]="PARTITION_BLOCKED_FAIL_CLOSED"; break
    cur=nxt
if manifest["classification"]=="IN_PROGRESS": manifest["classification"]="PARTITION_COMPLETE"
manifest["chunk_count"]=len(manifest["chunks"])
manifest["successful_instruction_count"]=sum(x["successful_instruction_count"] for x in manifest["chunks"])
manifest["failed_attempt_count"]=sum(x["failed_attempt_count"] for x in manifest["chunks"])
manifest["anomaly_count"]=sum(x["anomaly_count"] for x in manifest["chunks"])
(out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:manifest[k] for k in ["classification","chunk_count","successful_instruction_count","failed_attempt_count","anomaly_count"]},indent=2))
if manifest["classification"]!="PARTITION_COMPLETE": raise SystemExit(2)
