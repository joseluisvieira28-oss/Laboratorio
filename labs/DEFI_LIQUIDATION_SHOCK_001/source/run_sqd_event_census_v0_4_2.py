#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TS_BASE="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
ROOT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/sqd_census_v0_4")
ROOT.mkdir(parents=True,exist_ok=True)
BOUNDARY_CACHE=ROOT/"BOUNDARY_CACHE.json"
SUMMARY=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_EVENT_CENSUS_RECEIPT_V0.4.2.json")
RAW_SAMPLE=ROOT/"RAW_SAMPLE_QUEUE_V0.4.2.json"

END_TS=1735689600
END_DATE=dt.date(2025,1,1)

PROTOCOLS={
 "kamino":{
   "program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
   "prefix_hex":"b1479abce2854a37","server_filter_key":"d8","server_filter_value":"0xb1479abce2854a37",
   "start_ts":1700232504,"start_slot":230572965,"start_date":dt.date(2023,11,17),
   "first_sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
 },
 "save11":{
   "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix_hex":"11","server_filter_key":None,"server_filter_value":None,
   "start_ts":1721417452,"start_slot":278496102,"start_date":dt.date(2024,7,19),
   "first_sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
 }
}

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for ch in s:
        if ch not in B58MAP:
            raise ValueError("invalid base58")
        n=n*58+B58MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha_file(path):
    return sha_bytes(Path(path).read_bytes())

def canon(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"))

def utc_midnight(d):
    return int(dt.datetime(d.year,d.month,d.day,tzinfo=dt.timezone.utc).timestamp())

def norm_ts(v):
    if isinstance(v,(int,float)):
        return int(v)
    if isinstance(v,str):
        try:
            return int(dt.datetime.fromisoformat(v.replace("Z","+00:00")).timestamp())
        except Exception:
            return None
    return None

def http_get(url,retries=9):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={
              "Accept":"application/json,text/plain,*/*",
              "User-Agent":"crypto-lab-dls-census/0.4.2"})
            with urllib.request.urlopen(req,timeout=45) as resp:
                return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            body=e.read().decode("utf-8","replace")
            last={"http":e.code,"body":body[:600]}
            if e.code in (429,529) or 500<=e.code<600:
                time.sleep(min(45,2**i)); continue
            return int(e.code),dict(e.headers),body
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:400]}
            time.sleep(min(45,2**i))
    raise RuntimeError(f"GET_EXHAUSTED:{last}")

def http_post(body,retries=9):
    raw=json.dumps(body,separators=(",",":")).encode()
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(STREAM,data=raw,method="POST",headers={
              "Content-Type":"application/json",
              "Accept":"application/x-ndjson,application/json",
              "User-Agent":"crypto-lab-dls-census/0.4.2"})
            with urllib.request.urlopen(req,timeout=90) as resp:
                return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            bodytxt=e.read().decode("utf-8","replace")
            last={"http":e.code,"body":bodytxt[:600]}
            if e.code in (429,529) or 500<=e.code<600:
                time.sleep(min(45,2**i)); continue
            return int(e.code),dict(e.headers),bodytxt
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:400]}
            time.sleep(min(45,2**i))
    raise RuntimeError(f"POST_EXHAUSTED:{last}")

def load_cache():
    if BOUNDARY_CACHE.exists():
        try:
            obj=json.loads(BOUNDARY_CACHE.read_text())
            if isinstance(obj,dict): return obj
        except Exception:
            pass
    return {}

CACHE=load_cache()

