#!/usr/bin/env python3
import argparse, base64, json, time, urllib.request
from datetime import datetime
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

def parse_ts(s): return datetime.fromisoformat(str(s).replace("Z","+00:00"))

def find_one(root,names):
    if isinstance(names,str):names=[names]
    for name in names:
        hits=sorted(Path(root).rglob(name))
        if hits:return json.loads(hits[0].read_text())
    return None

def rpc_slice(targets,offset,length,retries=8):
    body={"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
          "params":[targets,{"encoding":"base64","commitment":"finalized",
                            "dataSlice":{"offset":offset,"length":length}}]}
    raw=json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=raw,headers={"Content-Type":"application/json",
        "User-Agent":"crypto-lab-dls-save0c-unit-completion/0.3.1"},method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as resp:
                obj=json.loads(resp.read())
                if obj.get("error"): raise RuntimeError(str(obj["error"]))
                return obj["result"]["value"]
        except Exception as e:
            last=str(e)[:300]; time.sleep(min(30,2**i))
    raise RuntimeError(f"rpc_exhausted:{last}")

ap=argparse.ArgumentParser()
ap.add_argument("--aggregate",required=True)
ap.add_argument("--partitions",required=True)
ap.add_argument("--historical-registry",required=True)
args=ap.parse_args()

agg=find_one(args.aggregate,"SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json")
hist=find_one(args.historical_registry,[
    "SAVE0C_HISTORICAL_RESERVE_REGISTRY_RECEIPT_V0.2.json",
    "SAVE0C_HISTORICAL_RESERVE_REGISTRY_RECEIPT_V0.1.json"])
errors=[];source_conflicts=[]

if not agg:
    errors.append({"reason":"missing_v0_1_aggregate"})
elif agg.get("classification")!="SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE":
    errors.append({"reason":"invalid_trigger_classification","classification":agg.get("classification")})

allowed_hist={"SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS",
              "SAVE0C_HISTORICAL_RESERVE_REGISTRY_PARTIAL_SOURCE_COVERAGE"}
if not hist:
    errors.append({"reason":"missing_historical_registry_receipt"})
elif hist.get("classification") not in allowed_hist:
    errors.append({"reason":"historical_registry_invalid_classification",
                   "classification":hist.get("classification")})

targets=sorted({x["reserve"] for x in (agg or {}).get("unmapped_reserves") or []})
hist_registry=(hist or {}).get("registry") or {}
coverage_end=(hist or {}).get("coverage_end")
coverage_end_dt=parse_ts(coverage_end) if coverage_end else None

# Query calibrated current-state metadata for every target. Historical is bounded and cannot
# silently replace post-retirement evidence.
rpc_registry={};pending=[]

if not errors and targets:
    for i in range(0,len(targets),100):
        chunk=targets[i:i+100]
        a=rpc_slice(chunk,42,33); b=rpc_slice(chunk,227,32)
        for j,reserve in enumerate(chunk):
            ra=a[j] if j<len(a) else None; rb=b[j] if j<len(b) else None
            if ra is None or rb is None:
                pending.append({"reserve":reserve,"reason":"account_missing"}); continue
            if ra.get("owner")!=PROGRAM or rb.get("owner")!=PROGRAM:
                source_conflicts.append({"reserve":reserve,"reason":"owner_mismatch",
                                         "owner_a":ra.get("owner"),"owner_b":rb.get("owner")}); continue
            try:
                da=base64.b64decode((ra.get("data") or [""])[0])
                db=base64.b64decode((rb.get("data") or [""])[0])
            except Exception:
                source_conflicts.append({"reserve":reserve,"reason":"base64_decode_failed"}); continue
            if len(da)!=33 or len(db)!=32:
                source_conflicts.append({"reserve":reserve,"reason":"slice_length_mismatch",
                                         "len_a":len(da),"len_b":len(db)}); continue
            rpc_registry[reserve]={
                "underlying_mint":b58e(da[:32]),
                "underlying_decimals":int(da[32]),
                "collateral_mint":b58e(db),
                "source":"finalized_rpc_dataslice_v0.3.1"
            }

# Independent cross-source comparison wherever both sources exist.
cross_source_compared=0
for reserve in sorted(set(hist_registry)&set(rpc_registry)):
    h=hist_registry[reserve]; q=rpc_registry[reserve]
    hp=(h.get("underlying_mint"),h.get("underlying_decimals"),h.get("collateral_mint"))
    qp=(q.get("underlying_mint"),q.get("underlying_decimals"),q.get("collateral_mint"))
    cross_source_compared+=1
    if hp!=qp:
        source_conflicts.append({"reserve":reserve,"reason":"historical_rpc_identity_conflict",
                                 "historical":{"underlying_mint":hp[0],"underlying_decimals":hp[1],"collateral_mint":hp[2]},
                                 "rpc":{"underlying_mint":qp[0],"underlying_decimals":qp[1],"collateral_mint":qp[2]}})

