#!/usr/bin/env python3
import json, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
START_ISO="2023-11-17T13:25:35Z"
END_ISO="2023-11-24T13:25:35Z"
START_TS=int(datetime.fromisoformat(START_ISO.replace("Z","+00:00")).timestamp())
END_TS=int(datetime.fromisoformat(END_ISO.replace("Z","+00:00")).timestamp())
LOW_SLOT=150_000_000
HIGH_SLOT=307_588_986

def rpc(method, params, retries=8):
    data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for a in range(retries):
        req=urllib.request.Request(RPC,data=data,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-source-audit/1.0"})
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                obj=json.loads(r.read())
            if obj.get("error") and ("Too many requests" in str(obj["error"]) or obj["error"].get("code") in (-32005,429)):
                time.sleep(min(20,2*(a+1))); continue
            return obj
        except Exception as e:
            last=repr(e); time.sleep(min(20,2*(a+1)))
    return {"transport_error":last}

def block_time_near(slot):
    # deterministic local neighborhood only to survive skipped slots
    for d in range(0,65):
        for s in ([slot] if d==0 else [slot-d,slot+d]):
            if s < 0: continue
            o=rpc("getBlockTime",[s])
            if o.get("result") is not None:
                return s,int(o["result"])
    raise RuntimeError(f"no blockTime within +/-64 of slot {slot}")

def locate(target):
    lo,hi=LOW_SLOT,HIGH_SLOT
    best=None
    for _ in range(32):
        if lo>hi: break
        mid=(lo+hi)//2
        s,t=block_time_near(mid)
        if best is None or abs(t-target)<abs(best[1]-target):
            best=(s,t)
        if t < target:
            lo=max(lo+1,s+1)
        elif t > target:
            hi=min(hi-1,s-1)
        else:
            return s,t
    return best

def block_signature(slot):
    for d in range(0,65):
        for s in ([slot] if d==0 else [slot-d,slot+d]):
            o=rpc("getBlock",[s,{"transactionDetails":"signatures","rewards":False,"commitment":"finalized","maxSupportedTransactionVersion":0}])
            res=o.get("result")
            if isinstance(res,dict) and res.get("signatures"):
                return s,res.get("blockTime"),res["signatures"][0],len(res["signatures"])
    raise RuntimeError(f"no block with signatures within +/-64 of {slot}")

start_slot,start_bt=locate(START_TS)
end_slot,end_bt=locate(END_TS)
sslot,sbt,start_sig,start_block_n=block_signature(start_slot)
eslot,ebt,end_sig,end_block_n=block_signature(end_slot)

tests={}
for name,params in [
    ("before_only",[PROGRAM,{"limit":5,"before":end_sig,"commitment":"finalized"}]),
    ("before_until",[PROGRAM,{"limit":1000,"before":end_sig,"until":start_sig,"commitment":"finalized"}]),
]:
    o=rpc("getSignaturesForAddress",params)
    rec={"error":o.get("error"),"transport_error":o.get("transport_error")}
    rows=o.get("result")
    if isinstance(rows,list):
        times=[x.get("blockTime") for x in rows if isinstance(x.get("blockTime"),int)]
        rec.update(
            rows=len(rows),
            newest_utc=datetime.fromtimestamp(max(times),timezone.utc).isoformat().replace("+00:00","Z") if times else None,
            oldest_utc=datetime.fromtimestamp(min(times),timezone.utc).isoformat().replace("+00:00","Z") if times else None,
            first_signature=rows[0].get("signature") if rows else None,
            last_signature=rows[-1].get("signature") if rows else None,
            all_at_or_before_end=all(t <= ebt for t in times) if times else None,
            all_at_or_after_start=all(t >= sbt for t in times) if times else None,
        )
    tests[name]=rec

before_ok=(not tests["before_only"].get("error") and not tests["before_only"].get("transport_error")
           and tests["before_only"].get("rows",0)>0 and tests["before_only"].get("all_at_or_before_end") is True)
bounded_rows=tests["before_until"].get("rows")
until_effective=(not tests["before_until"].get("error") and not tests["before_until"].get("transport_error")
                 and bounded_rows is not None and tests["before_until"].get("all_at_or_before_end") is True
                 and tests["before_until"].get("all_at_or_after_start") is True)
if before_ok and until_effective:
    classification="KAMINO_PUBLIC_RPC_ARBITRARY_CURSOR_BOUNDED_WINDOW_SUPPORTED"
elif before_ok:
    classification="KAMINO_PUBLIC_RPC_ARBITRARY_BEFORE_SUPPORTED_UNTIL_UNRESOLVED"
else:
    classification="KAMINO_PUBLIC_RPC_ARBITRARY_CURSOR_NOT_SUPPORTED_OR_BLOCKED"

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "target_window":{"start":START_ISO,"end_exclusive":END_ISO},
 "located":{"start_slot":sslot,"start_block_time":sbt,"start_utc":datetime.fromtimestamp(sbt,timezone.utc).isoformat().replace("+00:00","Z"),
            "start_cursor_signature":start_sig,"start_block_signature_count":start_block_n,
            "end_slot":eslot,"end_block_time":ebt,"end_utc":datetime.fromtimestamp(ebt,timezone.utc).isoformat().replace("+00:00","Z"),
            "end_cursor_signature":end_sig,"end_block_signature_count":end_block_n},
 "tests":tests,
 "firewalls":{"transaction_bodies_fetched":False,"instruction_data_inspected":False,"liquidation_candidates_classified":False,
              "prices_queried":False,"returns_computed":False,"pnl_computed":False,"direction_tested":False,
              "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False}
}
Path("DLS_KAMINO_PUBLIC_RPC_ARBITRARY_CURSOR_SEMANTICS_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
