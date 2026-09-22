#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
START_BEFORE="37bfneBLcVoWnqWEoP7Y4EnJREUeaHeEYgnQ9kjBGpsN3tMjP2AceURMpbgQDeR8hmxZ4L5JVSokepJ7WhsuTDnK"
BOUNDARY_ISO="2023-11-17T13:25:35Z"
BOUNDARY_TS=int(datetime.fromisoformat(BOUNDARY_ISO.replace("Z","+00:00")).timestamp())
PAGE_SIZE=1000
MAX_PAGES=100

def rpc_call(before):
    payload={"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress",
             "params":[PROGRAM,{"limit":PAGE_SIZE,"before":before,"commitment":"finalized"}]}
    data=json.dumps(payload).encode()
    last=None
    for attempt in range(8):
        req=urllib.request.Request(RPC,data=data,headers={
            "Content-Type":"application/json",
            "User-Agent":"crypto-lab-source-audit/1.0"
        })
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                obj=json.loads(r.read())
            if obj.get("error"):
                code=obj["error"].get("code")
                if code in (-32005,429) or "Too many requests" in str(obj["error"]):
                    time.sleep(min(30,2*(attempt+1)))
                    continue
            return obj
        except Exception as e:
            last=repr(e)
            time.sleep(min(30,2*(attempt+1)))
    return {"transport_error":last}

pages=[]
cursor=START_BEFORE
seen=set()
cumulative=0
classification=None
for page_no in range(1,MAX_PAGES+1):
    if cursor in seen:
        classification="KAMINO_PUBLIC_RPC_HISTORY_REPEATED_CURSOR_BLOCKED"
        break
    seen.add(cursor)
    obj=rpc_call(cursor)
    if "transport_error" in obj:
        pages.append({"page":page_no,"before":cursor,"transport_error":obj["transport_error"]})
        classification="KAMINO_PUBLIC_RPC_HISTORY_TRANSPORT_BLOCKED"
        break
    if obj.get("error"):
        pages.append({"page":page_no,"before":cursor,"rpc_error":obj["error"]})
        classification="KAMINO_PUBLIC_RPC_HISTORY_RPC_ERROR_BLOCKED"
        break
    rows=obj.get("result")
    if rows is None:
        pages.append({"page":page_no,"before":cursor,"result_null":True})
        classification="KAMINO_PUBLIC_RPC_HISTORY_NULL_BLOCKED"
        break
    if not rows:
        pages.append({"page":page_no,"before":cursor,"rows":0})
        classification="KAMINO_PUBLIC_RPC_HISTORY_EXHAUSTED_BEFORE_BOUNDARY"
        break
    times=[r.get("blockTime") for r in rows if isinstance(r.get("blockTime"),int)]
    if not times:
        pages.append({"page":page_no,"before":cursor,"rows":len(rows),"blocktime_missing":True})
        classification="KAMINO_PUBLIC_RPC_HISTORY_BLOCKTIME_MISSING_FAIL_CLOSED"
        break
    newest=max(times); oldest=min(times)
    cumulative += len(rows)
    last_sig=rows[-1].get("signature")
    first_sig=rows[0].get("signature")
    pages.append({
        "page":page_no,
        "rows":len(rows),
        "cumulative_rows":cumulative,
        "newest_block_time":newest,
        "newest_utc":datetime.fromtimestamp(newest,timezone.utc).isoformat().replace("+00:00","Z"),
        "oldest_block_time":oldest,
        "oldest_utc":datetime.fromtimestamp(oldest,timezone.utc).isoformat().replace("+00:00","Z"),
        "first_signature":first_sig,
        "last_signature":last_sig,
        "boundary_reached":oldest <= BOUNDARY_TS
    })
    print(f"PAGE {page_no}: rows={len(rows)} cumulative={cumulative} oldest={pages[-1]['oldest_utc']}")
    if oldest <= BOUNDARY_TS:
        classification="KAMINO_PUBLIC_RPC_HISTORY_BOUNDARY_REACHABLE"
        break
    if not last_sig:
        classification="KAMINO_PUBLIC_RPC_HISTORY_CURSOR_MISSING_FAIL_CLOSED"
        break
    cursor=last_sig
    time.sleep(0.75)
else:
    classification="KAMINO_PUBLIC_RPC_HISTORY_PAGE_LIMIT_BEFORE_BOUNDARY"

receipt={
 "schema_version":"0.1",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,
 "endpoint":RPC,
 "method":"getSignaturesForAddress",
 "program_id":PROGRAM,
 "start_before":START_BEFORE,
 "boundary_utc":BOUNDARY_ISO,
 "page_size":PAGE_SIZE,
 "max_pages":MAX_PAGES,
 "pages_executed":len(pages),
 "cumulative_rows":cumulative,
 "pages":pages,
 "firewalls":{
   "getTransaction_called":False,
   "instruction_data_inspected":False,
   "liquidation_candidates_classified":False,
   "prices_queried":False,
   "returns_computed":False,
   "pnl_computed":False,
   "direction_tested":False,
   "live_trading":False,
   "orders":False,
   "wallets":False,
   "exchange_mutation":False,
   "paid_source":False
 }
}
Path("DLS_KAMINO_PUBLIC_RPC_HISTORY_DEPTH_PROBE_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print("CLASSIFICATION",classification)
print("CUMULATIVE_ROWS",cumulative)
