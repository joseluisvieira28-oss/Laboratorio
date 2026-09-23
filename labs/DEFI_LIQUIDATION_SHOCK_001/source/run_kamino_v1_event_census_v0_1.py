#!/usr/bin/env python3
import argparse, hashlib, json, os, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

LAB_ID="DEFI-LIQUIDATION-SHOCK-001"
CLASS_ID="KAMINO_V1"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
PREFIX_HEX="b1479abce2854a37"
PREFIX=bytes.fromhex(PREFIX_HEX)
START_ISO="2023-11-17T14:48:24Z"
END_ISO="2023-11-18T00:00:00Z"
START_TS=int(datetime.fromisoformat(START_ISO.replace("Z","+00:00")).timestamp())
END_TS=int(datetime.fromisoformat(END_ISO.replace("Z","+00:00")).timestamp())
FIRST_SIG="2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv"
FIRST_SLOT=230572965
PARENT_RUN=35704794316
PARENT_ARTIFACT=10686881756
PARENT_ARTIFACT_SHA="15097adc6e833edfc99ab11f24c6c4057752b2df7c5de831567bdc6cc01ecf14"
RPC="https://api.mainnet-beta.solana.com"
TRANCHE_SIZE=250
MAX_RETRIES=12
REPO_DIR=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
QUEUE_PATH=REPO_DIR/"KAMINO_V1_EVENT_CENSUS_QUEUE_V0.1.json"
QUEUE_RECEIPT=REPO_DIR/"KAMINO_V1_EVENT_CENSUS_QUEUE_RECEIPT_V0.1.json"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58={c:i for i,c in enumerate(ALPH)}

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o,separators=(",",":"),sort_keys=True).encode()

def b58decode(s):
    n=0
    for c in s:
        if c not in B58: raise ValueError("non-base58")
        n=n*58+B58[c]
    body=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+body

def write_json(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def cmd_queue(parent):
    parent=Path(parent)
    pages=sorted(parent.rglob("signatures_page_*.json"))
    if not pages: raise RuntimeError("NO_SIGNATURE_PAGES_IN_PARENT_ARTIFACT")
    selected=[]; seen=set(); page_count=0; null_bt=0
    for p in pages:
        obj=json.loads(p.read_text(encoding="utf-8"))
        rows=obj.get("result")
        if not isinstance(rows,list): raise RuntimeError(f"INVALID_PAGE_RESULT {p}")
        page_count+=1
        for r in rows:
            if not isinstance(r,dict) or not isinstance(r.get("signature"),str) or r.get("slot") is None:
                raise RuntimeError(f"INVALID_SIGNATURE_ROW {p}")
            bt=r.get("blockTime")
            if bt is None:
                null_bt+=1
                continue
            bt=int(bt)
            if START_TS <= bt < END_TS:
                sig=r["signature"]
                if sig in seen: raise RuntimeError(f"DUPLICATE_SELECTED_SIGNATURE {sig}")
                seen.add(sig)
                selected.append({"signature":sig,"slot":int(r["slot"]),"blockTime":bt,"err":r.get("err")})
    if null_bt:
        raise RuntimeError(f"NULL_BLOCKTIME_ROWS_PRESENT {null_bt}")
    selected.sort(key=lambda r:(r["blockTime"],r["slot"],r["signature"]))
    if not selected: raise RuntimeError("EMPTY_FROZEN_CHUNK_QUEUE")
    if FIRST_SIG not in {r["signature"] for r in selected}: raise RuntimeError("KNOWN_FIRST_SUCCESS_MISSING_FROM_QUEUE")
    qhash=sha(canon(selected))
    queue={
      "schema_version":"0.1","lab_id":LAB_ID,"class_id":CLASS_ID,
      "program_id":PROGRAM,"discriminator":PREFIX_HEX,
      "window":{"start":START_ISO,"end":END_ISO,"semantics":"half_open"},
      "parent":{"run_id":PARENT_RUN,"artifact_id":PARENT_ARTIFACT,"artifact_sha256":PARENT_ARTIFACT_SHA},
      "source_page_files_seen":page_count,"queue_rows":len(selected),"queue_sha256":qhash,
      "known_first_success":{"signature":FIRST_SIG,"slot":FIRST_SLOT,"blockTime":START_TS},
      "rows":selected,
      "firewalls":{"prices":False,"returns":False,"pnl":False,"direction":False,"market_outcomes":False,
                   "event_size_threshold_tuning":False,"live_trading":False,"orders":False,"wallets":False,
                   "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}
    }
    write_json(QUEUE_PATH,queue)
    receipt={k:v for k,v in queue.items() if k!="rows"}
    receipt["classification"]="KAMINO_V1_EVENT_CENSUS_QUEUE_FROZEN"
    write_json(QUEUE_RECEIPT,receipt)
    print(json.dumps({"queue_rows":len(selected),"queue_sha256":qhash},sort_keys=True))

def rpc_transaction(sig):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}]},separators=(",",":")).encode()
    last=None
    for attempt in range(MAX_RETRIES):
        req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-census/0.1"})
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                raw=resp.read()
            obj=json.loads(raw)
            if obj.get("error"):
                last={"rpc_error":obj["error"]}
                time.sleep(min(45,2*(attempt+1))); continue
            if obj.get("result") is None:
                last={"null_result":True}
                time.sleep(min(20,2*(attempt+1))); continue
            return obj,raw
        except urllib.error.HTTPError as e:
            body=e.read() if hasattr(e,"read") else b""
            last={"http":e.code,"body":body[:300].decode("utf-8","replace")}
            if e.code in (429,500,502,503,504):
                time.sleep(min(45,2*(attempt+1))); continue
            break
        except Exception as e:
            last={"transport":repr(e)}
            time.sleep(min(45,2*(attempt+1)))
    raise RuntimeError(f"GET_TRANSACTION_EXHAUSTED {sig} {last}")

