#!/usr/bin/env python3
import csv,json,math
from datetime import datetime,timezone
from pathlib import Path

obs=json.load(open("artifacts/discovery/observed_receipt.json"))
observed=float(obs["observed"]["4"]["mean_signed_log_return"])
trig=int(obs["observed"]["4"]["eligible_trigger_count"])
null=[];eligible_counts=[];all_counts=[]
with open("artifacts/discovery/null_stats.csv") as f:
    for r in csv.DictReader(f):
        all_counts.append(int(r["all_independent_triggers"]))
        eligible_counts.append(int(r["eligible_triggers"]))
        try:x=float(r["null_stat"])
        except Exception:continue
        if math.isfinite(x):null.append(x)
valid=len(null)
ge=sum(x>=observed for x in null)
p=(1+ge)/(1+valid)
survives=(trig>=30 and observed>0 and p<=0.05)
receipt={
 "lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001","child_id":"CCLM-CCTP-SETTLED-FLOW-002",
 "stage":"DISCOVERY_V0.1","captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"DISCOVERY_SURVIVES" if survives else "NO_EDGE_DISCOVERY",
 "primary_horizon_hours":4,"independent_trigger_count":trig,
 "observed_mean_signed_4h_relative_log_return":observed,
 "permutations_requested":10000,"valid_null_count":valid,"invalid_null_count":10000-valid,
 "null_ge_observed_count":ge,"one_sided_empirical_p":p,
 "null_mean":sum(null)/valid if valid else None,
 "null_min":min(null) if null else None,"null_max":max(null) if null else None,
 "secondary_descriptive":{h:obs["observed"][h] for h in ("1","12","24")},
 "flow_sha256":obs["flow_sha256"],
 "predictor":{"lookback_hours":720,"minimum_prior_hours":672,"abs_robust_z":3.0,"decluster_hours":6},
 "null":{"seed":20260924,"per_month_circular_shift":True,"rotation":"np.roll(+k)","recompute_predictor":True},
 "oos_opened":False,"holdout_opened":False,"pnl_opened":False,"mutation":False,
 "stop_rule":"If NO_EDGE_DISCOVERY, OOS and protected holdout remain closed."
}
Path("artifacts/discovery/CCLM_002_DISCOVERY_V01_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
