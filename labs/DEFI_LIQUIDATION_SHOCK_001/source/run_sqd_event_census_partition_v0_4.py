#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

CFG={
 "kamino":{
   "program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
   "prefix":"b1479abce2854a37",
   "authoritative_start":"2023-11-17T14:48:24Z",
   "start_slot":230572965,
   "first_sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
   "server_filter":True
 },
 "save11":{
   "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix":"11",
   "authoritative_start":"2024-07-19T19:30:52Z",
   "start_slot":278496102,
   "first_sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
   "server_filter":False
 }
}
END_GLOBAL="2025-01-01T00:00:00Z"

def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid_base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def req(url, body=None, retries=8):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-census/0.4"}
    if data is not None: headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(request,timeout=90) as resp:
                return int(resp.status),dict(resp.headers),resp.read()
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

def iso_to_dt(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def ts_to_slot(day_iso):
    unix=int(iso_to_dt(day_iso).timestamp())
    st,h,raw=req(f"{TSROOT}/{unix}/block")
    if st!=200: raise RuntimeError(f"timestamp_resolver_http_{st}:{raw[:300]!r}")
    obj=json.loads(raw)
    if isinstance(obj,int): return obj
    if isinstance(obj,dict):
        for k in ("block","number","slot"):
            if isinstance(obj.get(k),int): return obj[k]
    raise RuntimeError(f"timestamp_resolver_schema:{obj!r}")

def norm_time(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None

def sha_obj(o): return hashlib.sha256(json.dumps(o,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def stream_day(protocol, day_start, day_end, from_slot, to_slot):
    c=CFG[protocol]
    current=from_slot
    request_count=0
    rows=[]
    source_headers=[]
    while current<=to_slot:
        filt={"programId":[c["program"]],"transaction":True}
        if c["server_filter"]:
            filt["d8"]=["0x"+c["prefix"]]
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
        st,h,raw=req(STREAM,body)
        request_count+=1
        source_headers.append(h.get("x-sqd-data-source"))
        if st==204: break
        if st!=200: raise RuntimeError(f"stream_http_{st}:{raw[:500]!r}")
        txt=raw.decode("utf-8","replace")
        lines=[x for x in txt.splitlines() if x.strip()]
        if not lines: raise RuntimeError("empty_200_response")
        batch=[json.loads(x) for x in lines]
        last=None
        for b in batch:
            hdr=b.get("header") or {}
            slot=hdr.get("number")
            if isinstance(slot,int): last=slot if last is None else max(last,slot)
            ts=norm_time(hdr.get("timestamp"))
            tx_by={}
            for pos,tx in enumerate(b.get("transactions") or []):
                idx=tx.get("transactionIndex",tx.get("index",pos)); tx_by[idx]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=c["program"]: continue
                data=ix.get("data")
                try: dec=b58decode(data) if isinstance(data,str) else b""
                except Exception: dec=b""
                if not dec.startswith(bytes.fromhex(c["prefix"])): continue
                ti=ix.get("transactionIndex"); tx=tx_by.get(ti)
                if not isinstance(tx,dict):
                    rows.append({"anomaly":"missing_parent_transaction","slot":slot,"timestamp":ts,
                                 "transactionIndex":ti,"instructionAddress":ix.get("instructionAddress")})
                    continue
                sigs=tx.get("signatures") or []
                sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                committed=ix.get("isCommitted"); ierr=ix.get("error"); terr=tx.get("err")
                if sig is None or not isinstance(ix.get("instructionAddress"),list):
                    cls="SOURCE_ANOMALY_FAIL_CLOSED"
                elif terr is None and committed is True and ierr is None:
                    cls="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
                elif terr is not None or committed is False or ierr is not None:
                    consistent=not (terr is None and (committed is False or ierr is not None)) and not (terr is not None and committed is True)
                    cls="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED" if consistent else "SOURCE_ANOMALY_FAIL_CLOSED"
                else:
                    cls="SOURCE_ANOMALY_FAIL_CLOSED"
                rows.append({
                  "protocol":protocol,"signature":sig,"slot":slot,"timestamp":ts,
                  "transactionIndex":ti,"instructionAddress":ix.get("instructionAddress"),
                  "transactionErr":terr,"isCommitted":committed,"instructionError":ierr,
                  "decoded_prefix_hex":dec[:len(bytes.fromhex(c["prefix"]))].hex(),
                  "classification":cls
                })
        if last is None: raise RuntimeError("no_block_number")
        if last<current: raise RuntimeError("non_advancing_stream")
        current=last+1

    # deterministic instruction dedup
    ded={}
    for r in rows:
        key=(r.get("protocol"),r.get("signature"),json.dumps(r.get("instructionAddress"),separators=(",",":")))
        if key in ded and ded[key]!=r: raise RuntimeError("dedup_key_collision")
        ded[key]=r
    rows=sorted(ded.values(),key=lambda r:(r.get("slot") or -1,r.get("signature") or "",json.dumps(r.get("instructionAddress"))))
    success=[r for r in rows if r.get("classification")=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
    failed=[r for r in rows if r.get("classification")=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
    anomalies=[r for r in rows if r.get("classification")=="SOURCE_ANOMALY_FAIL_CLOSED" or r.get("anomaly")]
    return {
      "schema_version":"0.4","protocol":protocol,"day_start":day_start,"day_end":day_end,
      "from_slot":from_slot,"to_slot":to_slot,"stream_complete":True,
      "request_count":request_count,"source_headers":source_headers,
      "instruction_match_count":len(rows),"successful_instruction_count":len(success),
      "failed_attempt_count":len(failed),"anomaly_count":len(anomalies),
      "rows_sha256":sha_obj(rows),"rows":rows
    }

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=["kamino","save11"],required=True)
ap.add_argument("--start",required=True)
ap.add_argument("--end",required=True)
ap.add_argument("--out",required=True)
args=ap.parse_args()
c=CFG[args.protocol]
start=max(iso_to_dt(args.start+"T00:00:00Z"),iso_to_dt(c["authoritative_start"]))
end=min(iso_to_dt(args.end+"T00:00:00Z"),iso_to_dt(END_GLOBAL))
out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
manifest={"schema_version":"0.4","protocol":args.protocol,"requested_start":args.start,"requested_end":args.end,
          "effective_start":start.isoformat(),"effective_end":end.isoformat(),"chunks":[],"classification":"IN_PROGRESS",
          "firewall":{"prices":False,"balances":False,"amounts":False,"returns":False,"pnl":False,"direction":False,
                      "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
                      "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
                      "account_creation":False,"merge_main":False}}

cur=dt.datetime(start.year,start.month,start.day,tzinfo=dt.timezone.utc)
while cur<end:
    nxt=min(cur+dt.timedelta(days=1),end)
    day0=cur.isoformat().replace("+00:00","Z"); day1=nxt.isoformat().replace("+00:00","Z")
    if cur.date()==iso_to_dt(c["authoritative_start"]).date():
        from_slot=c["start_slot"]
    else:
        from_slot=ts_to_slot(day0)
    next_slot=ts_to_slot(day1)
    to_slot=next_slot-1
    print("CHUNK",args.protocol,day0,day1,from_slot,to_slot,flush=True)
    try:
        rec=stream_day(args.protocol,day0,day1,from_slot,to_slot)
        cls="SOURCE_CHUNK_PASS" if rec["anomaly_count"]==0 else "SOURCE_CHUNK_ANOMALY_FAIL_CLOSED"
        rec["classification"]=cls
    except Exception as e:
        rec={"schema_version":"0.4","protocol":args.protocol,"day_start":day0,"day_end":day1,
             "from_slot":from_slot,"to_slot":to_slot,"stream_complete":False,
             "classification":"SOURCE_CHUNK_BLOCKED","error":type(e).__name__,"detail":str(e)[:1000]}
    p=out/(cur.strftime("%Y-%m-%d")+".json")
    p.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    manifest["chunks"].append({"day":cur.strftime("%Y-%m-%d"),"file":p.name,"classification":rec["classification"],
                               "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                               "successful_instruction_count":rec.get("successful_instruction_count",0),
                               "failed_attempt_count":rec.get("failed_attempt_count",0),
                               "anomaly_count":rec.get("anomaly_count",0)})
    if rec["classification"]!="SOURCE_CHUNK_PASS":
        manifest["classification"]="PARTITION_BLOCKED_FAIL_CLOSED"
        break
    cur=nxt

if manifest["classification"]=="IN_PROGRESS":
    manifest["classification"]="PARTITION_COMPLETE"
manifest["chunk_count"]=len(manifest["chunks"])
manifest["successful_instruction_count"]=sum(x["successful_instruction_count"] for x in manifest["chunks"])
manifest["failed_attempt_count"]=sum(x["failed_attempt_count"] for x in manifest["chunks"])
manifest["anomaly_count"]=sum(x["anomaly_count"] for x in manifest["chunks"])
(out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:manifest[k] for k in ["protocol","classification","chunk_count","successful_instruction_count","failed_attempt_count","anomaly_count"]},indent=2))
if manifest["classification"]!="PARTITION_COMPLETE": raise SystemExit(2)
