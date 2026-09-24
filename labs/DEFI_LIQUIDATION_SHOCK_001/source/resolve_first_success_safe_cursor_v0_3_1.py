#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PAGE_LIMIT=1000
TOTAL_PAGE_CAP=5000
MAX_RETRIES=12
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")

CFG={
 "marginfi":{
   "program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
   "prefix_hex":"d6a997d5fba756db",
   "boundary_iso":"2023-02-07T15:47:04Z",
   "upper_iso":"2025-01-01T00:00:00Z",
   "accepted_pages":205,
   "safe_page_sha":"72fce2cff5cc66d3b8881fbd7e9b6d17743f2c8fb30370073fd337ca3276f6b0",
   "safe_sig":"53dZ2HZHdFMisHmhPS1BS4pXhaD98YggaS7zYwshBFwza5mntJTANDvWthxagjgxc39eTg8eCq5eoyqFfTrKVW6m",
   "safe_slot":238600457,
   "safe_bt":1703805655,
   "safe_err":None,
   "cursor_receipt":BASE/"MARGINFI_V03_CANCEL_RECOVERY_CURSOR_V0.1.json",
   "cursor_class":"MARGINFI_V03_CANCEL_RECOVERY_CURSOR_EXTRACTED",
   "parent_run_id":35771014450,
   "parent_artifact_id":10713843479,
   "parent_artifact_name":"dls-marginfi-first-success-rpc-v03",
   "out":Path("dls_marginfi_rpc_boundary_v031"),
   "receipt":"DLS_MARGINFI_RPC_FIRST_SUCCESS_RECEIPT_V0.3.1.json",
   "pass_class":"MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_PASS",
   "blocked_class":"MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED",
   "no_match_class":"MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE",
   "anomaly_class":"MARGINFI_FIRST_SUCCESS_BOUNDARY_SOURCE_ANOMALY_FAIL_CLOSED",
 },
 "save0c":{
   "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
   "prefix_hex":"0c",
   "boundary_iso":"2021-12-08T00:00:00Z",
   "upper_iso":"2025-01-01T00:00:00Z",
   "accepted_pages":217,
   "safe_page_sha":"f21c44c8525bd11b0f1227d709cce16b1a79e10429570faa6766dfa1111a269c",
   "safe_sig":"4XfzrMP3m4vJSBmnsoqA9kG3pjRhjBvbCRrTeh3162FSzBoyVegaFxiCWxyaxrf5yxEGmtjoyM5qA5W9KUHLAyfu",
   "safe_slot":175929092,
   "safe_bt":1675484461,
   "safe_err":{"InstructionError":[2,{"Custom":42}]},
   "cursor_receipt":BASE/"SAVE0C_V03_SAFE_CURSOR_V0.1.json",
   "cursor_class":"SAVE0C_V03_SAFE_CURSOR_PAGE217_EXTRACTED",
   "parent_run_id":35771022352,
   "parent_artifact_id":10714501324,
   "parent_artifact_name":"dls-save0c-first-success-rpc-v03",
   "out":Path("dls_save0c_rpc_boundary_v031"),
   "receipt":"DLS_SAVE0C_RPC_FIRST_SUCCESS_RECEIPT_V0.3.1.json",
   "pass_class":"SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_PASS",
   "blocked_class":"SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED",
   "no_match_class":"SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_NO_MATCH_IN_EARLIEST_SLICE",
   "anomaly_class":"SAVE0C_FIRST_SUCCESS_BOUNDARY_SOURCE_ANOMALY_FAIL_CLOSED",
 }
}

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def b58decode(s):
    n=0
    for c in s:
        if c not in MAP:
            raise ValueError("non-base58")
        n=n*58+MAP[c]
    body=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+body

