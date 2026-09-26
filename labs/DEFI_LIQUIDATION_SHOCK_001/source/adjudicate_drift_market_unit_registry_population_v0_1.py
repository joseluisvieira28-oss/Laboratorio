#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--field-coverage",required=True)
ap.add_argument("--registry",required=True)
args=ap.parse_args()

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_MARKET_UNIT_REGISTRY_POPULATION_RECEIPT_V0.1.json")

def find(root,name):
    for p in Path(root).rglob(name):
        return json.loads(p.read_text())
    return None

f=find(args.field_coverage,"DRIFT_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json")
r=find(args.registry,"DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_RECEIPT_V0.1.json")
errors=[]
if not f:
    errors.append({"reason":"missing_drift_field_enrichment_receipt"})
if not r:
    errors.append({"reason":"missing_historical_registry_receipt"})
if f and f.get("classification")!="DRIFT_FIELD_ENRICHMENT_POPULATION_PASS":
    errors.append({"reason":"field_enrichment_not_pass","classification":f.get("classification")})
if r and r.get("classification")!="DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_SOURCE_PASS":
    errors.append({"reason":"historical_registry_not_pass","classification":r.get("classification")})

spot_obs=sorted(set(int(x) for x in ((f or {}).get("observed_spot_market_indexes") or [])))
perp_obs=sorted(set(int(x) for x in ((f or {}).get("observed_perp_market_indexes") or [])))
spot_reg=(r or {}).get("spot_registry") or {}
perp_reg=(r or {}).get("perp_registry") or {}

unresolved_spot=[]; unresolved_perp=[]; invalid_spot=[]; invalid_perp=[]
for idx in spot_obs:
    ent=spot_reg.get(str(idx))
    if not ent:
        unresolved_spot.append(idx); continue
    if not ent.get("mint") or ent.get("decimals") is None:
        invalid_spot.append({"market_index":idx,"entry":ent})
for idx in perp_obs:
    ent=perp_reg.get(str(idx))
    if not ent:
        unresolved_perp.append(idx); continue
    if int(ent.get("base_precision") or 0)!=1000000000 or int(ent.get("base_precision_exp") or -1)!=9:
        invalid_perp.append({"market_index":idx,"reason":"base_precision_mismatch","entry":ent})
    if int(ent.get("quote_precision") or 0)!=1000000 or int(ent.get("quote_precision_exp") or -1)!=6:
        invalid_perp.append({"market_index":idx,"reason":"quote_precision_mismatch","entry":ent})

if unresolved_spot or unresolved_perp:
    classification="DRIFT_MARKET_UNIT_REGISTRY_PENDING_SOURCE_COMPLETION"
elif errors or invalid_spot or invalid_perp:
    classification="DRIFT_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED"
else:
    classification="DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS"

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "field_enrichment_classification":(f or {}).get("classification"),
 "historical_registry_classification":(r or {}).get("classification"),
 "observed_spot_market_indexes":spot_obs,"observed_perp_market_indexes":perp_obs,
 "observed_spot_market_index_count":len(spot_obs),"observed_perp_market_index_count":len(perp_obs),
 "resolved_spot_market_count":len(spot_obs)-len(unresolved_spot),
 "resolved_perp_market_count":len(perp_obs)-len(unresolved_perp),
 "unresolved_spot_market_indexes":unresolved_spot,
 "unresolved_perp_market_indexes":unresolved_perp,
 "invalid_spot_entries":invalid_spot,"invalid_perp_entries":invalid_perp,
 "error_count":len(errors),"errors":errors,
 "unit_semantics":{
   "spot":"historical source marketIndex -> mint + decimals",
   "perp":"protocol-native base precision 1e9 / quote precision 1e6 + historical source market identity"
 },
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"token_amounts":False,
             "requested_max_amount_values":False,"limit_price_values":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="DRIFT_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
