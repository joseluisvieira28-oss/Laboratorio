#!/usr/bin/env python3
import argparse,hashlib,json
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

TARGET="So11111111111111111111111111111111111111112"
END=datetime.fromisoformat("2026-01-01T00:00:00+00:00")
CLASSES={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral"
}
ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);args=ap.parse_args()
recs=[];errors=[]
for p in sorted(Path(args.root).rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("classification") in ("PROTECTED_2025_PROTOCOL_SOURCE_PASS","PROTECTED_2025_PROTOCOL_SOURCE_BLOCKED"):
        recs.append((p,r))
by={}
for p,r in recs:
    proto=r.get("protocol")
    if proto in by:errors.append({"reason":"duplicate_protocol_receipt","protocol":proto})
    by[proto]=(p,r)
for proto in CLASSES:
    if proto not in by:errors.append({"reason":"missing_protocol_receipt","protocol":proto})
    elif by[proto][1].get("classification")!="PROTECTED_2025_PROTOCOL_SOURCE_PASS":
        errors.append({"reason":"protocol_not_pass","protocol":proto,"classification":by[proto][1].get("classification")})

events=[]
for proto,(p,r) in by.items():
    for e in r.get("rows") or []:
        if e.get("collateral_mint")==TARGET:
            events.append({"protocol":proto,"instruction_class":r["instruction_class"],
                           "signature":e["signature"],"timestamp":e["timestamp"]})

groups=defaultdict(list)
for e in events:groups[(e["protocol"],e["instruction_class"])].append(e)
clusters=[]
cross_2026=[0]
for (proto,cls),items in sorted(groups.items()):
    items.sort(key=lambda e:(e["timestamp"],e["signature"]))
    state=None
    def finish(s):
        last=datetime.fromisoformat(s["last"].replace("Z","+00:00"))
        t0=last+timedelta(seconds=60)
        if t0>=END:
            cross_2026[0]+=1;return
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
        cur=datetime.fromisoformat(e["timestamp"].replace("Z","+00:00"))
        last=datetime.fromisoformat(state["last"].replace("Z","+00:00"))
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
with (outdir/"PROTECTED_2025_SOURCE_CLUSTER_CENSUS_V0.1.ndjson").open("w") as f:
    for c in clusters:f.write(json.dumps(c,sort_keys=True,separators=(",",":"))+"\n")
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "protocol_receipts":[{"protocol":p,"classification":r["classification"],
   "successful_instruction_count":r["successful_instruction_count"],
   "sol_collateral_event_count":r["sol_collateral_event_count"]} for p,(path,r) in sorted(by.items())],
 "sol_collateral_event_count":len(events),"sol_cluster_count":len(clusters),
 "clusters_by_protocol":dict(sorted(by_proto.items())),"clusters_crossing_2026_excluded":cross_2026[0],
 "error_count":len(errors),"errors":errors,
 "strategy_translation_freeze":"STRATEGY_TRANSLATION_FREEZE_V0.1.md",
 "execution_cost_freeze":"EXECUTION_COST_FREEZE_V0.1.md",
 "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
             "funding_2025_opened":False,"market_direction_2025_opened":False,
             "prices_2026_opened":False,"returns_2026_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"merge_main":False}}
(outdir/"PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="PROTECTED_2025_SOURCE_AUTHORITY_PASS":raise SystemExit(2)
