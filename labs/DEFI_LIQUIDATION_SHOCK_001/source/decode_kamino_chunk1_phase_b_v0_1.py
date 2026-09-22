#!/usr/bin/env python3
import csv, gzip, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
PREFIX_HEX="b1479abce2854a37"
PREFIX=bytes.fromhex(PREFIX_HEX)
EXPECTED_CSV_SHA="27f621aa318c138871a2951d94992acc0d5729b4d0657219ab21232325c5b73e"
EXPECTED_ROWS=10560
BATCH_SIZE=25
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("bad base58")
        n=n*58+MAP[c]
    out=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+out

def post(reqs,retries=12):
    data=json.dumps(reqs,separators=(",",":")).encode()
    last=None
    for a in range(retries):
        q=urllib.request.Request(RPC,data=data,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-source-audit/1.0"})
        try:
            with urllib.request.urlopen(q,timeout=90) as r:
                raw=r.read()
            obj=json.loads(raw)
            return raw,obj,None
        except urllib.error.HTTPError as e:
            try: body=e.read()
            except Exception: body=b""
            last=f"HTTPError {e.code}: {body[:500]!r}"
            if e.code in (429,500,502,503,504):
                time.sleep(min(45,2*(a+1))); continue
            return body,None,last
        except Exception as e:
            last=repr(e); time.sleep(min(45,2*(a+1)))
    return b"",None,last

def instructions(res):
    tx=(res.get("transaction") or {})
    msg=(tx.get("message") or {})
    for i,ins in enumerate(msg.get("instructions") or []):
        yield ("outer",i,None,ins)
    meta=res.get("meta") or {}
    for grp in meta.get("innerInstructions") or []:
        parent=grp.get("index")
        for j,ins in enumerate(grp.get("instructions") or []):
            yield ("inner",j,parent,ins)

root=Path("dls_kamino_chunk1_phase_b_v01")
rawdir=root/"raw_rpc_batches"
root.mkdir(exist_ok=True); rawdir.mkdir(exist_ok=True)
input_path=Path("phase_a/dls_kamino_chunk1_signature_enumeration_v01/CHUNK1_SIGNATURES.csv")
if not input_path.exists():
    raise SystemExit("INPUT_ARTIFACT_MISSING")
data=input_path.read_bytes()
sha=hashlib.sha256(data).hexdigest()
if sha!=EXPECTED_CSV_SHA:
    raise SystemExit(f"INPUT_SHA_MISMATCH {sha}")
rows=list(csv.DictReader(data.decode("utf-8").splitlines()))
if len(rows)!=EXPECTED_ROWS:
    raise SystemExit(f"INPUT_ROW_COUNT_MISMATCH {len(rows)}")
sigs=[r["signature"] for r in rows]
if len(set(sigs))!=EXPECTED_ROWS:
    raise SystemExit("INPUT_SIGNATURE_DUPLICATE")

results={}
transport_errors=[]
batch_receipts=[]
for batch_no,start in enumerate(range(0,len(rows),BATCH_SIZE),1):
    part=rows[start:start+BATCH_SIZE]
    reqs=[]
    for off,r in enumerate(part):
        idx=start+off
        reqs.append({"jsonrpc":"2.0","id":idx,"method":"getTransaction","params":[r["signature"],{"encoding":"jsonParsed","maxSupportedTransactionVersion":0,"commitment":"finalized"}]})
    raw,obj,err=post(reqs)
    if raw:
        with gzip.open(rawdir/f"batch_{batch_no:05d}.json.gz","wb",compresslevel=6) as f:f.write(raw)
    if err or not isinstance(obj,list):
        transport_errors.append({"batch":batch_no,"start_index":start,"size":len(part),"error":err or f"NONLIST:{type(obj).__name__}"})
        continue
    got_ids=set()
    for item in obj:
        if not isinstance(item,dict) or not isinstance(item.get("id"),int): continue
        idx=item["id"]; got_ids.add(idx); results[idx]=item
    missing=[i for i in range(start,start+len(part)) if i not in got_ids]
    if missing:
        transport_errors.append({"batch":batch_no,"missing_ids":missing})
    batch_receipts.append({"batch":batch_no,"start_index":start,"size":len(part),"response_items":len(obj),"missing_ids":missing})
    if batch_no%25==0 or start+len(part)==len(rows):
        print(f"BATCH {batch_no}: resolved={len(results)}/{len(rows)} transport_errors={len(transport_errors)}")
    time.sleep(0.35)

# Retry unresolved individually. Preserve each raw body.
for idx,r in enumerate(rows):
    if idx in results: continue
    req={"jsonrpc":"2.0","id":idx,"method":"getTransaction","params":[r["signature"],{"encoding":"jsonParsed","maxSupportedTransactionVersion":0,"commitment":"finalized"}]}
    raw,obj,err=post([req],retries=10)
    if raw:
        with gzip.open(rawdir/f"retry_{idx:05d}.json.gz","wb",compresslevel=6) as f:f.write(raw)
    if not err and isinstance(obj,list) and len(obj)==1 and isinstance(obj[0],dict) and obj[0].get("id")==idx:
        results[idx]=obj[0]
    else:
        transport_errors.append({"retry_index":idx,"signature":r["signature"],"error":err or "INVALID_RETRY_RESPONSE"})
    time.sleep(0.8)

matches=[]
tx_audit=[]
unavailable=[]
source_anomalies=[]
for idx,r in enumerate(rows):
    item=results.get(idx)
    rec={"index":idx,"signature":r["signature"],"expected_slot":int(r["slot"]),"expected_blockTime":int(r["blockTime"])}
    if not item:
        rec["status"]="TRANSPORT_UNAVAILABLE"; unavailable.append(rec); tx_audit.append(rec); continue
    if item.get("error"):
        rec.update(status="RPC_ERROR",detail=json.dumps(item["error"],sort_keys=True)); unavailable.append(rec); tx_audit.append(rec); continue
    res=item.get("result")
    if not isinstance(res,dict):
        rec["status"]="RPC_NULL_OR_INVALID_RESULT"; unavailable.append(rec); tx_audit.append(rec); continue
    slot=res.get("slot"); bt=res.get("blockTime"); meta=res.get("meta")
    phase_a_success=(r.get("err") or "").strip()==""
    rpc_success=isinstance(meta,dict) and meta.get("err") is None
    slot_ok=slot==int(r["slot"]); bt_ok=bt==int(r["blockTime"]); status_ok=phase_a_success==rpc_success
    rec.update(returned_slot=slot,returned_blockTime=bt,slot_match=slot_ok,blockTime_match=bt_ok,
               phase_a_success=phase_a_success,rpc_success=rpc_success,status_match=status_ok)
    if not (slot_ok and bt_ok and status_ok and isinstance(meta,dict)):
        rec["status"]="SOURCE_CONSISTENCY_FAIL_CLOSED"; source_anomalies.append(rec); tx_audit.append(rec); continue
    nmatch=0
    for loc,pos,parent,ins in instructions(res):
        if not isinstance(ins,dict) or ins.get("programId")!=PROGRAM or not isinstance(ins.get("data"),str): continue
        try: raw=b58decode(ins["data"])
        except Exception: continue
        if raw.startswith(PREFIX):
            nmatch+=1
            matches.append({
              "signature":r["signature"],"slot":slot,"blockTime":bt,"block_time_utc":r["block_time_utc"],
              "instruction_location":loc,"instruction_position":pos,"parent_instruction_index":parent,
              "data_prefix_8_hex":raw[:8].hex(),"transaction_success":rpc_success,
              "classification":"SUCCESSFUL_REALIZED_KAMINO_LIQUIDATION_REFERENCE" if rpc_success else "FAILED_KAMINO_LIQUIDATION_ATTEMPT_NOT_REALIZED"
            })
    rec.update(status="SOURCE_CONSISTENT",kamino_liquidation_match_count=nmatch)
    tx_audit.append(rec)

successful=[m for m in matches if m["transaction_success"]]
failed=[m for m in matches if not m["transaction_success"]]
successful.sort(key=lambda x:(x["blockTime"],x["slot"],x["signature"],0 if x["instruction_location"]=="outer" else 1,
                              x["parent_instruction_index"] if x["parent_instruction_index"] is not None else -1,x["instruction_position"]))
failed.sort(key=lambda x:(x["blockTime"],x["slot"],x["signature"],x["instruction_position"]))
complete=(len(results)==EXPECTED_ROWS and not unavailable and not source_anomalies)
if not complete:
    classification="KAMINO_CHUNK1_PHASE_B_SOURCE_BLOCKED_FAIL_CLOSED"
elif successful:
    classification="KAMINO_CHUNK1_SUCCESSFUL_REFERENCE_FOUND_RAW_REVERIFY_REQUIRED"
else:
    classification="KAMINO_CHUNK1_ZERO_SUCCESSFUL_LIQUIDATION_REFERENCES"

def write_csv(name,items):
    p=root/name
    if not items:
        p.write_text("")
        return
    keys=[]
    for d in items:
        for k in d:
            if k not in keys:keys.append(k)
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(items)

write_csv("TRANSACTION_SOURCE_AUDIT_V0.1.csv",tx_audit)
write_csv("KAMINO_LIQUIDATION_REFERENCE_MATCHES_V0.1.csv",matches)
write_csv("KAMINO_SUCCESSFUL_REALIZED_REFERENCES_V0.1.csv",successful)
write_csv("KAMINO_FAILED_ATTEMPTS_V0.1.csv",failed)
earliest=successful[0] if successful else None
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","phase":"B_EXHAUSTIVE_TRANSACTION_DECODE",
 "classification":classification,
 "input_binding":{"phase_a_csv_sha256":sha,"rows":len(rows),"expected_sha256":EXPECTED_CSV_SHA},
 "rpc":{"endpoint":RPC,"method":"getTransaction","encoding":"jsonParsed","batch_size":BATCH_SIZE,
        "raw_response_storage":"gzip lossless raw HTTP response bodies"},
 "retrieval":{"frozen_transactions":EXPECTED_ROWS,"response_items_resolved":len(results),
              "unavailable_count":len(unavailable),"source_anomaly_count":len(source_anomalies),
              "transport_error_records":len(transport_errors),"raw_batch_files":len(list(rawdir.glob("*.gz")))},
 "decoder":{"program_id":PROGRAM,"prefix_hex":PREFIX_HEX,
            "total_matching_instructions":len(matches),"successful_matching_instructions":len(successful),
            "failed_matching_instructions":len(failed)},
 "earliest_successful_reference":earliest,
 "raw_reverify_required":bool(earliest),
 "phase_c_authorized_only_if_complete":complete,
 "firewalls":{"prices_queried":False,"returns_computed":False,"pnl_computed":False,"direction_tested":False,
              "market_outcomes_opened":False,"live_trading":False,"orders":False,"wallets":False,
              "exchange_mutation":False,"paid_source":False,"merge_main":False}
}
(root/"DLS_KAMINO_CHUNK1_PHASE_B_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
(root/"TRANSPORT_ERROR_LOG_V0.1.json").write_text(json.dumps(transport_errors,indent=2,sort_keys=True)+"\n")
print("CLASSIFICATION",classification)
print("RESOLVED",len(results),"/",EXPECTED_ROWS)
print("SOURCE_ANOMALIES",len(source_anomalies),"UNAVAILABLE",len(unavailable))
print("MATCHES",len(matches),"SUCCESSFUL",len(successful),"FAILED",len(failed))
if earliest: print("EARLIEST",json.dumps(earliest,sort_keys=True))
