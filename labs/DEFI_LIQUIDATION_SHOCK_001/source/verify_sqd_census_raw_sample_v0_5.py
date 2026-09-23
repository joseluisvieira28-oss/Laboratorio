#!/usr/bin/env python3
import hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
ROOT=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
CROOT=ROOT/"sqd_census_v0_4"
SUMMARY=ROOT/"KAMINO_SAVE11_SQD_EVENT_CENSUS_RECEIPT_V0.4.2.json"
QUEUE=CROOT/"RAW_SAMPLE_QUEUE_V0.4.2.json"
RAWROOT=CROOT/"raw_sample_v0_5"
OUT=ROOT/"KAMINO_SAVE11_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.5.json"
RAWROOT.mkdir(parents=True,exist_ok=True)

PROTOCOLS={
 "kamino":{"program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","prefix_hex":"b1479abce2854a37"},
 "save11":{"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix_hex":"11"}
}
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("non-base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def sha(b): return hashlib.sha256(b).hexdigest()

def rpc(sig,retries=12):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[
      sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}
    ]},separators=(",",":")).encode()
    last=None
    for i in range(retries):
        req=urllib.request.Request(RPC,data=payload,headers={
          "Content-Type":"application/json","User-Agent":"crypto-lab-dls-raw-reconcile/0.5"})
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                raw=resp.read()
                obj=json.loads(raw)
                if obj.get("error"):
                    code=obj["error"].get("code")
                    if code in (-32005,429) or "Too many requests" in str(obj["error"]):
                        last={"rpc_error":obj["error"]}
                        time.sleep(min(60,2*(i+1))); continue
                return obj,raw,None
        except urllib.error.HTTPError as e:
            body=e.read() if hasattr(e,"read") else b""
            last={"http":e.code,"body":body[:500].decode("utf-8","replace")}
            if e.code in (429,500,502,503,504):
                time.sleep(min(60,2*(i+1))); continue
            return None,None,last
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:500]}
            time.sleep(min(60,2*(i+1)))
    return None,None,last

def raw_matches(res,program,prefix):
    out=[]
    tx=res.get("transaction") or {}
    msg=tx.get("message") or {}
    for i,ins in enumerate(msg.get("instructions") or []):
        if ins.get("programId")!=program or not isinstance(ins.get("data"),str):
            continue
        try: dec=b58decode(ins["data"])
        except Exception: continue
        if dec.startswith(prefix):
            out.append([i])
    meta=res.get("meta") or {}
    for group in meta.get("innerInstructions") or []:
        parent=group.get("index")
        if not isinstance(parent,int): continue
        for j,ins in enumerate(group.get("instructions") or []):
            if ins.get("programId")!=program or not isinstance(ins.get("data"),str):
                continue
            try: dec=b58decode(ins["data"])
            except Exception: continue
            if dec.startswith(prefix):
                out.append([parent,j])
    return out

summary=json.loads(SUMMARY.read_text())
if summary.get("classification")!="SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE":
    raise SystemExit("CENSUS_NOT_COMPLETE_FAIL_CLOSED")
queue=json.loads(QUEUE.read_text())

expected={}
for p in sorted((CROOT/"chunks").glob("*")):
    if not p.is_dir(): continue
    protocol=p.name
    expected[protocol]={}
    for ledger in sorted(p.glob("*.ledger.jsonl")):
        for line in ledger.read_text().splitlines():
            if not line.strip(): continue
            r=json.loads(line)
            if r.get("classification")!="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION":
                continue
            expected[protocol].setdefault(r["signature"],[]).append(r)

