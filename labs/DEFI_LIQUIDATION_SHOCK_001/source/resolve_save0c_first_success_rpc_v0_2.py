#!/usr/bin/env python3
import base64, hashlib, json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
PREFIX_HEX="0c"
PREFIX=bytes.fromhex(PREFIX_HEX)
BOUNDARY_ISO="2021-12-08T00:00:00Z"
BOUNDARY_TS=int(datetime.fromisoformat(BOUNDARY_ISO.replace("Z","+00:00")).timestamp())
ANCHOR_SIG="44b86ujEfT2EvYnXSV47pct5wv2dJQD3T8KkVePPaPcNPx9zRpkPxmorPjLn64FUovmnYSL1mU4qguV9ykZazB9P"
ANCHOR_SLOT=235155834
ANCHOR_TS=int(datetime.fromisoformat("2023-12-10T21:21:20+00:00").timestamp())
ANCHOR_ERR={"InstructionError":[3,{"Custom":29}]}
PAGE_LIMIT=1000
MAX_PAGES=5000
MAX_RETRIES=12
OUT=Path("dls_save0c_rpc_boundary_v02")
OUT.mkdir(parents=True,exist_ok=True)
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def b58decode(s):
    n=0
    for c in s:
        if c not in MAP:
            raise ValueError("non-base58")
        n=n*58+MAP[c]
    body=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+body

def rpc_call(method, params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-source-only/0.1"})
    last=None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req,timeout=45) as resp:
                raw=resp.read()
                obj=json.loads(raw)
                if obj.get("error"):
                    code=obj["error"].get("code")
                    if code in (-32005,429) or "Too many requests" in str(obj["error"]):
                        last={"rpc_error":obj["error"]}
                        time.sleep(min(60,2*(attempt+1)))
                        continue
                return obj, raw
        except urllib.error.HTTPError as e:
            body=e.read() if hasattr(e,"read") else b""
            last={"http_error":e.code,"body":body[:500].decode("utf-8","replace")}
            if e.code in (429,500,502,503,504):
                retry=e.headers.get("Retry-After") if e.headers else None
                time.sleep(min(60,int(retry) if retry and retry.isdigit() else 2*(attempt+1)))
                continue
            break
        except Exception as e:
            last={"transport_error":repr(e)}
            time.sleep(min(60,2*(attempt+1)))
    raise RuntimeError(f"RPC_EXHAUSTED {method}: {last}")

def resolve_block_time(row):
    bt=row.get("blockTime")
    if bt is not None:
        return int(bt)
    obj,_=rpc_call("getBlockTime",[int(row["slot"])])
    if obj.get("error") or obj.get("result") is None:
        raise RuntimeError(f"NULL_BLOCKTIME slot={row.get('slot')}")
    return int(obj["result"])

def instruction_iter(result):
    tx=(result.get("transaction") or {})
    msg=(tx.get("message") or {})
    for ins in msg.get("instructions") or []:
        yield "outer",ins
    meta=result.get("meta") or {}
    for group in meta.get("innerInstructions") or []:
        for ins in group.get("instructions") or []:
            yield "inner",ins

def matches_liquidation(result):
    for loc,ins in instruction_iter(result):
        if ins.get("programId")!=PROGRAM:
            continue
        data=ins.get("data")
        if not isinstance(data,str):
            continue
        try:
            raw=b58decode(data)
        except Exception:
            continue
        if raw.startswith(PREFIX):
            return True,loc,data
    return False,None,None

def write_json(name,obj):
    p=OUT/name
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return p

state={
 "schema_version":"0.2","boundary_class":"SAVE0C","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "transport":"official_public_solana_rpc","endpoint":RPC,
 "program_id":PROGRAM,"discriminator":PREFIX_HEX,
 "source_boundary":BOUNDARY_ISO,
 "anchor":{"signature":ANCHOR_SIG,"slot":ANCHOR_SLOT,"block_time":ANCHOR_TS,"err":ANCHOR_ERR},
 "continuation_parent_run_id":35716197055,
 "resume_cursor_extraction_run_id":35732854347,
 "resume_cursor_page_sha256":"00ea8f13874c2520622d0991c9ae7179456a6278d4463be44ba08a1109e1f056",
 "phase":"PHASE_A_SIGNATURE_CRAWL","pages_completed":0,"signatures_seen":0,
 "crossed_lower_boundary":False,
 "firewalls":{"prices":False,"returns":False,"pnl":False,"direction":False,
 "market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
 "wallets":False,"exchange_mutation":False,"paid_source":False,"merge_main":False}
}
write_json("CHECKPOINT.json",state)

