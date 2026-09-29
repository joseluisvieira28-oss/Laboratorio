#!/usr/bin/env python3
import argparse,hashlib,json
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

TARGET="So11111111111111111111111111111111111111112"
START=datetime.fromisoformat("2025-01-01T00:00:00+00:00")
END=datetime.fromisoformat("2026-01-01T00:00:00+00:00")
PROTOCOLS={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral"
}
MONTHS=[f"{m:02d}" for m in range(1,13)]

def iso(s):return datetime.fromisoformat(str(s).replace("Z","+00:00"))
def month_bounds(mm):
    m=int(mm)
    a=datetime(2025,m,1,tzinfo=timezone.utc)
    b=datetime(2026,1,1,tzinfo=timezone.utc) if m==12 else datetime(2025,m+1,1,tzinfo=timezone.utc)
    return a,b

ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);args=ap.parse_args()
root=Path(args.root);errors=[];selected={};events=[];seen=set()

for proto,cls in PROTOCOLS.items():
    for mm in MONTHS:
        name=f"{proto}-2025{mm}.json"
        hits=sorted(root.rglob(name))
        if len(hits)!=1:
            errors.append({"reason":"partition_receipt_count","protocol":proto,"month":mm,"observed":len(hits),"expected":1})
            continue
        p=hits[0]
        try:r=json.loads(p.read_text())
        except Exception as e:
            errors.append({"reason":"partition_receipt_unreadable","protocol":proto,"month":mm,"error":type(e).__name__})
            continue
        selected[(proto,mm)]=(p,r)
        a,b=month_bounds(mm)
        if r.get("protocol")!=proto or r.get("instruction_class")!=cls:
            errors.append({"reason":"protocol_or_class_mismatch","protocol":proto,"month":mm,
                           "observed_protocol":r.get("protocol"),"observed_class":r.get("instruction_class")})
        if r.get("classification")!="PROTECTED_2025_PROTOCOL_SOURCE_PASS":
            errors.append({"reason":"partition_not_pass","protocol":proto,"month":mm,"classification":r.get("classification")})
        if iso(r.get("window_start"))!=a or iso(r.get("window_end"))!=b:
            errors.append({"reason":"partition_window_mismatch","protocol":proto,"month":mm,
                           "start":r.get("window_start"),"end":r.get("window_end")})
        if int(r.get("duplicate_count") or 0)!=0 or int(r.get("error_count") or 0)!=0:
            errors.append({"reason":"partition_nonzero_errors","protocol":proto,"month":mm,
                           "duplicate_count":r.get("duplicate_count"),"error_count":r.get("error_count")})
        for e in r.get("rows") or []:
            sig=e.get("signature");addr=e.get("instructionAddress")
            key=(proto,sig,json.dumps(addr,separators=(",",":"),sort_keys=True))
            if key in seen:
                errors.append({"reason":"cross_partition_duplicate_identity","protocol":proto,"signature":sig,"instructionAddress":addr})
                continue
            seen.add(key)
            try:t=iso(e.get("timestamp"))
            except Exception:
                errors.append({"reason":"bad_event_timestamp","protocol":proto,"signature":sig});continue
            if not(a<=t<b):
                errors.append({"reason":"event_outside_partition","protocol":proto,"month":mm,"signature":sig,"timestamp":e.get("timestamp")})
                continue
            if e.get("collateral_mint")==TARGET:
                events.append({"protocol":proto,"instruction_class":cls,"signature":sig,
                               "timestamp":e.get("timestamp"),"instructionAddress":addr})

if len(selected)!=48:
    errors.append({"reason":"selected_partition_count","observed":len(selected),"expected":48})