def rpc_call(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-source-only/0.3.1"})
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
                return obj,raw
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

def resolve_bt(row):
    bt=row.get("blockTime")
    if bt is not None:
        return int(bt)
    obj,_=rpc_call("getBlockTime",[int(row["slot"])])
    if obj.get("error") or obj.get("result") is None:
        raise RuntimeError(f"NULL_BLOCKTIME slot={row.get('slot')}")
    return int(obj["result"])

def instruction_iter(result):
    tx=result.get("transaction") or {}
    msg=tx.get("message") or {}
    for ins in msg.get("instructions") or []:
        yield "outer",ins
    for group in (result.get("meta") or {}).get("innerInstructions") or []:
        for ins in group.get("instructions") or []:
            yield "inner",ins

def matches_instruction(result,program,prefix):
    for loc,ins in instruction_iter(result):
        if ins.get("programId")!=program:
            continue
        data=ins.get("data")
        if not isinstance(data,str):
            continue
        try:
            dec=b58decode(data)
        except Exception:
            continue
        if dec.startswith(prefix):
            return True,loc,dec[:len(prefix)].hex()
    return False,None,None

def write_json(out,name,obj):
    p=out/name
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    return p

def fail(state,out,cfg,classification,reason,**extra):
    state.update(phase="FAIL_CLOSED" if "ANOMALY" in classification else "BLOCKED",
                 classification=classification,reason=reason,**extra)
    write_json(out,cfg["receipt"],state)
    print(json.dumps(state,indent=2,sort_keys=True))
    raise SystemExit(2 if "ANOMALY" in classification else 0)

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=sorted(CFG),required=True)
ap.add_argument("--parent",required=True)
args=ap.parse_args()

protocol=args.protocol
cfg=CFG[protocol]
out=cfg["out"]
out.mkdir(parents=True,exist_ok=True)
prefix=bytes.fromhex(cfg["prefix_hex"])
boundary_ts=int(datetime.fromisoformat(cfg["boundary_iso"].replace("Z","+00:00")).timestamp())
upper_ts=int(datetime.fromisoformat(cfg["upper_iso"].replace("Z","+00:00")).timestamp())
remaining=TOTAL_PAGE_CAP-cfg["accepted_pages"]

state={
 "schema_version":"0.3.1",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "boundary_class":protocol.upper(),
 "transport":"official_public_solana_rpc",
 "endpoint":RPC,
 "program_id":cfg["program"],
 "discriminator":cfg["prefix_hex"],
 "source_boundary":cfg["boundary_iso"],
 "scientific_upper_exclusive":cfg["upper_iso"],
 "continuation_parent_run_id":cfg["parent_run_id"],
 "parent_artifact_id":cfg["parent_artifact_id"],
 "parent_artifact_name":cfg["parent_artifact_name"],
 "accepted_parent_pages":cfg["accepted_pages"],
 "frozen_total_page_cap":TOTAL_PAGE_CAP,
 "remaining_page_budget":remaining,
 "safe_cursor":{
   "signature":cfg["safe_sig"],"slot":cfg["safe_slot"],
   "blockTime":cfg["safe_bt"],"err":cfg["safe_err"],
   "accepted_page_sha256":cfg["safe_page_sha"]
 },
 "phase":"PARENT_CONTINUITY_AUDIT",
 "pages_completed":0,
 "signatures_seen":0,
 "crossed_lower_boundary":False,
 "firewalls":{
   "prices":False,"returns":False,"pnl":False,"direction":False,
   "event_outcomes":False,"market_outcomes_2025_2026":False,
   "live_trading":False,"orders":False,"wallets":False,
   "exchange_mutation":False,"paid_source":False,
   "account_creation":False,"merge_main":False
 }
}
write_json(out,"CHECKPOINT.json",state)

# Verify the repository-persisted safe-cursor authority.
cr=json.loads(cfg["cursor_receipt"].read_text())
if cr.get("classification")!=cfg["cursor_class"]:
    fail(state,out,cfg,cfg["anomaly_class"],"safe_cursor_classification_mismatch",observed=cr.get("classification"))
page_field="selected_page_number" if protocol=="marginfi" else "accepted_page_number"
if int(cr.get(page_field,-1))!=cfg["accepted_pages"]:
    fail(state,out,cfg,cfg["anomaly_class"],"safe_cursor_page_number_mismatch",observed=cr.get(page_field))
if cr.get("resume_before_signature")!=cfg["safe_sig"] or int(cr.get("resume_slot",-1))!=cfg["safe_slot"] or int(cr.get("resume_block_time",-1))!=cfg["safe_bt"]:
    fail(state,out,cfg,cfg["anomaly_class"],"safe_cursor_identity_mismatch")
if cr.get("page_sha256")!=cfg["safe_page_sha"]:
    fail(state,out,cfg,cfg["anomaly_class"],"safe_cursor_page_hash_authority_mismatch")

parent=Path(args.parent)
all_parent_pages={}
for p in parent.rglob("signatures_page_*.json"):
    try:
        n=int(p.stem.split("_")[-1])
    except Exception:
        continue
    all_parent_pages.setdefault(n,[]).append(p)

ignored_orphan_pages=sorted(n for n in all_parent_pages if n>cfg["accepted_pages"])
seen=set()
page_records=[]
prev_bt=None
rolling=hashlib.sha256()