seen=set()
rows=[]
cursor=ANCHOR_SIG
prev_bt=ANCHOR_TS
for page_no in range(1,MAX_PAGES+1):
    obj,raw=rpc_call("getSignaturesForAddress",[PROGRAM,{"commitment":"finalized","limit":PAGE_LIMIT,"before":cursor}])
    write_json(f"signatures_page_{page_no:04d}.json",obj)
    page=obj.get("result")
    if not isinstance(page,list):
        raise RuntimeError("SIGNATURE_PAGE_NOT_LIST")
    if not page:
        state.update(phase="BLOCKED",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED",reason="history_exhausted_before_crossing_lower_boundary")
        write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
        print(json.dumps(state,indent=2)); sys.exit(0)
    for row in page:
        sig=row.get("signature")
        if not isinstance(sig,str) or sig in seen:
            raise RuntimeError(f"DUPLICATE_OR_INVALID_SIGNATURE {sig}")
        seen.add(sig)
        bt=resolve_block_time(row)
        if bt>prev_bt:
            raise RuntimeError(f"NON_MONOTONIC_SIGNATURE_TIME {bt}>{prev_bt}")
        prev_bt=bt
        rec={"signature":sig,"slot":int(row["slot"]),"blockTime":bt,"err":row.get("err")}
        rows.append(rec)
    cursor=page[-1]["signature"]
    state["pages_completed"]=page_no
    state["signatures_seen"]=len(rows)
    state["oldest_block_time"]=rows[-1]["blockTime"]
    write_json("CHECKPOINT.json",state)
    print(f"PHASE_A page={page_no} signatures={len(rows)} oldest={rows[-1]['blockTime']}",flush=True)
    if rows[-1]["blockTime"]<BOUNDARY_TS:
        state["crossed_lower_boundary"]=True
        break
    time.sleep(0.4)

if not state["crossed_lower_boundary"]:
    state.update(phase="BLOCKED",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED",reason="max_pages_reached_before_lower_boundary")
    write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
    print(json.dumps(state,indent=2)); sys.exit(0)

# Persist the complete enumerated signature slice before transaction-content inspection.
write_json("SIGNATURE_CRAWL_COMPLETE.json",{"rows":rows,"sha256":sha256_bytes(json.dumps(rows,separators=(",",":"),sort_keys=True).encode())})

eligible=[r for r in rows if r["blockTime"]>=BOUNDARY_TS and r["blockTime"]<int(datetime.fromisoformat("2025-01-01T00:00:00+00:00").timestamp())]
eligible.append({"signature":ANCHOR_SIG,"slot":ANCHOR_SLOT,"blockTime":ANCHOR_TS,"err":ANCHOR_ERR,"frozen_anchor":True})
eligible.sort(key=lambda r:(r["blockTime"],r["slot"],r["signature"]))

state.update(phase="PHASE_B_RAW_OLDEST_TO_NEWEST",eligible_transactions=len(eligible),successful_signatures=sum(r.get("err") is None for r in eligible))
write_json("CHECKPOINT.json",state)

raw_checked=0
for pos,row in enumerate(eligible):
    if row.get("err") is not None:
        continue
    sig=row["signature"]
    obj,raw=rpc_call("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}])
    raw_checked+=1
    p=OUT/f"tx_{pos:07d}_{sig}.json"
    p.write_bytes(raw)
    res=obj.get("result")
    if res is None:
        state.update(phase="BLOCKED",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED",
                     reason="null_raw_transaction_before_first_match",blocked_signature=sig,raw_transactions_checked=raw_checked)
        write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
        print(json.dumps(state,indent=2)); sys.exit(0)
    if int(res.get("slot",-1))!=int(row["slot"]):
        state.update(phase="FAIL_CLOSED",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_SOURCE_ANOMALY_FAIL_CLOSED",
                     reason="slot_mismatch",signature=sig,expected_slot=row["slot"],returned_slot=res.get("slot"))
        write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
        print(json.dumps(state,indent=2)); sys.exit(0)
    meta=res.get("meta")
    if not isinstance(meta,dict):
        state.update(phase="FAIL_CLOSED",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_SOURCE_ANOMALY_FAIL_CLOSED",
                     reason="missing_meta",signature=sig)
        write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
        print(json.dumps(state,indent=2)); sys.exit(0)
    # getSignaturesForAddress said success, RAW must agree.
    if meta.get("err") is not None:
        state.update(phase="FAIL_CLOSED",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_SOURCE_ANOMALY_FAIL_CLOSED",
                     reason="signature_success_raw_failure_mismatch",signature=sig,raw_err=meta.get("err"))
        write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
        print(json.dumps(state,indent=2)); sys.exit(0)
    matched,location,data=matches_liquidation(res)
    if matched:
        block_time=res.get("blockTime")
        if block_time is None:
            block_time=row["blockTime"]
        boundary={
          "signature":sig,"slot":int(row["slot"]),"blockTime":int(block_time),
          "blockTimeIso":datetime.fromtimestamp(int(block_time),tz=timezone.utc).isoformat().replace("+00:00","Z"),
          "instruction_location":location,"data_prefix_hex":PREFIX_HEX,
          "raw_file":p.name,"raw_sha256":sha256_bytes(raw)
        }
        state.update(phase="COMPLETE",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_PASS",
                     raw_transactions_checked=raw_checked,first_success_boundary=boundary)
        write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
        print(json.dumps(state,indent=2)); sys.exit(0)
    if raw_checked%100==0:
        state["raw_transactions_checked"]=raw_checked
        state["last_checked_signature"]=sig
        write_json("CHECKPOINT.json",state)
        print(f"PHASE_B raw_checked={raw_checked}",flush=True)
    time.sleep(0.2)

state.update(phase="COMPLETE_NO_MATCH",classification="SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE",
             reason="no_liquidation_match_between_source_boundary_and_resume_cursor",
             raw_transactions_checked=raw_checked)
write_json("DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.2.json",state)
print(json.dumps(state,indent=2))