groups=defaultdict(list)
for e in events:groups[(e["protocol"],e["instruction_class"])].append(e)
clusters=[];cross_2026=0
for (proto,cls),items in sorted(groups.items()):
    items.sort(key=lambda e:(e["timestamp"],e["signature"],json.dumps(e["instructionAddress"],separators=(",",":"),sort_keys=True)))
    state=None
    def finish(s):
        nonlocal cross_2026
        last=iso(s["last"])
        t0=last+timedelta(seconds=60)
        if t0>=END:
            cross_2026+=1;return
        raw="|".join(["DEFI-LIQUIDATION-SHOCK-001","cluster-v0.1","60",proto,cls,
                      "mint:"+TARGET,s["first"],s["last"],s["first_signature"],s["last_signature"],str(s["n"])])
        clusters.append({"cluster_id":hashlib.sha256(raw.encode()).hexdigest(),"quiet_seconds":60,
                         "split":"protected_2025","protocol":proto,"instruction_class":cls,
                         "primary_market_identity":"mint:"+TARGET,
                         "first_event_timestamp":s["first"],"last_event_timestamp":s["last"],
                         "t0":t0.isoformat().replace("+00:00","Z"),"event_count":s["n"],
                         "distinct_transaction_signature_count":len(s["signatures"]),
                         "first_signature":s["first_signature"],"last_signature":s["last_signature"],
                         "source_only":True})
    for e in items:
        if state is None:
            state={"first":e["timestamp"],"last":e["timestamp"],"n":1,
                   "first_signature":e["signature"],"last_signature":e["signature"],"signatures":{e["signature"]}}
            continue
        cur=iso(e["timestamp"]);last=iso(state["last"])
        if (cur-last).total_seconds()<=60:
            state["last"]=e["timestamp"];state["n"]+=1;state["last_signature"]=e["signature"];state["signatures"].add(e["signature"])
        else:
            finish(state)
            state={"first":e["timestamp"],"last":e["timestamp"],"n":1,
                   "first_signature":e["signature"],"last_signature":e["signature"],"signatures":{e["signature"]}}
    if state is not None:finish(state)

clusters.sort(key=lambda x:(x["t0"],x["protocol"],x["cluster_id"]))
by_proto=defaultdict(int)
for c in clusters:by_proto[c["protocol"]]+=1
if not clusters:errors.append({"reason":"zero_sol_clusters_2025"})

classification="PROTECTED_2025_SOURCE_AUTHORITY_PASS" if not errors else "PROTECTED_2025_SOURCE_AUTHORITY_BLOCKED"
outdir=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
census=outdir/"PROTECTED_2025_SOURCE_CLUSTER_CENSUS_V0.2.ndjson"
with census.open("w") as f:
    for c in clusters:f.write(json.dumps(c,sort_keys=True,separators=(",",":"))+"\n")
receipt={
 "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "authority_addendum":"PROTECTED_2025_SOURCE_PARTITIONING_ADDENDUM_V0.2.md",
 "partition_count":len(selected),"expected_partition_count":48,
 "partitions":[{"protocol":p,"month":m,"classification":r.get("classification"),
                "successful_instruction_count":r.get("successful_instruction_count"),
                "sol_collateral_event_count":r.get("sol_collateral_event_count")}
               for (p,m),(path,r) in sorted(selected.items())],
 "sol_collateral_event_count":len(events),"sol_cluster_count":len(clusters),
 "clusters_by_protocol":dict(sorted(by_proto.items())),"clusters_crossing_2026_excluded":cross_2026,
 "error_count":len(errors),"errors":errors[:500],
 "cluster_census_sha256":hashlib.sha256(census.read_bytes()).hexdigest(),
 "strategy_translation_freeze":"STRATEGY_TRANSLATION_FREEZE_V0.1.md",
 "execution_cost_freeze":"EXECUTION_COST_FREEZE_V0.1.md",
 "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
             "funding_2025_opened":False,"market_direction_2025_opened":False,
             "prices_2026_opened":False,"returns_2026_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"merge_main":False}}
(outdir/"PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","partition_count","sol_collateral_event_count",
                                        "sol_cluster_count","clusters_by_protocol","clusters_crossing_2026_excluded","error_count"]},indent=2,sort_keys=True))
if classification!="PROTECTED_2025_SOURCE_AUTHORITY_PASS":raise SystemExit(2)
