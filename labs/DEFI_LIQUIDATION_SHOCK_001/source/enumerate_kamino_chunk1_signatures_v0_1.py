#!/usr/bin/env python3
import csv, json, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
START_ISO="2023-11-17T13:25:35Z"
END_ISO="2023-11-24T13:25:35Z"
START_TS=int(datetime.fromisoformat(START_ISO.replace("Z","+00:00")).timestamp())
END_TS=int(datetime.fromisoformat(END_ISO.replace("Z","+00:00")).timestamp())
KNOWN_START_SLOT=230561475
KNOWN_END_SLOT=231964523
PAGE_SIZE=1000
MAX_PAGES=500

def rpc(method,params,retries=10):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for a in range(retries):
        req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-source-audit/1.0"})
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                obj=json.loads(r.read())
            if obj.get("error") and ("Too many requests" in str(obj["error"]) or obj["error"].get("code") in (-32005,429)):
                time.sleep(min(30,2*(a+1))); continue
            return obj
        except Exception as e:
            last=repr(e); time.sleep(min(30,2*(a+1)))
    return {"transport_error":last}

def get_block_time(slot):
    o=rpc("getBlockTime",[slot])
    if o.get("result") is None:
        return None
    return int(o["result"])

def find_guard(start_slot, want_before):
    # strictly before start if want_before, at/after end otherwise
    direction=-1 if want_before else 1
    for d in range(0,256):
        slot=start_slot + direction*d
        bt=get_block_time(slot)
        if bt is None: continue
        if (want_before and bt < START_TS) or ((not want_before) and bt >= END_TS):
            # find a block that contains at least one ordinary tx signature
            for dd in range(0,128):
                s=slot + direction*dd
                o=rpc("getBlock",[s,{"transactionDetails":"signatures","rewards":False,"commitment":"finalized","maxSupportedTransactionVersion":0}])
                res=o.get("result")
                if isinstance(res,dict) and res.get("signatures"):
                    rbt=res.get("blockTime")
                    if rbt is None: continue
                    if want_before and rbt >= START_TS: continue
                    if (not want_before) and rbt < END_TS: continue
                    return {"slot":s,"blockTime":int(rbt),"signature":res["signatures"][0],"block_signature_count":len(res["signatures"])}
    raise RuntimeError("guard block not found")

start_guard=find_guard(KNOWN_START_SLOT,True)
end_guard=find_guard(KNOWN_END_SLOT,False)
print("START_GUARD",start_guard)
print("END_GUARD",end_guard)

all_raw=[]
target=[]
seen=set()
cursor=end_guard["signature"]
terminal=None
prev_slot=None
prev_bt=None
page_receipts=[]
for page_no in range(1,MAX_PAGES+1):
    params=[PROGRAM,{"limit":PAGE_SIZE,"before":cursor,"until":start_guard["signature"],"commitment":"finalized"}]
    o=rpc("getSignaturesForAddress",params)
    if "transport_error" in o:
        terminal="TRANSPORT_ERROR"; page_receipts.append({"page":page_no,"error":o["transport_error"]}); break
    if o.get("error"):
        terminal="RPC_ERROR"; page_receipts.append({"page":page_no,"error":o["error"]}); break
    rows=o.get("result")
    if not isinstance(rows,list):
        terminal="NULL_OR_NONLIST_RESULT"; page_receipts.append({"page":page_no}); break
    if not rows:
        terminal="EMPTY_PAGE_EXHAUSTED"
        page_receipts.append({"page":page_no,"rows":0,"before":cursor})
        break
    page_newest=None; page_oldest=None
    for pos,r in enumerate(rows):
        sig=r.get("signature"); slot=r.get("slot"); bt=r.get("blockTime")
        if not sig or not isinstance(slot,int) or not isinstance(bt,int):
            terminal="STRUCTURAL_ROW_ERROR"; break
        if sig in seen:
            terminal="DUPLICATE_SIGNATURE_FAIL_CLOSED"; break
        # Global RPC ordering should be newest -> oldest. Same slot/time allowed.
        if prev_slot is not None and slot > prev_slot:
            terminal="NONMONOTONIC_SLOT_FAIL_CLOSED"; break
        if prev_bt is not None and bt > prev_bt:
            terminal="NONMONOTONIC_BLOCKTIME_FAIL_CLOSED"; break
        prev_slot,prev_bt=slot,bt
        seen.add(sig)
        rec={
          "page":page_no,"page_position":pos,"signature":sig,"slot":slot,"blockTime":bt,
          "block_time_utc":datetime.fromtimestamp(bt,timezone.utc).isoformat().replace("+00:00","Z"),
          "err":r.get("err"),"memo":r.get("memo"),"confirmationStatus":r.get("confirmationStatus")
        }
        all_raw.append(rec)
        if START_TS <= bt < END_TS:
            target.append(rec)
        page_newest=bt if page_newest is None else max(page_newest,bt)
        page_oldest=bt if page_oldest is None else min(page_oldest,bt)
    if terminal in ("STRUCTURAL_ROW_ERROR","DUPLICATE_SIGNATURE_FAIL_CLOSED","NONMONOTONIC_SLOT_FAIL_CLOSED","NONMONOTONIC_BLOCKTIME_FAIL_CLOSED"):
        break
    page_receipts.append({
      "page":page_no,"rows":len(rows),"cumulative_raw":len(all_raw),"cumulative_target":len(target),
      "newest_utc":datetime.fromtimestamp(page_newest,timezone.utc).isoformat().replace("+00:00","Z"),
      "oldest_utc":datetime.fromtimestamp(page_oldest,timezone.utc).isoformat().replace("+00:00","Z"),
      "before":cursor,"last_signature":rows[-1]["signature"]
    })
    print(f"PAGE {page_no}: rows={len(rows)} target={len(target)} newest={page_receipts[-1]['newest_utc']} oldest={page_receipts[-1]['oldest_utc']}")
    cursor=rows[-1]["signature"]
    if len(rows)<PAGE_SIZE:
        terminal="SHORT_PAGE_EXHAUSTED"
        break
    time.sleep(0.65)