for page_no in range(1,cfg["accepted_pages"]+1):
    candidates=all_parent_pages.get(page_no,[])
    if len(candidates)!=1:
        fail(state,out,cfg,cfg["anomaly_class"],"accepted_parent_page_resolution_failure",page=page_no,count=len(candidates))
    p=candidates[0]
    if page_no==cfg["accepted_pages"] and sha256_file(p)!=cfg["safe_page_sha"]:
        fail(state,out,cfg,cfg["anomaly_class"],"accepted_safe_page_sha_mismatch",page=page_no,actual=sha256_file(p))
    obj=json.loads(p.read_text())
    page=obj.get("result")
    if not isinstance(page,list) or len(page)!=PAGE_LIMIT:
        fail(state,out,cfg,cfg["anomaly_class"],"accepted_parent_page_shape_failure",page=page_no,row_count=len(page) if isinstance(page,list) else None)
    for row in page:
        sig=row.get("signature")
        if not isinstance(sig,str) or not sig or sig in seen:
            fail(state,out,cfg,cfg["anomaly_class"],"parent_duplicate_or_invalid_signature",page=page_no,signature=sig)
        seen.add(sig)
        bt=resolve_bt(row)
        if prev_bt is not None and bt>prev_bt:
            fail(state,out,cfg,cfg["anomaly_class"],"parent_non_monotonic_block_time",page=page_no,current=bt,previous=prev_bt)
        prev_bt=bt
        rolling.update((sig+"|"+str(int(row["slot"]))+"|"+str(bt)+"\n").encode())
    page_records.append({"page":page_no,"path":str(p),"source":"accepted_parent","sha256":sha256_file(p)})

last_parent=json.loads(page_records[-1] and Path(page_records[-1]["path"]).read_text()).get("result")[-1]
if last_parent.get("signature")!=cfg["safe_sig"] or int(last_parent.get("slot",-1))!=cfg["safe_slot"] or resolve_bt(last_parent)!=cfg["safe_bt"] or last_parent.get("err")!=cfg["safe_err"]:
    fail(state,out,cfg,cfg["anomaly_class"],"safe_cursor_not_exact_last_row_of_accepted_parent")

state.update(
 phase="PHASE_A_SIGNATURE_CRAWL_CONTINUATION",
 pages_completed=cfg["accepted_pages"],
 signatures_seen=len(seen),
 oldest_block_time=prev_bt,
 ignored_parent_pages=ignored_orphan_pages,
 parent_continuity_rolling_sha256=rolling.hexdigest()
)
write_json(out,"CHECKPOINT.json",state)
print(f"PARENT_PASS protocol={protocol} accepted_pages={cfg['accepted_pages']} ignored_orphans={ignored_orphan_pages}",flush=True)

cursor=cfg["safe_sig"]
crossed=prev_bt<boundary_ts
for page_no in range(cfg["accepted_pages"]+1,TOTAL_PAGE_CAP+1):
    if crossed:
        break
    obj,raw=rpc_call("getSignaturesForAddress",[cfg["program"],{"commitment":"finalized","limit":PAGE_LIMIT,"before":cursor}])
    p=write_json(out,f"signatures_page_{page_no:04d}.json",obj)
    page=obj.get("result")
    if not isinstance(page,list):
        fail(state,out,cfg,cfg["anomaly_class"],"signature_page_not_list",page=page_no)
    if not page:
        fail(state,out,cfg,cfg["blocked_class"],"history_exhausted_before_crossing_lower_boundary",page=page_no)
    for row in page:
        sig=row.get("signature")
        if not isinstance(sig,str) or not sig or sig in seen:
            fail(state,out,cfg,cfg["anomaly_class"],"continuation_duplicate_or_invalid_signature",page=page_no,signature=sig)
        seen.add(sig)
        bt=resolve_bt(row)
        if bt>prev_bt:
            fail(state,out,cfg,cfg["anomaly_class"],"continuation_non_monotonic_block_time",page=page_no,current=bt,previous=prev_bt)
        prev_bt=bt
        rolling.update((sig+"|"+str(int(row["slot"]))+"|"+str(bt)+"\n").encode())
    cursor=page[-1]["signature"]
    page_records.append({"page":page_no,"path":str(p),"source":"continuation","sha256":sha256_file(p)})
    state.update(pages_completed=page_no,signatures_seen=len(seen),oldest_block_time=prev_bt,
                 continuation_pages_completed=page_no-cfg["accepted_pages"],
                 full_continuity_rolling_sha256=rolling.hexdigest())
    write_json(out,"CHECKPOINT.json",state)
    print(f"PHASE_A protocol={protocol} page={page_no} signatures={len(seen)} oldest={prev_bt}",flush=True)
    if prev_bt<boundary_ts:
        crossed=True
        state["crossed_lower_boundary"]=True
        break
    time.sleep(0.4)