def persist_cache():
    BOUNDARY_CACHE.write_text(json.dumps(CACHE,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def resolve_boundary(target_ts):
    key=str(int(target_ts))
    cached=CACHE.get(key)
    if isinstance(cached,dict) and cached.get("ok") and isinstance(cached.get("selected_slot"),int):
        return cached

    status,h,txt=http_get(f"{TS_BASE}/{target_ts}/block")
    if status!=200:
        raise RuntimeError(f"TIMESTAMP_SEED_HTTP_{status}:{txt[:400]}")
    obj=json.loads(txt)
    seed=obj.get("block_number")
    if not isinstance(seed,int):
        raise RuntimeError(f"TIMESTAMP_SEED_SHAPE:{obj}")

    body={"type":"solana","fromBlock":seed,"toBlock":seed+64,
          "fields":{"block":{"number":True,"timestamp":True}}}
    st,hh,nd=http_post(body)
    if st!=200:
        raise RuntimeError(f"TIMESTAMP_STREAM_HTTP_{st}:{nd[:400]}")
    blocks=[]
    for line in nd.splitlines():
        if not line.strip(): continue
        b=json.loads(line)
        hdr=b.get("header") or {}
        n=hdr.get("number")
        t=norm_ts(hdr.get("timestamp"))
        if isinstance(n,int) and isinstance(t,int):
            blocks.append((n,t))
    blocks.sort()
    selected=next(((n,t) for n,t in blocks if t>=target_ts),None)
    if selected is None:
        raise RuntimeError(f"TIMESTAMP_NO_BLOCK_GE_TARGET seed={seed} target={target_ts} blocks={blocks[-5:]}")
    rec={"ok":True,"target_timestamp":int(target_ts),"seed_block":seed,
         "selected_slot":selected[0],"selected_timestamp":selected[1],
         "x_sqd_data_source":hh.get("x-sqd-data-source")}
    CACHE[key]=rec
    persist_cache()
    return rec

def expected_dates(proto):
    d=proto["start_date"]
    out=[]
    while d<END_DATE:
        out.append(d)
        d+=dt.timedelta(days=1)
    return out

def chunk_paths(name,d):
    base=ROOT/"chunks"/name
    base.mkdir(parents=True,exist_ok=True)
    ds=d.isoformat()
    return base/f"{ds}.receipt.json", base/f"{ds}.ledger.jsonl"

def load_complete_chunk(receipt_path,ledger_path):
    if not receipt_path.exists() or not ledger_path.exists():
        return None
    try:
        rec=json.loads(receipt_path.read_text())
    except Exception:
        return None
    if rec.get("classification")!="SOURCE_CHUNK_COMPLETE":
        return None
    if rec.get("ledger_sha256")!=sha_file(ledger_path):
        return None
    return rec

def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def row_key(row):
    return row["protocol"]+":"+row["signature"]+":"+canon(row["instructionAddress"])

def classify_exact(txerr,committed,ixerr):
    if txerr is None and committed is True and ixerr is None:
        return "SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
    if txerr is not None and committed is False:
        return "LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"
    return "SOURCE_ANOMALY_FAIL_CLOSED"

def stream_day(name,proto,d,start_slot,end_slot,day_start_ts,day_end_ts):
    current=start_slot
    rows=[]
    anomalies=[]
    statuses=[]
    source_headers=[]
    request_count=0
    block_rows=0
    stream_complete=False
    prefix=bytes.fromhex(proto["prefix_hex"])

    while current<=end_slot:
        filt={"programId":[proto["program"]],"transaction":True}
        if proto["server_filter_key"]:
            filt[proto["server_filter_key"]]=[proto["server_filter_value"]]
        body={
          "type":"solana","fromBlock":current,"toBlock":end_slot,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{"programId":True,"data":True,"transactionIndex":True,
                           "instructionAddress":True,"isCommitted":True,"error":True}
          },
          "instructions":[filt]
        }
        try:
            st,h,txt=http_post(body)
        except Exception as e:
            return {"blocked":True,"reason":type(e).__name__+":"+str(e)[:500],
                    "rows":rows,"anomalies":anomalies,"statuses":statuses,
                    "source_headers":source_headers,"request_count":request_count,
                    "block_rows":block_rows,"stream_complete":False}
        request_count+=1
        statuses.append(st)
        source_headers.append(h.get("x-sqd-data-source"))
        if st==204:
            stream_complete=True
            current=end_slot+1
            break
        if st!=200:
            return {"blocked":True,"reason":f"http_{st}:{txt[:500]}",
                    "rows":rows,"anomalies":anomalies,"statuses":statuses,
                    "source_headers":source_headers,"request_count":request_count,
                    "block_rows":block_rows,"stream_complete":False}
        lines=[x for x in txt.splitlines() if x.strip()]
        if not lines:
            return {"blocked":True,"reason":"empty_200_response",
                    "rows":rows,"anomalies":anomalies,"statuses":statuses,
                    "source_headers":source_headers,"request_count":request_count,
                    "block_rows":block_rows,"stream_complete":False}
        batch=[]
        try:
            batch=[json.loads(x) for x in lines]
        except Exception as e:
            return {"blocked":True,"reason":"ndjson_parse_error:"+str(e)[:300],
                    "rows":rows,"anomalies":anomalies,"statuses":statuses,
                    "source_headers":source_headers,"request_count":request_count,
                    "block_rows":block_rows,"stream_complete":False}

        last=None
        for b in batch:
            hdr=b.get("header") or {}
            slot=hdr.get("number")
            bts=norm_ts(hdr.get("timestamp"))
            if not isinstance(slot,int):
                anomalies.append({"type":"missing_block_number"})
                continue
            last=slot if last is None else max(last,slot)
            block_rows+=1
            if slot<start_slot or slot>end_slot:
                anomalies.append({"type":"slot_outside_chunk","slot":slot})
            if not isinstance(bts,int):
                anomalies.append({"type":"missing_block_timestamp","slot":slot})
                continue
            if bts<day_start_ts or bts>=day_end_ts:
                # First authoritative day may start intra-day; source rows before that slot are forbidden.
                anomalies.append({"type":"timestamp_outside_chunk","slot":slot,"timestamp":bts})

            txs=b.get("transactions") or []
            tx_by_idx={}
            for pos,tx in enumerate(txs):
                idx=tx.get("transactionIndex",tx.get("index",pos))
                tx_by_idx[idx]=tx

            for ix in b.get("instructions") or []:
                if ix.get("programId")!=proto["program"]:
                    continue
                data=ix.get("data")
                try:
                    dec=b58decode(data) if isinstance(data,str) else b""
                except Exception:
                    anomalies.append({"type":"base58_decode_error","slot":slot,"data":str(data)[:120]})
                    continue

                if name=="kamino":
                    if not dec.startswith(prefix):
                        anomalies.append({"type":"server_filter_prefix_mismatch","slot":slot,
                                          "decoded_prefix":dec[:len(prefix)].hex()})
                        continue
                else:
                    if not dec.startswith(prefix):
                        continue

                ti=ix.get("transactionIndex")
                tx=tx_by_idx.get(ti)
                if not isinstance(tx,dict):
                    anomalies.append({"type":"missing_parent_transaction","slot":slot,"transactionIndex":ti})
                    continue
                sigs=tx.get("signatures") or []
                address=ix.get("instructionAddress")
                if not isinstance(sigs,list) or not sigs or not isinstance(sigs[0],str):
                    anomalies.append({"type":"missing_signature","slot":slot,"transactionIndex":ti})
                    continue
                if not isinstance(address,list) or len(address)==0:
                    anomalies.append({"type":"missing_instruction_address","slot":slot,"signature":sigs[0]})
                    continue

                txerr=tx.get("err")
                committed=ix.get("isCommitted")
                ixerr=ix.get("error")
                cls=classify_exact(txerr,committed,ixerr)
                row={
                  "protocol":name,"date":d.isoformat(),"slot":slot,"timestamp":bts,
                  "signature":sigs[0],"instructionAddress":address,
                  "prefix_hex":proto["prefix_hex"],"transactionErr":txerr,
                  "isCommitted":committed,"instructionError":ixerr,
                  "classification":cls
                }
                if cls=="SOURCE_ANOMALY_FAIL_CLOSED":
                    anomalies.append({"type":"execution_state_inconsistency","row":row})
                rows.append(row)

        if last is None:
            return {"blocked":True,"reason":"no_advancing_block_number",
                    "rows":rows,"anomalies":anomalies,"statuses":statuses,
                    "source_headers":source_headers,"request_count":request_count,
                    "block_rows":block_rows,"stream_complete":False}
        if last<current:
            return {"blocked":True,"reason":"non_advancing_stream",
                    "rows":rows,"anomalies":anomalies,"statuses":statuses,
                    "source_headers":source_headers,"request_count":request_count,
                    "block_rows":block_rows,"stream_complete":False}
        current=last+1
        if last>=end_slot:
            stream_complete=True
            break

    return {"blocked":False,"rows":rows,"anomalies":anomalies,
            "statuses":statuses,"source_headers":source_headers,
            "request_count":request_count,"block_rows":block_rows,
            "stream_complete":stream_complete}

def execute_protocol(name,proto):
    dates=expected_dates(proto)
    protocol_meta={"protocol":name,"expected_days":len(dates),"processed":[],"blocked":None}
    previous_next=None

    for idx,d in enumerate(dates):
        rp,lp=chunk_paths(name,d)
        cached=load_complete_chunk(rp,lp)
        if cached:
            protocol_meta["processed"].append({"date":d.isoformat(),"reused":True,
                                                "classification":cached["classification"]})
            previous_next=cached.get("next_day_start_slot")
            print(f"REUSE {name} {d} success={cached.get('successful_count')} failed={cached.get('failed_count')}",flush=True)
            continue

        midnight=utc_midnight(d)
        nextd=d+dt.timedelta(days=1)
        next_midnight=utc_midnight(nextd)

        if d==proto["start_date"]:
            start_slot=proto["start_slot"]
            day_start_ts=proto["start_ts"]
        else:
            if isinstance(previous_next,int):
                start_slot=previous_next
            else:
                start_slot=resolve_boundary(midnight)["selected_slot"]
            day_start_ts=midnight

        next_info=resolve_boundary(next_midnight)
        next_slot=next_info["selected_slot"]
        end_slot=next_slot-1
        if end_slot<start_slot:
            rec={
              "schema_version":"0.4.2","lab_id":LAB,"protocol":name,"date":d.isoformat(),
              "classification":"SOURCE_ANOMALY_FAIL_CLOSED","reason":"end_slot_before_start_slot",
              "start_slot":start_slot,"end_slot":end_slot,"next_day_start_slot":next_slot
            }
            lp.write_bytes(b"")
            rec["ledger_sha256"]=sha_file(lp)
            write_json(rp,rec)
            protocol_meta["blocked"]=rec
            return protocol_meta

        print(f"CENSUS {name} {d} slots={start_slot}-{end_slot}",flush=True)
        result=stream_day(name,proto,d,start_slot,end_slot,day_start_ts,next_midnight)
        rows=result["rows"]

        # Deduplicate exact repeated source rows within the day, preserving conflicts fail-closed.
        bykey={}
        dup_identical=0
        local_anomalies=list(result["anomalies"])
        for row in rows:
            k=row_key(row)
            if k in bykey:
                if canon(bykey[k])==canon(row):
                    dup_identical+=1
                else:
                    local_anomalies.append({"type":"conflicting_duplicate_instruction_key","key":k})
            else:
                bykey[k]=row
        dedup_rows=sorted(bykey.values(),key=lambda x:(x["slot"],x["signature"],canon(x["instructionAddress"])))
        ledger_bytes=("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in dedup_rows)).encode()
        lp.write_bytes(ledger_bytes)

        successful=[x for x in dedup_rows if x["classification"]=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
        failed=[x for x in dedup_rows if x["classification"]=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]

        if result["blocked"]:
            cls="SOURCE_CHUNK_BLOCKED"
        elif local_anomalies:
            cls="SOURCE_ANOMALY_FAIL_CLOSED"
        elif result["stream_complete"]:
            cls="SOURCE_CHUNK_COMPLETE"
        else:
            cls="SOURCE_CHUNK_BLOCKED"

        rec={
          "schema_version":"0.4.2","lab_id":LAB,"protocol":name,"date":d.isoformat(),
          "classification":cls,"start_slot":start_slot,"end_slot":end_slot,
          "day_start_timestamp":day_start_ts,"day_end_timestamp_exclusive":next_midnight,
          "next_day_start_slot":next_slot,
          "request_count":result["request_count"],"http_statuses":result["statuses"],
          "source_headers":result["source_headers"],"source_block_rows":result["block_rows"],
          "stream_complete":result["stream_complete"],"exact_instruction_count":len(dedup_rows),
          "successful_count":len(successful),"failed_count":len(failed),
          "anomaly_count":len(local_anomalies),"identical_duplicate_rows":dup_identical,
          "ledger_path":str(lp),"ledger_sha256":sha_file(lp),
          "blocker_reason":result.get("reason"),
          "anomalies":local_anomalies[:100],
          "firewall":{"prices":False,"balances":False,"token_balances":False,"amounts":False,
                      "fees":False,"returns":False,"pnl":False,"direction":False,
                      "economic_outcomes":False,"live_trading":False,"orders":False,
                      "wallets":False,"exchange_mutation":False,"paid_source":False,
                      "account_creation":False,"merge_main":False}
        }
        write_json(rp,rec)
        protocol_meta["processed"].append({"date":d.isoformat(),"reused":False,
                                            "classification":cls,"successful":len(successful),
                                            "failed":len(failed)})
        previous_next=next_slot
        print(f"RESULT {name} {d} {cls} exact={len(dedup_rows)} success={len(successful)} failed={len(failed)} anomalies={len(local_anomalies)}",flush=True)
        if cls!="SOURCE_CHUNK_COMPLETE":
            protocol_meta["blocked"]=rec
            return protocol_meta
        time.sleep(0.03)

    return protocol_meta

def aggregate(protocol_meta):
    manifest=[]
    all_rows={name:[] for name in PROTOCOLS}
    all_complete=True

    for name,proto in PROTOCOLS.items():
        for d in expected_dates(proto):
            rp,lp=chunk_paths(name,d)
            if not rp.exists() or not lp.exists():
                all_complete=False
                manifest.append({"protocol":name,"date":d.isoformat(),"classification":"MISSING"})
                continue
            try: rec=json.loads(rp.read_text())
            except Exception:
                all_complete=False
                manifest.append({"protocol":name,"date":d.isoformat(),"classification":"RECEIPT_PARSE_ERROR"})
                continue
            entry={"protocol":name,"date":d.isoformat(),"classification":rec.get("classification"),
                   "receipt_sha256":sha_file(rp),"ledger_sha256":sha_file(lp),
                   "successful_count":rec.get("successful_count"),"failed_count":rec.get("failed_count")}
            manifest.append(entry)
            if rec.get("classification")!="SOURCE_CHUNK_COMPLETE" or rec.get("ledger_sha256")!=entry["ledger_sha256"]:
                all_complete=False
                continue
            for line in lp.read_text().splitlines():
                if line.strip():
                    all_rows[name].append(json.loads(line))

    protocol_summaries={}
    sample_obj={"schema_version":"0.4.2","lab_id":LAB,"protocols":{}}
    global_anomalies=[]

    for name,proto in PROTOCOLS.items():
        rows=all_rows[name]
        unique={}
        for r in rows:
            k=row_key(r)
            if k in unique and canon(unique[k])!=canon(r):
                global_anomalies.append({"type":"cross_chunk_conflicting_instruction_key","protocol":name,"key":k})
            else:
                unique[k]=r
        rows=sorted(unique.values(),key=lambda x:(x["slot"],x["signature"],canon(x["instructionAddress"])))
        successes=[r for r in rows if r["classification"]=="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"]
        failed=[r for r in rows if r["classification"]=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"]
        bad=[r for r in rows if r["classification"]=="SOURCE_ANOMALY_FAIL_CLOSED"]
        if bad:
            global_anomalies.append({"type":"anomaly_rows_present","protocol":name,"count":len(bad)})

        first_found=any(r["signature"]==proto["first_sig"] for r in successes)
        if all_complete and not first_found:
            global_anomalies.append({"type":"known_first_success_missing","protocol":name})

        sig_to_last={}
        for r in successes:
            sig=r["signature"]
            prev=sig_to_last.get(sig)
            if prev is None or (r["slot"],canon(r["instructionAddress"]))>(prev["slot"],canon(prev["instructionAddress"])):
                sig_to_last[sig]=r
        sigs=sorted(sig_to_last)
        last_sig=None
        if sig_to_last:
            last_sig=max(sig_to_last.values(),key=lambda r:(r["slot"],canon(r["instructionAddress"])))["signature"]

        mandatory=[]
        if proto["first_sig"] in sig_to_last: mandatory.append(proto["first_sig"])
        if last_sig and last_sig not in mandatory: mandatory.append(last_sig)
        ranked=sorted(
          [(hashlib.sha256(f"{name}:{s}".encode()).hexdigest(),s) for s in sigs if s not in mandatory],
          key=lambda x:x[0]
        )
        if len(sigs)<=32:
            sample=sigs
        else:
            sample=mandatory+[s for _,s in ranked[:max(0,32-len(mandatory))]]

        sample_obj["protocols"][name]={
          "distinct_successful_signatures":len(sigs),
          "mandatory_first_signature":proto["first_sig"],
          "chronologically_last_successful_signature":last_sig,
          "sample_signatures":sample,
          "sample_count":len(sample),
          "selection_rule":"mandatory first + chronological last + ascending sha256(protocol:signature); verify all if <=32"
        }
        protocol_summaries[name]={
          "instruction_rows":len(rows),"successful_instruction_rows":len(successes),
          "failed_instruction_rows":len(failed),"distinct_successful_signatures":len(sigs),
          "known_first_success_recovered":first_found,
          "chronologically_last_successful_signature":last_sig
        }

    write_json(RAW_SAMPLE,sample_obj)
    manifest_sorted=sorted(manifest,key=lambda x:(x["protocol"],x["date"]))
    manifest_sha=sha_bytes(canon(manifest_sorted).encode())

    classification=(
      "SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE"
      if all_complete and not global_anomalies
      else "SQD_EVENT_CENSUS_BLOCKED"
    )
    receipt={
      "schema_version":"0.4.2","lab_id":LAB,"classification":classification,
      "source":STREAM,"window_end_exclusive":"2025-01-01T00:00:00Z",
      "protocol_summaries":protocol_summaries,
      "expected_chunk_counts":{n:len(expected_dates(p)) for n,p in PROTOCOLS.items()},
      "manifest_entry_count":len(manifest_sorted),"manifest_sha256":manifest_sha,
      "manifest":manifest_sorted,"global_anomalies":global_anomalies,
      "raw_sample_queue_path":str(RAW_SAMPLE),"raw_sample_queue_sha256":sha_file(RAW_SAMPLE),
      "firewall":{"prices":False,"balances":False,"token_balances":False,"amounts":False,
                  "fees":False,"returns":False,"pnl":False,"direction":False,
                  "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
                  "live_trading":False,"orders":False,"wallets":False,
                  "exchange_mutation":False,"paid_source":False,
                  "account_creation":False,"merge_main":False}
    }
    write_json(SUMMARY,receipt)
    return receipt

metas={}
exit_code=0
for name,proto in PROTOCOLS.items():
    try:
        metas[name]=execute_protocol(name,proto)
        if metas[name].get("blocked") is not None:
            exit_code=2
    except Exception as e:
        metas[name]={"protocol":name,"fatal_error":type(e).__name__,"detail":str(e)[:1000]}
        exit_code=2
        print("FATAL",name,type(e).__name__,str(e)[:1000],flush=True)

receipt=aggregate(metas)
print(json.dumps({
 "classification":receipt["classification"],
 "protocol_summaries":receipt["protocol_summaries"],
 "expected_chunk_counts":receipt["expected_chunk_counts"],
 "manifest_entry_count":receipt["manifest_entry_count"],
 "global_anomalies":receipt["global_anomalies"]
},indent=2,sort_keys=True))
if receipt["classification"]!="SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":
    exit_code=2
raise SystemExit(exit_code)