rows=[]
for protocol,cfg in PROTOCOLS.items():
    sample=((queue.get("protocols") or {}).get(protocol) or {}).get("sample_signatures") or []
    pdir=RAWROOT/protocol
    pdir.mkdir(parents=True,exist_ok=True)
    prefix=bytes.fromhex(cfg["prefix_hex"])
    for idx,sig in enumerate(sample):
        exp=(expected.get(protocol) or {}).get(sig) or []
        rec={"protocol":protocol,"signature":sig,"sample_index":idx,"expected_row_count":len(exp)}
        if not exp:
            rec.update(status="CONTENT_MISMATCH_FAIL_CLOSED",reason="sample_signature_missing_from_success_ledger")
            rows.append(rec); continue
        slots={int(x["slot"]) for x in exp}
        times={int(x["timestamp"]) for x in exp}
        exp_paths={tuple(x["instructionAddress"]) for x in exp}
        rec["expected_slots"]=sorted(slots)
        rec["expected_timestamps"]=sorted(times)
        rec["expected_instruction_paths"]=[list(x) for x in sorted(exp_paths)]
        if len(slots)!=1 or len(times)!=1:
            rec.update(status="CONTENT_MISMATCH_FAIL_CLOSED",reason="census_signature_has_multiple_slot_or_time_values")
            rows.append(rec); continue

        obj,raw,terr=rpc(sig)
        if obj is None:
            rec.update(status="TRANSPORT_BLOCKED",reason=terr)
            rows.append(rec); continue
        rawfile=pdir/f"{idx:02d}_{sig}.json"
        rawfile.write_bytes(raw)
        rec["raw_file"]=str(rawfile)
        rec["raw_sha256"]=sha(raw)
        if obj.get("error"):
            rec.update(status="TRANSPORT_BLOCKED",reason={"rpc_error":obj["error"]})
            rows.append(rec); continue
        res=obj.get("result")
        if res is None:
            rec.update(status="TRANSPORT_BLOCKED",reason="null_raw_transaction")
            rows.append(rec); continue

        tx=(res.get("transaction") or {})
        sigs=tx.get("signatures") or []
        rec["requested_signature_present"]=sig in sigs
        rec["returned_slot"]=res.get("slot")
        rec["returned_block_time"]=res.get("blockTime")
        meta=res.get("meta")
        rec["meta_err"]=meta.get("err") if isinstance(meta,dict) else "MISSING_META"
        paths=raw_matches(res,cfg["program"],prefix)
        raw_path_set={tuple(x) for x in paths}
        rec["raw_matching_instruction_paths"]=[list(x) for x in sorted(raw_path_set)]
        checks={
          "requested_signature_present":sig in sigs,
          "slot_exact":res.get("slot")==next(iter(slots)),
          "block_time_exact":res.get("blockTime")==next(iter(times)),
          "meta_err_null":isinstance(meta,dict) and meta.get("err") is None,
          "instruction_path_set_exact":raw_path_set==exp_paths,
          "at_least_one_exact_instruction":len(raw_path_set)>0
        }
        rec["checks"]=checks
        if all(checks.values()):
            rec["status"]="RAW_SAMPLE_SIGNATURE_PASS"
        else:
            rec["status"]="CONTENT_MISMATCH_FAIL_CLOSED"
        rows.append(rec)
        print(protocol,idx+1,len(sample),sig[:12],rec["status"],flush=True)
        time.sleep(0.35)

passed=sum(r["status"]=="RAW_SAMPLE_SIGNATURE_PASS" for r in rows)
mismatch=sum(r["status"]=="CONTENT_MISMATCH_FAIL_CLOSED" for r in rows)
blocked=sum(r["status"]=="TRANSPORT_BLOCKED" for r in rows)
if mismatch:
    classification="RAW_SAMPLE_RECONCILIATION_MISMATCH_FAIL_CLOSED"
elif blocked:
    classification="RAW_SAMPLE_RECONCILIATION_TRANSPORT_BLOCKED"
elif passed==len(rows) and len(rows)>0:
    classification="RAW_SAMPLE_RECONCILIATION_PASS"
else:
    classification="RAW_SAMPLE_RECONCILIATION_MISMATCH_FAIL_CLOSED"

receipt={
 "schema_version":"0.5","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,"endpoint":RPC,
 "sample_signature_count":len(rows),"passed_count":passed,
 "transport_blocked_count":blocked,"content_mismatch_count":mismatch,
 "rows":rows,
 "firewall":{
   "balances_interpreted":False,"token_balances_interpreted":False,"fees_interpreted":False,
   "amounts_interpreted":False,"prices":False,"returns":False,"pnl":False,"direction":False,
   "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
   "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
   "paid_source":False,"account_creation":False,"merge_main":False
 }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"classification":classification,"sample_signature_count":len(rows),
                  "passed_count":passed,"transport_blocked_count":blocked,
                  "content_mismatch_count":mismatch},indent=2,sort_keys=True))
if classification!="RAW_SAMPLE_RECONCILIATION_PASS":
    raise SystemExit(2)