event_total=0;unit_complete=0;still_unmapped={};event_conflicts=[]
historical_applied=0;rpc_applied=0;partition_count=0

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
        ts=parse_ts(e.get("timestamp"))
        h=hist_registry.get(reserve)
        q=rpc_registry.get(reserve)

        hist_applicable=bool(h) and (
            (hist or {}).get("classification")=="SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS"
            or (coverage_end_dt is not None and ts<coverage_end_dt)
        )

        chosen=None
        if hist_applicable:
            chosen={"underlying_mint":h.get("underlying_mint"),
                    "underlying_decimals":h.get("underlying_decimals"),
                    "collateral_mint":h.get("collateral_mint"),
                    "source":"official_solend_sdk_historical_registry_v0.2"}
            historical_applied+=1
        elif q:
            chosen=q
            rpc_applied+=1

        if not chosen:
            still_unmapped[reserve]=still_unmapped.get(reserve,0)+1
            continue

        if not chosen.get("underlying_mint") or chosen.get("underlying_decimals") is None or not chosen.get("collateral_mint"):
            event_conflicts.append({"signature":e.get("signature"),"reserve":reserve,
                                    "reason":"chosen_metadata_incomplete","source":chosen.get("source")})
            continue

        ctok=e.get("collateral_token") or {}
        if ctok.get("mint")!=chosen["collateral_mint"]:
            event_conflicts.append({"signature":e.get("signature"),"reserve":reserve,
                                    "reason":"recovered_collateral_mint_conflict",
                                    "observed":ctok.get("mint"),"expected":chosen["collateral_mint"],
                                    "source":chosen["source"]})
            continue
        unit_complete+=1

EXPECTED=66628;EXPECTED_PARTITIONS=37
if partition_count!=EXPECTED_PARTITIONS:
    errors.append({"reason":"partition_count_mismatch","observed":partition_count,"expected":EXPECTED_PARTITIONS})
if event_total!=EXPECTED:
    errors.append({"reason":"event_total_mismatch","observed":event_total,"expected":EXPECTED})

if source_conflicts or event_conflicts or errors:
    classification="SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED"
elif still_unmapped or unit_complete!=EXPECTED:
    classification="SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE"
else:
    classification="SAVE0C_UNIT_METADATA_POPULATION_PASS"

combined={}
for reserve,h in hist_registry.items():
    combined.setdefault(reserve,{})["historical"]={
        "underlying_mint":h.get("underlying_mint"),"underlying_decimals":h.get("underlying_decimals"),
        "collateral_mint":h.get("collateral_mint")}
for reserve,q in rpc_registry.items():
    combined.setdefault(reserve,{})["rpc"]=q

receipt={
 "schema_version":"0.3.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "trigger_classification":(agg or {}).get("classification"),
 "historical_registry_classification":(hist or {}).get("classification"),
 "historical_coverage_end":coverage_end,
 "target_reserve_count":len(targets),
 "historical_registry_target_match_count":sum(1 for x in targets if x in hist_registry),
 "rpc_recovered_reserve_count":len(rpc_registry),
 "cross_source_compared_reserve_count":cross_source_compared,
 "pending_reserve_count":len(pending),"pending_reserves":pending,
 "source_conflict_count":len(source_conflicts),"source_conflicts":source_conflicts,
 "partition_count":partition_count,"event_total":event_total,
 "unit_complete_event_count":unit_complete,
 "historical_applied_event_count":historical_applied,
 "rpc_applied_event_count":rpc_applied,
 "still_unmapped_event_count":EXPECTED-unit_complete,
 "unique_still_unmapped_reserve_count":len(still_unmapped),
 "still_unmapped_reserves":[{"reserve":k,"event_count":v}
                            for k,v in sorted(still_unmapped.items(),key=lambda kv:(-kv[1],kv[0]))],
 "event_conflict_count":len(event_conflicts),"event_conflicts":event_conflicts[:100],
 "registry_extension":[{"reserve":k,**(v.get("rpc") or v.get("historical") or {})}
                       for k,v in sorted(combined.items()) if k in targets],
 "error_count":len(errors),"errors":errors,
 "full_reserve_state_requested":False,"economic_amount_fields_decoded":False,
 "oracle_fields_read":False,
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"reserve_amounts":False,"token_amounts":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","target_reserve_count",
                                         "historical_registry_target_match_count","rpc_recovered_reserve_count",
                                         "cross_source_compared_reserve_count","pending_reserve_count",
                                         "event_total","unit_complete_event_count",
                                         "historical_applied_event_count","rpc_applied_event_count",
                                         "still_unmapped_event_count","source_conflict_count",
                                         "event_conflict_count","error_count"]},indent=2))
if classification=="SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if classification!="SAVE0C_UNIT_METADATA_POPULATION_PASS":raise SystemExit(3)
