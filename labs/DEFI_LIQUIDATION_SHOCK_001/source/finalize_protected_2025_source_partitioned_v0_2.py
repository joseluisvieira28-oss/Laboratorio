#!/usr/bin/env python3
import argparse,hashlib,json
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path

TARGET="So11111111111111111111111111111111111111112"
END=datetime.fromisoformat("2026-01-01T00:00:00+00:00")
EXPECTED={
 ("marginfi","2025Q1"):("2025-01-01T00:00:00Z","2025-04-01T00:00:00Z"),
 ("marginfi","2025Q2"):("2025-04-01T00:00:00Z","2025-07-01T00:00:00Z"),
 ("marginfi","2025Q3"):("2025-07-01T00:00:00Z","2025-10-01T00:00:00Z"),
 ("marginfi","2025Q4"):("2025-10-01T00:00:00Z","2026-01-01T00:00:00Z"),
 ("save0c","2025Q1"):("2025-01-01T00:00:00Z","2025-04-01T00:00:00Z"),
 ("save0c","2025Q2"):("2025-04-01T00:00:00Z","2025-07-01T00:00:00Z"),
 ("save0c","2025Q3"):("2025-07-01T00:00:00Z","2025-10-01T00:00:00Z"),
 ("save0c","2025Q4"):("2025-10-01T00:00:00Z","2026-01-01T00:00:00Z"),
 ("kamino","2025Q1"):("2025-01-01T00:00:00Z","2025-04-01T00:00:00Z"),
 ("kamino","2025Q2"):("2025-04-01T00:00:00Z","2025-07-01T00:00:00Z"),
 ("kamino","2025Q3"):("2025-07-01T00:00:00Z","2025-10-01T00:00:00Z"),
 ("kamino","2025Q4"):("2025-10-01T00:00:00Z","2026-01-01T00:00:00Z"),
 ("save11","2025Q1"):("2025-01-01T00:00:00Z","2025-04-01T00:00:00Z"),
 ("save11","2025Q2"):("2025-04-01T00:00:00Z","2025-07-01T00:00:00Z"),
 ("save11","2025Q3"):("2025-07-01T00:00:00Z","2025-10-01T00:00:00Z"),
 ("save11","2025Q4"):("2025-10-01T00:00:00Z","2026-01-01T00:00:00Z"),
}
CLASS={
 "marginfi":"lending_account_liquidate",
 "save0c":"LiquidateObligation",
 "kamino":"liquidate_obligation_and_redeem_reserve_collateral",
 "save11":"LiquidateObligationAndRedeemReserveCollateral"
}
ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);args=ap.parse_args()
errors=[];selected={};all_events=[];seen=set()