def iter_instructions(res):
    msg=((res.get("transaction") or {}).get("message") or {})
    for i,ins in enumerate(msg.get("instructions") or []):
        yield "outer",str(i),ins
    meta=res.get("meta") or {}
    for g in meta.get("innerInstructions") or []:
        parent=g.get("index")
        for j,ins in enumerate(g.get("instructions") or []):
            yield "inner",f"{parent}:{j}",ins

def exact_matches(res):
    out=[]
    for loc,idx,ins in iter_instructions(res):
        if ins.get("programId")!=PROGRAM: continue
        data=ins.get("data")
        if not isinstance(data,str): continue
        try: raw=b58decode(data)
        except Exception: continue
        if raw.startswith(PREFIX):
            out.append({"location":loc,"instruction_index":idx,"data_prefix_hex":raw[:len(PREFIX)].hex()})
    return out

def cmd_scan(queue_path,index,start,end,outdir):
    queue=json.loads(Path(queue_path).read_text(encoding="utf-8"))
    rows=queue["rows"]
    if queue["queue_sha256"]!=sha(canon(rows)): raise RuntimeError("QUEUE_HASH_MISMATCH")
    index=int(index); start=int(start); end=min(int(end),len(rows))
    out=Path(outdir); rawdir=out/"raw"; rawdir.mkdir(parents=True,exist_ok=True)
    adjud=[]; events=[]; attempts=[]; anomalies=[]
    for qi in range(start,end):
        row=rows[qi]; sig=row["signature"]
        try:
            obj,raw=rpc_transaction(sig)
        except Exception as e:
            anomalies.append({"queue_index":qi,"signature":sig,"reason":"rpc_exhausted","detail":str(e)[:500]})
            break
        (rawdir/f"{qi:07d}_{sig}.json").write_bytes(raw)
        res=obj.get("result")
        meta=res.get("meta") if isinstance(res,dict) else None
        reason=None
        if not isinstance(res,dict): reason="missing_result"
        elif int(res.get("slot",-1))!=int(row["slot"]): reason="slot_mismatch"
        elif not isinstance(meta,dict): reason="missing_meta"
        elif (row.get("err") is None)!=(meta.get("err") is None): reason="signature_raw_status_mismatch"
        elif res.get("blockTime") is not None and int(res["blockTime"])!=int(row["blockTime"]): reason="blocktime_mismatch"
        if reason:
            anomalies.append({"queue_index":qi,"signature":sig,"reason":reason})
            break
        matches=exact_matches(res)
        if len(matches)>1:
            anomalies.append({"queue_index":qi,"signature":sig,"reason":"multiple_exact_matches","match_count":len(matches)})
            break
        klass="NON_CANDIDATE_PROGRAM_TRANSACTION"
        if len(matches)==1:
            klass="AUTHORITATIVE_REALIZED_LIQUIDATION" if meta.get("err") is None else "LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"
        rec={
          "queue_index":qi,"signature":sig,"slot":int(row["slot"]),"blockTime":int(row["blockTime"]),
          "blockTimeIso":datetime.fromtimestamp(int(row["blockTime"]),timezone.utc).isoformat().replace("+00:00","Z"),
          "signature_err":row.get("err"),"raw_meta_err":meta.get("err"),"classification":klass,
          "match_count":len(matches),"match":matches[0] if matches else None,
          "raw_response_sha256":sha(raw),"raw_file":f"raw/{qi:07d}_{sig}.json"
        }
        adjud.append(rec)
        if klass=="AUTHORITATIVE_REALIZED_LIQUIDATION": events.append(rec)
        elif klass=="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED": attempts.append(rec)
        if (qi-start+1)%25==0: print(f"tranche={index} processed={qi-start+1}/{end-start}",flush=True)
        time.sleep(0.12)
    out.mkdir(parents=True,exist_ok=True)
    for name,data in [("adjudications.jsonl",adjud),("events.jsonl",events),("attempts.jsonl",attempts),("anomalies.jsonl",anomalies)]:
        (out/name).write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in data),encoding="utf-8")
    receipt={
      "schema_version":"0.1","lab_id":LAB_ID,"class_id":CLASS_ID,"tranche_index":index,
      "queue_sha256":queue["queue_sha256"],"start_index":start,"end_index_exclusive":end,
      "expected_rows":end-start,"adjudicated_rows":len(adjud),"events":len(events),"failed_attempts":len(attempts),
      "anomalies":len(anomalies),"classification":"TRANCHE_PASS" if not anomalies and len(adjud)==end-start else "TRANCHE_FAIL_CLOSED"
    }
    write_json(out/"TRANCHE_RECEIPT.json",receipt)
    if receipt["classification"]!="TRANCHE_PASS":
        print(json.dumps(receipt,indent=2)); raise SystemExit(2)
    print(json.dumps(receipt,sort_keys=True))