else:
    terminal="MAX_PAGES_EXHAUSTED_FAIL_CLOSED"

# Completeness guards.
duplicates=len(all_raw)-len(seen)
out_of_upper=sum(1 for r in all_raw if r["blockTime"]>=END_TS)
out_of_lower=sum(1 for r in all_raw if r["blockTime"]<START_TS)
oldest_raw=min((r["blockTime"] for r in all_raw),default=None)
newest_raw=max((r["blockTime"] for r in all_raw),default=None)
oldest_target=min((r["blockTime"] for r in target),default=None)
newest_target=max((r["blockTime"] for r in target),default=None)
terminal_ok=terminal in ("EMPTY_PAGE_EXHAUSTED","SHORT_PAGE_EXHAUSTED")
guard_order_ok=start_guard["blockTime"] < START_TS and end_guard["blockTime"] >= END_TS
# Returned rows must remain between transport guards.
guard_leak=sum(1 for r in all_raw if not (start_guard["blockTime"] <= r["blockTime"] <= end_guard["blockTime"]))
classification="KAMINO_CHUNK1_SIGNATURE_ENUMERATION_PASS" if (
    terminal_ok and duplicates==0 and guard_order_ok and guard_leak==0
) else "KAMINO_CHUNK1_SIGNATURE_ENUMERATION_FAIL_CLOSED"

outdir=Path("dls_kamino_chunk1_signature_enumeration_v01"); outdir.mkdir(exist_ok=True)
fields=["page","page_position","signature","slot","blockTime","block_time_utc","err","memo","confirmationStatus"]
for name,rows in [("ALL_GUARD_ROWS.csv",all_raw),("CHUNK1_SIGNATURES.csv",target)]:
    with open(outdir/name,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "phase":"A_COMPLETE_BOUNDED_SIGNATURE_ENUMERATION",
 "classification":classification,
 "endpoint":RPC,"method":"getSignaturesForAddress","program_id":PROGRAM,
 "chunk":{"sequence":1,"start_inclusive":START_ISO,"end_exclusive":END_ISO},
 "transport_guards":{
   "start":{"slot":start_guard["slot"],"blockTime":start_guard["blockTime"],"utc":datetime.fromtimestamp(start_guard["blockTime"],timezone.utc).isoformat().replace("+00:00","Z"),"signature":start_guard["signature"],"block_signature_count":start_guard["block_signature_count"]},
   "end":{"slot":end_guard["slot"],"blockTime":end_guard["blockTime"],"utc":datetime.fromtimestamp(end_guard["blockTime"],timezone.utc).isoformat().replace("+00:00","Z"),"signature":end_guard["signature"],"block_signature_count":end_guard["block_signature_count"]}
 },
 "pagination":{
   "page_size":PAGE_SIZE,"pages_executed":len(page_receipts),"terminal_condition":terminal,
   "raw_rows":len(all_raw),"target_rows":len(target),"unique_signatures":len(seen),
   "duplicates":duplicates,"guard_leak_rows":guard_leak,
   "rows_at_or_after_end_excluded":out_of_upper,"rows_before_start_excluded":out_of_lower,
   "newest_raw_utc":datetime.fromtimestamp(newest_raw,timezone.utc).isoformat().replace("+00:00","Z") if newest_raw else None,
   "oldest_raw_utc":datetime.fromtimestamp(oldest_raw,timezone.utc).isoformat().replace("+00:00","Z") if oldest_raw else None,
   "newest_target_utc":datetime.fromtimestamp(newest_target,timezone.utc).isoformat().replace("+00:00","Z") if newest_target else None,
   "oldest_target_utc":datetime.fromtimestamp(oldest_target,timezone.utc).isoformat().replace("+00:00","Z") if oldest_target else None,
   "pages":page_receipts
 },
 "phase_b_authorized_only_if_pass":classification=="KAMINO_CHUNK1_SIGNATURE_ENUMERATION_PASS",
 "firewalls":{"transaction_bodies_fetched":False,"instruction_data_inspected":False,"liquidation_candidates_classified":False,
   "prices_queried":False,"returns_computed":False,"pnl_computed":False,"direction_tested":False,
   "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False}
}
(outdir/"DLS_KAMINO_CHUNK1_SIGNATURE_ENUMERATION_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print("CLASSIFICATION",classification)
print("TARGET_SIGNATURES",len(target))
print("TERMINAL",terminal)
