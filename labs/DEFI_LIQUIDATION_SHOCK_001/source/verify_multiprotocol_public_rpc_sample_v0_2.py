#!/usr/bin/env python3
import json, time, urllib.request
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE_FILE=ROOT/"DLS_MULTIPROTOCOL_RAW_VALIDATION_SAMPLE_V0.2.json"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58={c:i for i,c in enumerate(ALPH)}

def b58decode(s):
    n=0
    for c in s:
        n=n*58+B58[c]
    out=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+out

def call(sig):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","maxSupportedTransactionVersion":0,"commitment":"finalized"}]}).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-source-audit/0.2"})
    err=None
    for i in range(6):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            err=repr(e)
            time.sleep(min(2*(i+1),10))
    return {"transport_error":err}

def instructions(result,loc):
    if loc=="outer":
        return (((result.get("transaction") or {}).get("message") or {}).get("instructions") or [])
    out=[]
    for g in ((result.get("meta") or {}).get("innerInstructions") or []):
        out.extend(g.get("instructions") or [])
    return out

spec=json.loads(CANDIDATE_FILE.read_text())
outdir=Path("dls_multiprotocol_public_rpc_rawverify_v02"); outdir.mkdir(exist_ok=True)
rows=[]
for c in spec["candidates"]:
    sig=c["tx_signature"]; obj=call(sig)
    (outdir/f'{c["index"]:02d}_{sig}.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    rec={k:c[k] for k in ["index","protocol","match_name","program_id","reference_prefix_hex","block_slot","block_timestamp","tx_signature","instruction_location","sample_rank"]}
    if "transport_error" in obj:
        rec.update(status="TRANSPORT_ERROR",detail=obj["transport_error"]); rows.append(rec); continue
    if obj.get("error"):
        rec.update(status="RPC_ERROR",detail=obj["error"]); rows.append(rec); continue
    res=obj.get("result")
    if res is None:
        rec.update(status="RPC_NULL_HISTORY_UNAVAILABLE"); rows.append(rec); continue
    rec["returned_slot"]=res.get("slot")
    rec["slot_match"]=res.get("slot")==c["block_slot"]
    meta=res.get("meta")
    rec["meta_err"]=meta.get("err") if isinstance(meta,dict) else "META_MISSING"
    rec["tx_success"]=isinstance(meta,dict) and meta.get("err") is None
    prefix=bytes.fromhex(c["reference_prefix_hex"])
    found=False
    for ins in instructions(res,c["instruction_location"]):
        if ins.get("programId")!=c["program_id"] or not isinstance(ins.get("data"),str):
            continue
        try: raw=b58decode(ins["data"])
        except Exception: continue
        if raw.startswith(prefix):
            found=True; break
    rec["program_prefix_location_match"]=found
    if not rec["slot_match"] or not found:
        rec["status"]="RAW_CONTENT_MISMATCH_FAIL_CLOSED"
    elif rec["tx_success"]:
        rec["status"]="RAW_VERIFIED_SUCCESSFUL_LIQUIDATION_REFERENCE"
    else:
        rec["status"]="RAW_VERIFIED_FAILED_ATTEMPT_NOT_REALIZED"
    rows.append(rec)
    time.sleep(0.75)

classes={}
for r in rows:
    key=f'{r["protocol"]}|{r["match_name"]}'
    d=classes.setdefault(key,{"rows":0,"structural_valid":0,"successful":0,"failed_attempts":0,"transport_blocked":0,"content_mismatch":0})
    d["rows"]+=1
    s=r["status"]
    if s.startswith("RAW_VERIFIED_"): d["structural_valid"]+=1
    if s=="RAW_VERIFIED_SUCCESSFUL_LIQUIDATION_REFERENCE": d["successful"]+=1
    if s=="RAW_VERIFIED_FAILED_ATTEMPT_NOT_REALIZED": d["failed_attempts"]+=1
    if s in ("TRANSPORT_ERROR","RPC_ERROR","RPC_NULL_HISTORY_UNAVAILABLE"): d["transport_blocked"]+=1
    if s=="RAW_CONTENT_MISMATCH_FAIL_CLOSED": d["content_mismatch"]+=1
for k,d in classes.items():
    if d["content_mismatch"]:
        d["classification"]="RAW_CONTENT_MISMATCH_FAIL_CLOSED"
    elif d["successful"]>0:
        d["classification"]="REALIZED_SUCCESS_CONFIRMED_BY_2024_12_15"
    elif d["transport_blocked"]>0:
        d["classification"]="TRANSPORT_BLOCKED"
    else:
        d["classification"]="DECODER_CONFIRMED_SUCCESS_NOT_ESTABLISHED"

summary={
 "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"MULTIPROTOCOL_RAW_SAMPLE_VERIFICATION_COMPLETE",
 "global_source_data_pass":False,
 "endpoint":RPC,"candidate_count":len(rows),
 "successful_raw_verified":sum(r["status"]=="RAW_VERIFIED_SUCCESSFUL_LIQUIDATION_REFERENCE" for r in rows),
 "failed_attempt_raw_verified":sum(r["status"]=="RAW_VERIFIED_FAILED_ATTEMPT_NOT_REALIZED" for r in rows),
 "transport_blocked":sum(r["status"] in ("TRANSPORT_ERROR","RPC_ERROR","RPC_NULL_HISTORY_UNAVAILABLE") for r in rows),
 "content_mismatch":sum(r["status"]=="RAW_CONTENT_MISMATCH_FAIL_CLOSED" for r in rows),
 "classes":classes,"rows":rows,
 "firewalls":{"prices_queried":False,"returns_computed":False,"pnl_computed":False,"direction_tested":False,"market_response_opened":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False}
}
(outdir/"DLS_MULTIPROTOCOL_PUBLIC_RPC_RAWVERIFY_RECEIPT_V0.2.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,indent=2,sort_keys=True))