for p in sorted(Path(args.root).rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    proto=r.get("protocol")
    if proto not in CLASS or "window_start" not in r or "window_end" not in r:continue
    key=None
    for k,(a,b) in EXPECTED.items():
        if k[0]==proto and r.get("window_start")==a and r.get("window_end")==b:
            key=k;break
    if key is None:
        errors.append({"reason":"unexpected_partition_window","protocol":proto,
                       "window_start":r.get("window_start"),"window_end":r.get("window_end"),"file":str(p)})
        continue
    if key in selected:
        errors.append({"reason":"duplicate_partition_receipt","protocol":key[0],"partition":key[1]})
        continue
    selected[key]=(p,r)

for key,(a,b) in EXPECTED.items():
    if key not in selected:
        errors.append({"reason":"missing_partition_receipt","protocol":key[0],"partition":key[1]})
        continue
    p,r=selected[key]
    if r.get("classification")!="PROTECTED_2025_PROTOCOL_SOURCE_PASS":
        errors.append({"reason":"partition_not_pass","protocol":key[0],"partition":key[1],
                       "classification":r.get("classification")})
    if r.get("error_count") or r.get("duplicate_count"):
        errors.append({"reason":"partition_nonzero_error_or_duplicate","protocol":key[0],"partition":key[1],
                       "error_count":r.get("error_count"),"duplicate_count":r.get("duplicate_count")})
    for e in r.get("rows") or []:
        ident=(key[0],e.get("signature"),json.dumps(e.get("instructionAddress"),sort_keys=True,separators=(",",":")))
        if ident in seen:
            errors.append({"reason":"cross_partition_duplicate_event","protocol":key[0],"signature":e.get("signature")})
            continue
        seen.add(ident)
        if e.get("collateral_mint")==TARGET:
            all_events.append({"protocol":key[0],"instruction_class":CLASS[key[0]],
                               "signature":e["signature"],"timestamp":e["timestamp"]})

def flush(proto,cls,state,clusters):
    last=datetime.fromisoformat(state["last"].replace("Z","+00:00"))
    t0=last+timedelta(seconds=60)
    if t0>=END:return 1
    raw="|".join(["DEFI-LIQUIDATION-SHOCK-001","cluster-v0.1","60",proto,cls,
                  "mint:"+TARGET,state["first"],state["last"],state["first_signature"],
                  state["last_signature"],str(state["n"])])
    clusters.append({"cluster_id":hashlib.sha256(raw.encode()).hexdigest(),"quiet_seconds":60,
                     "split":"protected_2025","protocol":proto,"instruction_class":cls,
                     "primary_market_identity":"mint:"+TARGET,
                     "first_event_timestamp":state["first"],"last_event_timestamp":state["last"],
                     "t0":t0.isoformat().replace("+00:00","Z"),"event_count":state["n"],
                     "distinct_transaction_signature_count":len(state["signatures"]),
                     "first_signature":state["first_signature"],"last_signature":state["last_signature"],
                     "source_only":True})
    return 0

groups=defaultdict(list)
for e in all_events:groups[(e["protocol"],e["instruction_class"])].append(e)
clusters=[];cross=0
for (proto,cls),items in sorted(groups.items()):
    items.sort(key=lambda e:(e["timestamp"],e["signature"]))
    state=None
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
            cross+=flush(proto,cls,state,clusters)
            state={"first":e["timestamp"],"last":e["timestamp"],"n":1,
                   "first_signature":e["signature"],"last_signature":e["signature"],"signatures":{e["signature"]}}
    if state is not None:cross+=flush(proto,cls,state,clusters)

clusters.sort(key=lambda x:(x["t0"],x["protocol"],x["cluster_id"]))
by_proto=defaultdict(int)
for c in clusters:by_proto[c["protocol"]]+=1
if not clusters:errors.append({"reason":"zero_sol_clusters_2025"})
classification="PROTECTED_2025_SOURCE_AUTHORITY_PASS" if not errors else "PROTECTED_2025_SOURCE_AUTHORITY_BLOCKED"
outdir=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
with (outdir/"PROTECTED_2025_SOURCE_CLUSTER_CENSUS_V0.1.ndjson").open("w") as f:
    for c in clusters:f.write(json.dumps(c,sort_keys=True,separators=(",",":"))+"\n")
receipt={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "transport_authority":"DLS_PROTECTED_2025_SOURCE_PARTITIONED_TRANSPORT_ADDENDUM_V0.2.md",
 "partition_receipt_count":len(selected),"expected_partition_receipt_count":16,
 "sol_collateral_event_count":len(all_events),"sol_cluster_count":len(clusters),
 "clusters_by_protocol":dict(sorted(by_proto.items())),"clusters_crossing_2026_excluded":cross,
 "error_count":len(errors),"errors":errors,
 "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
             "funding_2025_opened":False,"market_direction_2025_opened":False,
             "prices_2026_opened":False,"returns_2026_opened":False,
             "post_outcome_tuning":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"merge_main":False}}
(outdir/"PROTECTED_2025_SOURCE_AUTHORITY_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="PROTECTED_2025_SOURCE_AUTHORITY_PASS":raise SystemExit(2)
