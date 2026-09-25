#!/usr/bin/env python3
import datetime as dt, json, time, urllib.request, urllib.error, sys
from pathlib import Path

ROOT=Path(sys.argv[1])
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
OUT=BASE/"DRIFT_FOURTH_CLASS_D8_LOCATOR_RECEIPT_V0.1.json"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
PREFIX="a911205acf94d11b"
RPC="https://api.mainnet-beta.solana.com"
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";MAP={c:i for i,c in enumerate(ALPH)}

def b58(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def iso(s):return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def rpc(sig):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}]},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-drift-fourth-raw/0.1"})
    last=None
    for i in range(10):
        try:
            with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last={"http":e.code}
            if e.code in (429,500,502,503,504):time.sleep(min(45,2*(i+1)));continue
            raise
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(45,2*(i+1)))
    raise RuntimeError(f"rpc_exhausted:{last}")
def iter_ix(res):
    msg=((res.get("transaction") or {}).get("message") or {})
    for i,ix in enumerate(msg.get("instructions") or []):yield [i],ix
    for g in (res.get("meta") or {}).get("innerInstructions") or []:
        outer=g.get("index")
        for j,ix in enumerate(g.get("instructions") or []):yield [outer,j],ix

parts=[]
for p in ROOT.rglob("*.json"):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("class")=="liquidate_borrow_for_perp_pnl" and r.get("start") and r.get("end"):
        parts.append(r)
parts.sort(key=lambda r:iso(r["start"]))
blocked=[r for r in parts if r.get("classification")!="DRIFT_FOURTH_CLASS_LOCATOR_PARTITION_PASS" or r.get("stream_complete") is not True or int(r.get("anomaly_count") or 0)!=0]
candidates=[]
for r in parts:
    c=r.get("earliest_success_candidate")
    if c:candidates.append(c)
candidates.sort(key=lambda r:(iso(r["timestamp"]),r.get("slot",-1),r.get("signature","")))
first=candidates[0] if candidates else None
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
         "classification":"DRIFT_FOURTH_CLASS_LOCATOR_NO_SUCCESS_YET" if not first else "DRIFT_FOURTH_CLASS_LOCATOR_CANDIDATE_PENDING_RAW",
         "partition_count":len(parts),"blocked_partition_count":len(blocked),
         "earliest_success_candidate":first,"raw_verification":None,
         "note":"Locator is not census authority and cannot produce GLOBAL SOURCE PASS.",
         "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
                     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
                     "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
if blocked:
    receipt["classification"]="DRIFT_FOURTH_CLASS_LOCATOR_BLOCKED_FAIL_CLOSED"
elif first:
    obj=rpc(first["signature"]);res=obj.get("result")
    raw={"signature":first["signature"],"expected_slot":first.get("slot"),"expected_timestamp":first.get("timestamp"),
         "expected_instructionAddress":first.get("instructionAddress")}
    passed=False
    if isinstance(res,dict) and (res.get("meta") or {}).get("err") is None:
        slot=res.get("slot")
        bt=res.get("blockTime")
        ts=dt.datetime.fromtimestamp(int(bt),dt.timezone.utc).isoformat().replace("+00:00","Z") if bt is not None else None
        matches=[]
        for addr,ix in iter_ix(res):
            if ix.get("programId")!=PROGRAM:continue
            try:dec=b58(ix.get("data",""))
            except Exception:continue
            if dec.startswith(bytes.fromhex(PREFIX)):
                matches.append({"instructionAddress":addr,"location":"inner" if len(addr)>1 else "outer","prefix":dec[:8].hex()})
        exp_class="inner" if len(first.get("instructionAddress") or [])>1 else "outer"
        got={m["location"] for m in matches}
        passed=(slot==first.get("slot") and ts==first.get("timestamp") and bool(matches) and exp_class in got)
        raw.update({"slot":slot,"timestamp":ts,"matches":matches,"pass":passed})
    else:
        raw.update({"pass":False,"reason":"null_or_failed_transaction"})
    receipt["raw_verification"]=raw
    receipt["classification"]="DRIFT_FOURTH_CLASS_LOCATOR_RAW_VERIFIED_PENDING_FULL_CENSUS_COMPLETENESS" if passed else "DRIFT_FOURTH_CLASS_LOCATOR_RAW_FAIL_CLOSED"

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["classification"] in ("DRIFT_FOURTH_CLASS_LOCATOR_BLOCKED_FAIL_CLOSED","DRIFT_FOURTH_CLASS_LOCATOR_RAW_FAIL_CLOSED"):raise SystemExit(2)
