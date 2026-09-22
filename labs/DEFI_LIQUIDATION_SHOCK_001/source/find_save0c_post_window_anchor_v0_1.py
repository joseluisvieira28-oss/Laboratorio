#!/usr/bin/env python3
import hashlib, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
TARGET_TS=int(datetime.fromisoformat("2025-01-01T00:00:00+00:00").timestamp())
REF_SLOT=307588986
REF_TS=int(datetime.fromisoformat("2024-12-15T07:32:56+00:00").timestamp())
PROGRAMS={
    "save_solend":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
}
MAX_RETRIES=10
OUT=Path("dls_save0c_upper_anchor_v01")
OUT.mkdir(parents=True,exist_ok=True)

def rpc(method, params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-source-only/0.1"})
    last=None
    for i in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                raw=resp.read()
                obj=json.loads(raw)
                if obj.get("error"):
                    last={"rpc_error":obj["error"]}
                    time.sleep(min(30,2*(i+1)))
                    continue
                return obj,raw
        except urllib.error.HTTPError as e:
            last={"http":e.code}
            if e.code in (429,500,502,503,504):
                time.sleep(min(30,2*(i+1))); continue
            raise
        except Exception as e:
            last={"transport":repr(e)}
            time.sleep(min(30,2*(i+1)))
    raise RuntimeError(f"RPC_EXHAUSTED {method}: {last}")

def bt(slot):
    obj,_=rpc("getBlockTime",[int(slot)])
    return obj.get("result")

# Solana ~400 ms/slot. Use the frozen 2024-12-15 reference only to center a broad outcome-blind time bracket.
estimate=REF_SLOT+round((TARGET_TS-REF_TS)/0.4)
start=max(0,estimate-50000)
obj,_=rpc("getBlocksWithLimit",[start,100000])
slots=obj.get("result")
if not isinstance(slots,list) or not slots:
    raise RuntimeError("NO_PRODUCED_SLOTS_IN_BRACKET")

# Binary search produced slots by blockTime.
lo,hi=0,len(slots)-1
first_idx=None
while lo<=hi:
    mid=(lo+hi)//2
    t=bt(slots[mid])
    if t is None:
        raise RuntimeError(f"NULL_BLOCKTIME_PRODUCED_SLOT {slots[mid]}")
    if int(t)>=TARGET_TS:
        first_idx=mid; hi=mid-1
    else:
        lo=mid+1
if first_idx is None:
    raise RuntimeError("TARGET_TIME_NOT_REACHED_IN_BRACKET")

anchors={}
block_receipts=[]
scan_slots=slots[first_idx:first_idx+5000]
for n,slot in enumerate(scan_slots,1):
    obj,raw=rpc("getBlock",[int(slot),{
        "encoding":"jsonParsed",
        "transactionDetails":"full",
        "rewards":False,
        "commitment":"finalized",
        "maxSupportedTransactionVersion":0
    }])
    res=obj.get("result")
    if res is None:
        continue
    block_time=res.get("blockTime")
    if block_time is None or int(block_time)<TARGET_TS:
        raise RuntimeError(f"CHRONOLOGY_FAIL slot={slot} blockTime={block_time}")
    raw_sha=hashlib.sha256(raw).hexdigest()
    txs=res.get("transactions") or []
    for txe in txs:
        tx=txe.get("transaction") or {}
        sigs=tx.get("signatures") or []
        if not sigs: continue
        msg=tx.get("message") or {}
        keys=[]
        for k in msg.get("accountKeys") or []:
            if isinstance(k,str): keys.append(k)
            elif isinstance(k,dict) and isinstance(k.get("pubkey"),str): keys.append(k["pubkey"])
        for name,pid in PROGRAMS.items():
            if name not in anchors and pid in keys:
                meta=txe.get("meta")
                anchors[name]={
                    "program_id":pid,
                    "signature":sigs[0],
                    "slot":int(slot),
                    "blockTime":int(block_time),
                    "blockTimeIso":datetime.fromtimestamp(int(block_time),timezone.utc).isoformat().replace("+00:00","Z"),
                    "tx_status_success":isinstance(meta,dict) and meta.get("err") is None,
                    "block_response_sha256":raw_sha,
                    "scanned_block_ordinal":n
                }
    block_receipts.append({"slot":int(slot),"blockTime":int(block_time),"sha256":raw_sha,"transactions":len(txs)})
    if len(anchors)==len(PROGRAMS):
        break
    time.sleep(0.15)

if "save_solend" in anchors:
    classification="SAVE0C_POST_WINDOW_UPPER_ANCHOR_PASS"
else:
    classification="SAVE0C_POST_WINDOW_UPPER_ANCHOR_BLOCKED"

receipt={
    "schema_version":"0.1",
    "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
    "classification":classification,
    "endpoint":RPC,
    "target_time":"2025-01-01T00:00:00Z",
    "reference":{"slot":REF_SLOT,"blockTime":REF_TS},
    "slot_estimate":estimate,
    "produced_slot_bracket_start":start,
    "first_produced_slot_at_or_after_target":int(slots[first_idx]),
    "blocks_scanned":len(block_receipts),
    "anchors":anchors,
    "firewalls":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
                 "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
                 "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}
}
(OUT/"BLOCK_RECEIPTS.json").write_text(json.dumps(block_receipts,indent=2,sort_keys=True)+"\n")
Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_POST_WINDOW_UPPER_ANCHOR_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