def read_jsonl(path):
    if not Path(path).exists(): return []
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def cmd_finalize(queue_path,tranches_dir):
    queue=json.loads(Path(queue_path).read_text(encoding="utf-8")); rows=queue["rows"]
    if queue["queue_sha256"]!=sha(canon(rows)): raise RuntimeError("QUEUE_HASH_MISMATCH_FINAL")
    root=Path(tranches_dir)
    receipts=[]; adjud=[]; events=[]; attempts=[]; anomalies=[]
    for rp in root.rglob("TRANCHE_RECEIPT.json"):
        r=json.loads(rp.read_text(encoding="utf-8"))
        receipts.append(r)
        d=rp.parent
        adjud+=read_jsonl(d/"adjudications.jsonl"); events+=read_jsonl(d/"events.jsonl")
        attempts+=read_jsonl(d/"attempts.jsonl"); anomalies+=read_jsonl(d/"anomalies.jsonl")
    if not receipts: raise RuntimeError("NO_TRANCHE_RECEIPTS")
    receipts.sort(key=lambda r:r["start_index"])
    cursor=0
    for r in receipts:
        if r["classification"]!="TRANCHE_PASS": raise RuntimeError("NONPASS_TRANCHE")
        if r["queue_sha256"]!=queue["queue_sha256"]: raise RuntimeError("TRANCHE_QUEUE_HASH_MISMATCH")
        if int(r["start_index"])!=cursor: raise RuntimeError(f"TRANCHE_GAP_OR_OVERLAP expected={cursor} got={r['start_index']}")
        cursor=int(r["end_index_exclusive"])
    if cursor!=len(rows): raise RuntimeError(f"INCOMPLETE_TRANCHE_COVERAGE {cursor}/{len(rows)}")
    adjud.sort(key=lambda x:x["queue_index"])
    if len(adjud)!=len(rows): raise RuntimeError("ADJUDICATION_COUNT_MISMATCH")
    for i,(a,q) in enumerate(zip(adjud,rows)):
        if a["queue_index"]!=i or a["signature"]!=q["signature"]: raise RuntimeError(f"ADJUDICATION_QUEUE_MISMATCH {i}")
    if anomalies: raise RuntimeError("ANOMALIES_PRESENT")
    events.sort(key=lambda x:(x["blockTime"],x["slot"],x["signature"]))
    attempts.sort(key=lambda x:(x["blockTime"],x["slot"],x["signature"]))
    if not events: raise RuntimeError("NO_REALIZED_EVENTS_IN_FIRST_CHUNK")
    first=events[0]
    if first["signature"]!=FIRST_SIG or first["slot"]!=FIRST_SLOT or first["blockTime"]!=START_TS:
        raise RuntimeError("FIRST_REALIZED_EVENT_DOES_NOT_RECONCILE_BOUNDARY")
    base=REPO_DIR
    (base/"KAMINO_V1_EVENT_CENSUS_ADJUDICATION_V0.1.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in adjud),encoding="utf-8")
    (base/"KAMINO_V1_EVENT_CENSUS_EVENTS_V0.1.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in events),encoding="utf-8")
    (base/"KAMINO_V1_EVENT_CENSUS_FAILED_ATTEMPTS_V0.1.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in attempts),encoding="utf-8")
    receipt={
      "schema_version":"0.1","lab_id":LAB_ID,"class_id":CLASS_ID,
      "classification":"KAMINO_V1_EVENT_CENSUS_FIRST_CHUNK_PASS",
      "window":{"start":START_ISO,"end":END_ISO,"semantics":"half_open"},
      "queue_rows":len(rows),"queue_sha256":queue["queue_sha256"],"tranches":len(receipts),
      "adjudicated_rows":len(adjud),"realized_events":len(events),"failed_attempts":len(attempts),
      "non_candidate_program_transactions":sum(x["classification"]=="NON_CANDIDATE_PROGRAM_TRANSACTION" for x in adjud),
      "first_realized_event":{"signature":first["signature"],"slot":first["slot"],"blockTime":first["blockTime"],"blockTimeIso":first["blockTimeIso"]},
      "parent":{"run_id":PARENT_RUN,"artifact_id":PARENT_ARTIFACT,"artifact_sha256":PARENT_ARTIFACT_SHA},
      "firewalls":{"prices":False,"returns":False,"pnl":False,"direction":False,"market_outcomes":False,
                   "event_size_threshold_tuning":False,"live_trading":False,"orders":False,"wallets":False,
                   "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}
    }
    write_json(base/"KAMINO_V1_EVENT_CENSUS_CHUNK_RECEIPT_V0.1.json",receipt)
    print(json.dumps(receipt,indent=2,sort_keys=True))

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    q=sub.add_parser("queue"); q.add_argument("--parent",required=True)
    s=sub.add_parser("scan"); s.add_argument("--queue",required=True); s.add_argument("--index",required=True); s.add_argument("--start",required=True); s.add_argument("--end",required=True); s.add_argument("--out",required=True)
    f=sub.add_parser("finalize"); f.add_argument("--queue",required=True); f.add_argument("--tranches",required=True)
    a=ap.parse_args()
    if a.cmd=="queue": cmd_queue(a.parent)
    elif a.cmd=="scan": cmd_scan(a.queue,a.index,a.start,a.end,a.out)
    else: cmd_finalize(a.queue,a.tranches)
if __name__=="__main__": main()
