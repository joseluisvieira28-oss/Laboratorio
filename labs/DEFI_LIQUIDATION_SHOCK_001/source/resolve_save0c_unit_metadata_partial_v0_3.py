#!/usr/bin/env python3
import argparse, base64, json, time, urllib.request
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.3.json")
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58e(b):
    n=int.from_bytes(b,"big"); s=""
    while n:
        n,r=divmod(n,58); s=ALPH[r]+s
    pad=0
    for x in b:
        if x==0: pad+=1
        else: break
    return "1"*pad+(s or ("" if pad else "1"))

def find_one(root,name):
    hits=list(Path(root).rglob(name))
    if not hits:return None
    return json.loads(sorted(hits)[0].read_text())

def rpc_slice(targets,offset,length,retries=8):
    body={"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
          "params":[targets,{"encoding":"base64","commitment":"finalized","dataSlice":{"offset":offset,"length":length}}]}
    raw=json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=raw,headers={"Content-Type":"application/json",
        "User-Agent":"crypto-lab-dls-save0c-unit-completion/0.3"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                o=json.loads(r.read())
                if o.get("error"): raise RuntimeError(str(o["error"]))
                return o["result"]["value"]
        except Exception as e:
            last=str(e)[:300]; time.sleep(min(30,2**i))
    raise RuntimeError(f"rpc_exhausted:{last}")

ap=argparse.ArgumentParser()
ap.add_argument("--aggregate",required=True)
ap.add_argument("--partitions",required=True)
ap.add_argument("--historical-registry",required=True)
args=ap.parse_args()

agg=find_one(args.aggregate,"SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json")
hist=find_one(args.historical_registry,"SAVE0C_HISTORICAL_RESERVE_REGISTRY_RECEIPT_V0.1.json")
errors=[]
if not agg:
    errors.append({"reason":"missing_v0_1_aggregate"})
elif agg.get("classification")!="SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE":
    errors.append({"reason":"invalid_trigger_classification","classification":agg.get("classification")})
if not hist:
    errors.append({"reason":"missing_historical_registry_receipt"})
elif hist.get("classification")!="SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS":
    errors.append({"reason":"historical_registry_not_pass","classification":hist.get("classification")})

targets=sorted({x["reserve"] for x in (agg or {}).get("unmapped_reserves") or []})
hist_registry=(hist or {}).get("registry") or {}
recovered={}; pending=[]; source_conflicts=[]

# First authority: historical official SDK registry.
for reserve in targets:
    ent=hist_registry.get(reserve)
    if not ent: continue
    mint=ent.get("underlying_mint"); dec=ent.get("underlying_decimals"); coll=ent.get("collateral_mint")
    if not mint or dec is None or not coll:
        source_conflicts.append({"reserve":reserve,"reason":"historical_registry_entry_incomplete","entry":ent})
        continue
    recovered[reserve]={
        "underlying_mint":mint,
        "underlying_decimals":int(dec),
        "collateral_mint":coll,
        "source":"official_solend_sdk_historical_registry_v0.1"
    }

# Second authority: exact calibrated current-state slices, only for unresolved targets.
rpc_targets=[r for r in targets if r not in recovered]
if not errors and rpc_targets:
    for i in range(0,len(rpc_targets),100):
        chunk=rpc_targets[i:i+100]
        a=rpc_slice(chunk,42,33); b=rpc_slice(chunk,227,32)
        for j,reserve in enumerate(chunk):
            ra=a[j] if j<len(a) else None; rb=b[j] if j<len(b) else None
            if ra is None or rb is None:
                pending.append({"reserve":reserve,"reason":"account_missing_after_historical_registry_miss"}); continue
            if ra.get("owner")!=PROGRAM or rb.get("owner")!=PROGRAM:
                source_conflicts.append({"reserve":reserve,"reason":"owner_mismatch",
                                         "owner_a":ra.get("owner"),"owner_b":rb.get("owner")}); continue
            try:
                da=base64.b64decode((ra.get("data") or [""])[0]); db=base64.b64decode((rb.get("data") or [""])[0])
            except Exception:
                source_conflicts.append({"reserve":reserve,"reason":"base64_decode_failed"}); continue
            if len(da)!=33 or len(db)!=32:
                source_conflicts.append({"reserve":reserve,"reason":"slice_length_mismatch",
                                         "len_a":len(da),"len_b":len(db)}); continue
            recovered[reserve]={
                "underlying_mint":b58e(da[:32]),
                "underlying_decimals":int(da[32]),
                "collateral_mint":b58e(db),
                "source":"finalized_rpc_dataslice_v0.3"
            }

event_total=0;unit_complete=0;still_unmapped={};event_conflicts=[]
partition_count=0
for p in sorted(Path(args.partitions).rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol")!="save0c" or not str(r.get("classification","")).startswith("SAVE0C_UNIT_METADATA_PARTITION_"):
        continue
    partition_count+=1
    for e in r.get("event_units") or []:
        event_total+=1
        if e.get("collateral_underlying"):
            unit_complete+=1; continue
        reserve=e.get("withdraw_reserve")
        ext=recovered.get(reserve)
        if not ext:
            still_unmapped[reserve]=still_unmapped.get(reserve,0)+1
            continue
        ctok=e.get("collateral_token") or {}
        if ctok.get("mint")!=ext["collateral_mint"]:
            event_conflicts.append({
                "signature":e.get("signature"),"reserve":reserve,
                "reason":"recovered_collateral_mint_conflict",
                "observed":ctok.get("mint"),"expected":ext["collateral_mint"],
                "source":ext["source"]
            })
            continue
        unit_complete+=1

EXPECTED=66628; EXPECTED_PARTITIONS=37
if partition_count!=EXPECTED_PARTITIONS:
    errors.append({"reason":"partition_count_mismatch","observed":partition_count,"expected":EXPECTED_PARTITIONS})
if event_total!=EXPECTED:
    errors.append({"reason":"event_total_mismatch","observed":event_total,"expected":EXPECTED})

if source_conflicts or event_conflicts or errors:
    classification="SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED"
elif still_unmapped or pending or unit_complete!=EXPECTED:
    classification="SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE"
else:
    classification="SAVE0C_UNIT_METADATA_POPULATION_PASS"

receipt={
 "schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "trigger_classification":(agg or {}).get("classification"),
 "historical_registry_classification":(hist or {}).get("classification"),
 "target_reserve_count":len(targets),
 "historical_recovered_reserve_count":sum(1 for x in recovered.values() if x["source"].startswith("official_")),
 "rpc_recovered_reserve_count":sum(1 for x in recovered.values() if x["source"].startswith("finalized_")),
 "recovered_reserve_count":len(recovered),
 "pending_reserve_count":len(pending),"pending_reserves":pending,
 "source_conflict_count":len(source_conflicts),"source_conflicts":source_conflicts,
 "partition_count":partition_count,"event_total":event_total,"unit_complete_event_count":unit_complete,
 "still_unmapped_event_count":EXPECTED-unit_complete,
 "unique_still_unmapped_reserve_count":len(still_unmapped),
 "still_unmapped_reserves":[{"reserve":k,"event_count":v} for k,v in sorted(still_unmapped.items(),key=lambda kv:(-kv[1],kv[0]))],
 "event_conflict_count":len(event_conflicts),"event_conflicts":event_conflicts[:100],
 "registry_extension":[{"reserve":k,**v} for k,v in sorted(recovered.items())],
 "error_count":len(errors),"errors":errors,
 "full_reserve_state_requested":False,"economic_amount_fields_decoded":False,"oracle_fields_read":False,
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"reserve_amounts":False,"token_amounts":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","target_reserve_count",
                                         "historical_recovered_reserve_count","rpc_recovered_reserve_count",
                                         "pending_reserve_count","event_total","unit_complete_event_count",
                                         "still_unmapped_event_count","source_conflict_count","event_conflict_count",
                                         "error_count"]},indent=2))
if classification=="SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if classification!="SAVE0C_UNIT_METADATA_POPULATION_PASS":raise SystemExit(3)