if not crossed:
    fail(state,out,cfg,cfg["blocked_class"],"max_total_pages_reached_before_lower_boundary",
         pages_completed=state.get("pages_completed"),remaining_budget=remaining)

state["crossed_lower_boundary"]=True
crawl_manifest={
 "schema_version":"0.3.1",
 "protocol":protocol,
 "accepted_parent_pages":cfg["accepted_pages"],
 "ignored_parent_pages":ignored_orphan_pages,
 "pages_completed":state["pages_completed"],
 "signatures_seen":state["signatures_seen"],
 "lower_boundary_crossed":True,
 "rolling_sha256":rolling.hexdigest(),
 "pages":page_records
}
write_json(out,"SIGNATURE_CRAWL_COMPLETE_MANIFEST.json",crawl_manifest)

# Phase B: use every accepted parent page plus every authoritative continuation page,
# oldest-to-newest, without loading the full multi-million-row slice into memory.
state.update(phase="PHASE_B_RAW_OLDEST_TO_NEWEST",raw_transactions_checked=0)
write_json(out,"CHECKPOINT.json",state)
raw_checked=0
eligible_successes=0

for prec in reversed(page_records):
    pobj=json.loads(Path(prec["path"]).read_text())
    page=pobj.get("result") or []
    for row in reversed(page):
        bt=resolve_bt(row)
        if bt<boundary_ts or bt>=upper_ts:
            continue
        if row.get("err") is not None:
            continue
        eligible_successes+=1
        sig=row["signature"]
        obj,raw=rpc_call("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}])
        raw_checked+=1
        raw_name=f"tx_{raw_checked:07d}_{sig}.json"
        raw_path=out/raw_name
        raw_path.write_bytes(raw)
        res=obj.get("result")
        if res is None:
            fail(state,out,cfg,cfg["blocked_class"],"null_raw_transaction_before_first_match",
                 blocked_signature=sig,raw_transactions_checked=raw_checked)
        if int(res.get("slot",-1))!=int(row["slot"]):
            fail(state,out,cfg,cfg["anomaly_class"],"slot_mismatch",signature=sig,
                 expected_slot=int(row["slot"]),returned_slot=res.get("slot"))
        meta=res.get("meta")
        if not isinstance(meta,dict):
            fail(state,out,cfg,cfg["anomaly_class"],"missing_meta",signature=sig)
        if meta.get("err") is not None:
            fail(state,out,cfg,cfg["anomaly_class"],"signature_success_raw_failure_mismatch",
                 signature=sig,raw_err=meta.get("err"))
        matched,location,prefix_hex=matches_instruction(res,cfg["program"],prefix)
        if matched:
            block_time=res.get("blockTime")
            if block_time is None:
                block_time=bt
            boundary={
              "signature":sig,
              "slot":int(row["slot"]),
              "blockTime":int(block_time),
              "blockTimeIso":datetime.fromtimestamp(int(block_time),tz=timezone.utc).isoformat().replace("+00:00","Z"),
              "instruction_location":location,
              "data_prefix_hex":prefix_hex,
              "raw_file":raw_name,
              "raw_sha256":sha256_bytes(raw)
            }
            state.update(
              phase="COMPLETE",
              classification=cfg["pass_class"],
              raw_transactions_checked=raw_checked,
              eligible_success_signatures_seen=eligible_successes,
              first_success_boundary=boundary
            )
            write_json(out,cfg["receipt"],state)
            print(json.dumps(state,indent=2,sort_keys=True))
            raise SystemExit(0)
        if raw_checked%100==0:
            state.update(raw_transactions_checked=raw_checked,last_checked_signature=sig,
                         eligible_success_signatures_seen=eligible_successes)
            write_json(out,"CHECKPOINT.json",state)
            print(f"PHASE_B protocol={protocol} raw_checked={raw_checked}",flush=True)
        time.sleep(0.2)

state.update(
 phase="COMPLETE_NO_MATCH",
 classification=cfg["no_match_class"],
 reason="no_exact_liquidation_match_between_lower_boundary_and_original_continuity_upper_range",
 raw_transactions_checked=raw_checked,
 eligible_success_signatures_seen=eligible_successes
)
write_json(out,cfg["receipt"],state)
print(json.dumps(state,indent=2,sort_keys=True))
