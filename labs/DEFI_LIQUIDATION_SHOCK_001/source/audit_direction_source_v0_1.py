#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from collections import Counter
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
TARGET="mint:So11111111111111111111111111111111111111112"
EXPECTED={"discovery":5672,"oos":9931}
EXPECTED_TOTAL=15603
EXPECTED_BUILDER_BLOB="0179427f0cef0da0630f8edcc8240056708fd445"
ALLOWED={
 ("marginfi","lending_account_liquidate"):"asset_bank=>collateral_asset",
 ("save0c","LiquidateObligation"):"withdraw_reserve=>collateral_underlying",
 ("kamino","liquidate_obligation_and_redeem_reserve_collateral"):"collateral_underlying",
 ("save11","LiquidateObligationAndRedeemReserveCollateral"):"collateral_underlying",
}
ap=argparse.ArgumentParser()
ap.add_argument("--sample-root",required=True)
ap.add_argument("--builder",required=True)
ap.add_argument("--oos-lock",required=True)
args=ap.parse_args()

errors=[]
lock=json.loads(Path(args.oos_lock).read_text())
if lock.get("classification")!="SURVIVES_OOS":
    errors.append({"reason":"canonical_oos_not_survived","classification":lock.get("classification")})

blob=subprocess.check_output(["git","hash-object",args.builder],text=True).strip()
if blob!=EXPECTED_BUILDER_BLOB:
    errors.append({"reason":"sample_builder_blob_mismatch","observed":blob,"expected":EXPECTED_BUILDER_BLOB})

hits=sorted(Path(args.sample_root).rglob("SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"))
if len(hits)!=1:
    errors.append({"reason":"cluster_census_count","observed":len(hits),"expected":1})
    rows=[]
else:
    rows=[]
    with hits[0].open() as f:
        for line in f:
            if not line.strip():continue
            r=json.loads(line)
            if r.get("primary_market_identity")==TARGET:
                rows.append(r)

by_split=Counter(r.get("split") for r in rows)
by_class=Counter((r.get("split"),r.get("protocol"),r.get("instruction_class")) for r in rows)
unknown=[]
for r in rows:
    k=(r.get("protocol"),r.get("instruction_class"))
    if k not in ALLOWED:
        unknown.append({"cluster_id":r.get("cluster_id"),"split":r.get("split"),"protocol":k[0],"class":k[1]})
if len(rows)!=EXPECTED_TOTAL:
    errors.append({"reason":"target_cluster_total_mismatch","observed":len(rows),"expected":EXPECTED_TOTAL})
for split,n in EXPECTED.items():
    if by_split.get(split,0)!=n:
        errors.append({"reason":"split_count_mismatch","split":split,"observed":by_split.get(split,0),"expected":n})
if unknown:
    errors.append({"reason":"unknown_protocol_or_class","count":len(unknown),"examples":unknown[:20]})
if any(r.get("protocol")=="drift" for r in rows):
    errors.append({"reason":"drift_present_in_sol_collateral_population"})
if any(r.get("source_only") is not True for r in rows):
    errors.append({"reason":"non_source_only_cluster_present"})

classification="DIRECTION_SOURCE_ROLE_AUDIT_PASS" if not errors else "DIRECTION_SOURCE_ROLE_AUDIT_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "canonical_oos_classification":lock.get("classification"),
 "target_market_identity":TARGET,
 "source_role":"LIQUIDATED_COLLATERAL_SOL" if not errors else None,
 "trade_side_directly_observed":False,
 "prospective_hypothesis_authorized":"H_SHORT_COLLATERAL_LIQUIDATION_V0.1" if not errors else None,
 "hypothesis_status":"UNTESTED_ON_PROTECTED_HOLDOUT" if not errors else "BLOCKED",
 "sample_builder_git_blob_sha":blob,
 "target_cluster_count":len(rows),
 "split_counts":dict(sorted(by_split.items())),
 "protocol_class_counts":[
   {"split":k[0],"protocol":k[1],"class":k[2],"count":v,
    "frozen_role_authority":ALLOWED.get((k[1],k[2]))}
   for k,v in sorted(by_class.items())
 ],
 "unknown_protocol_class_count":len(unknown),
 "error_count":len(errors),"errors":errors,
 "semantic_limits":{
   "collateral_role_proven":not errors,
   "liquidator_market_sale_proven":False,
   "venue_sell_flow_proven":False,
   "short_profitability_proven":False
 },
 "firewall":{
   "prices_2025_2026_opened":False,"returns_2025_2026_opened":False,
   "pnl_2025_2026_opened":False,"directional_2025_2026_outcomes_opened":False,
   "post_outcome_tuning":False,"live_trading":False,"orders":False,
   "wallets":False,"exchange_mutation":False,"merge_main":False
 }
}
out=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DIRECTION_SOURCE_AUDIT_RECEIPT_V0.1.json")
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="DIRECTION_SOURCE_ROLE_AUDIT_PASS": raise SystemExit(2)
