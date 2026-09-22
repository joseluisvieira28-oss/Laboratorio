#!/usr/bin/env python3
import hashlib, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
TARGET_ISO="2022-12-01T00:00:00Z"
TARGET_TS=int(datetime.fromisoformat(TARGET_ISO.replace("Z","+00:00")).timestamp())

# Frozen source-only reference point already established by the Save 0x0c crawl.
REF_SLOT=175932243
REF_TS=int(datetime.fromisoformat("2023-02-04T05:28:20+00:00").timestamp())

MAX_RETRIES=12
BRACKET_LIMIT=512
MAX_CALIBRATION_ROUNDS=80
MAX_SCAN_BLOCKS=2500
OUT=Path("dls_drift_early_upper_anchor_v03")
OUT.mkdir(parents=True,exist_ok=True)

def rpc(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-source-only/0.1"})
    last=None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                raw=resp.read()
                obj=json.loads(raw)
                if obj.get("error"):
                    last={"rpc_error":obj["error"]}
                    time.sleep(min(60,2*(attempt+1)))
                    continue
                return obj,raw
        except urllib.error.HTTPError as e:
            body=e.read() if hasattr(e,"read") else b""
            last={"http_error":e.code,"body":body[:500].decode("utf-8","replace")}
            if e.code in (429,500,502,503,504):
                time.sleep(min(60,2*(attempt+1)))
                continue
            raise
        except Exception as e:
            last={"transport":repr(e)}
            time.sleep(min(60,2*(attempt+1)))
    raise RuntimeError(f"RPC_EXHAUSTED {method}: {last}")

def block_time(slot):
    obj,_=rpc("getBlockTime",[int(slot)])
    return obj.get("result")

# Coarse slot estimate, then deterministically re-center from actual returned block times.
estimate=REF_SLOT+round((TARGET_TS-REF_TS)/0.4)
calibration=[]
target_slot=None

for round_no in range(1,MAX_CALIBRATION_ROUNDS+1):
    start=max(0,estimate-BRACKET_LIMIT//2)
    obj,_=rpc("getBlocksWithLimit",[int(start),BRACKET_LIMIT])
    slots=obj.get("result")
    if not isinstance(slots,list) or not slots:
        raise RuntimeError("DRIFT_EARLY_UPPER_ANCHOR_RPC_HISTORY_BLOCKED: no produced slots in calibration bracket")

    lo_t=block_time(slots[0])
    hi_t=block_time(slots[-1])
    if lo_t is None or hi_t is None:
        raise RuntimeError("DRIFT_EARLY_UPPER_ANCHOR_SOURCE_ANOMALY_FAIL_CLOSED: null block time on produced slot")

    calibration.append({
        "round":round_no,"estimate":estimate,"start":start,
        "first_slot":int(slots[0]),"first_block_time":int(lo_t),
        "last_slot":int(slots[-1]),"last_block_time":int(hi_t)
    })

    if int(lo_t)<=TARGET_TS<=int(hi_t):
        lo,hi=0,len(slots)-1
        first=None
        while lo<=hi:
            mid=(lo+hi)//2
            t=block_time(slots[mid])
            if t is None:
                raise RuntimeError(f"DRIFT_EARLY_UPPER_ANCHOR_SOURCE_ANOMALY_FAIL_CLOSED: null time at {slots[mid]}")
            if int(t)>=TARGET_TS:
                first=mid
                hi=mid-1
            else:
                lo=mid+1
        if first is None:
            raise RuntimeError("DRIFT_EARLY_UPPER_ANCHOR_SOURCE_ANOMALY_FAIL_CLOSED: target bracket binary search failed")
        target_slot=int(slots[first])
        break

    if TARGET_TS>int(hi_t):
        estimate=int(slots[-1])+round((TARGET_TS-int(hi_t))/0.4)
    else:
        estimate=int(slots[0])+round((TARGET_TS-int(lo_t))/0.4)

if target_slot is None:
    receipt={
      "schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"DRIFT_EARLY_UPPER_ANCHOR_RPC_HISTORY_BLOCKED",
      "reason":"calibration_rounds_exhausted","target_time":TARGET_ISO,
      "calibration":calibration
    }
    Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_EARLY_UPPER_ANCHOR_RECEIPT_V0.3.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    raise SystemExit(0)

obj,_=rpc("getBlocksWithLimit",[target_slot,MAX_SCAN_BLOCKS])
scan_slots=obj.get("result")
if not isinstance(scan_slots,list) or not scan_slots:
    raise RuntimeError("DRIFT_EARLY_UPPER_ANCHOR_RPC_HISTORY_BLOCKED: no produced scan slots")

anchor=None
blocks_scanned=0
for slot in scan_slots:
    obj,raw=rpc("getBlock",[int(slot),{
      "encoding":"jsonParsed","transactionDetails":"accounts","rewards":False,
      "commitment":"finalized","maxSupportedTransactionVersion":0
    }])
    res=obj.get("result")
    if res is None:
        continue
    bt=res.get("blockTime")
    if bt is None or int(bt)<TARGET_TS:
        raise RuntimeError(f"DRIFT_EARLY_UPPER_ANCHOR_SOURCE_ANOMALY_FAIL_CLOSED: chronology {slot} {bt}")
    blocks_scanned+=1
    raw_sha=hashlib.sha256(raw).hexdigest()

    for txe in res.get("transactions") or []:
        tx=txe.get("transaction") or {}
        sigs=tx.get("signatures") or []
        if not sigs:
            continue
        # accounts-only getBlock response exposes accountKeys directly on transaction.
        keys=[]
        for k in tx.get("accountKeys") or []:
            if isinstance(k,str):
                keys.append(k)
            elif isinstance(k,dict) and isinstance(k.get("pubkey"),str):
                keys.append(k["pubkey"])
        if PROGRAM in keys:
            meta=txe.get("meta")
            anchor={
              "signature":sigs[0],
              "slot":int(slot),
              "blockTime":int(bt),
              "blockTimeIso":datetime.fromtimestamp(int(bt),timezone.utc).isoformat().replace("+00:00","Z"),
              "tx_status_success":isinstance(meta,dict) and meta.get("err") is None,
              "block_response_sha256":raw_sha
            }
            break
    if anchor:
        break
    time.sleep(0.04)

classification="DRIFT_EARLY_UPPER_ANCHOR_PASS" if anchor else "DRIFT_EARLY_UPPER_ANCHOR_ACTIVITY_NOT_FOUND"
receipt={
  "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":classification,
  "endpoint":RPC,"program_id":PROGRAM,
  "target_time":TARGET_ISO,
  "source_boundary":"2022-11-04T15:17:54Z",
  "reference":{"slot":REF_SLOT,"blockTime":REF_TS},
  "technical_supersession":"getBlocksWithLimit 40000 -> 512; accounts-only retained",
      "technical_supersession":"getBlocksWithLimit 40000 -> 512; accounts-only retained",
  "calibration":calibration,
  "first_produced_slot_at_or_after_target":target_slot,
  "blocks_scanned":blocks_scanned,
  "anchor":anchor,
  "firewalls":{
    "prices":False,"returns":False,"pnl":False,"direction":False,
    "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
    "liquidation_classification":False,"live_trading":False,"orders":False,
    "wallets":False,"exchange_mutation":False,"paid_source":False,
    "account_creation":False,"merge_main":False
  }
}
Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_EARLY_UPPER_ANCHOR_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
