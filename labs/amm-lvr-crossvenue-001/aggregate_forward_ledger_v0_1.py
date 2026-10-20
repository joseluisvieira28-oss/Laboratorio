from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parent
LEDGER=ROOT/"forward_ledger"
EVID=ROOT/"evidence"
LEDGER.mkdir(parents=True,exist_ok=True)
EVID.mkdir(parents=True,exist_ok=True)

snapshots=[]
for p in sorted(LEDGER.glob("*.json")):
    if p.name=="ROLLUP_V0.1.json":
        continue
    try:
        x=json.loads(p.read_text(encoding="utf-8"))
        if x.get("lab_id")=="AMM-LVR-CROSSVENUE-001" and x.get("snapshot_version")=="V0.1":
            snapshots.append((p,x))
    except Exception:
        pass

tx=set()
swaps=set()
states=set()
dates=set()
source_runs=[]
positive_by_notional_latency={}
for p,x in snapshots:
    pop=x.get("raw_candidate_population",{})
    tx.update(pop.get("transaction_keys",[]) or [])
    swaps.update(pop.get("swap_keys",[]) or [])
    dates.update(pop.get("utc_dates",[]) or [])
    hp=x.get("headroom_population",{})
    states.update(hp.get("state_notional_keys",[]) or [])
    run_id=x.get("github_run_id")
    if run_id:
        source_runs.append(str(run_id))
    for n,latmap in (hp.get("by_notional_latency",{}) or {}).items():
        for lat,m in (latmap or {}).items():
            k=f"{n}|{lat}"
            bucket=positive_by_notional_latency.setdefault(k,{"evaluable_states_sum":0,"positive_headroom_states_sum":0})
            bucket["evaluable_states_sum"]+=int((m or {}).get("evaluable_states") or 0)
            bucket["positive_headroom_states_sum"]+=int((m or {}).get("positive_headroom_states") or 0)

rollup={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "protocol":"FORWARD_ECONOMIC_PROTOCOL_V0.1",
    "rollup_version":"V0.1",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "snapshot_count":len(snapshots),
    "source_run_ids":sorted(set(source_runs)),
    "deduplicated_raw_candidates":{
        "unique_transaction_count":len(tx),
        "unique_swap_key_count":len(swaps),
        "unique_state_notional_key_count":len(states),
        "distinct_utc_dates":sorted(dates),
        "distinct_utc_day_count":len(dates),
    },
    "diagnostic_headroom_accumulator":positive_by_notional_latency,
    "scientific_accounting":{
        "eligible_event_count_claimed":0,
        "discovery_event_credit_claimed":0,
        "minimum_eligible_events":500,
        "minimum_utc_days":14,
        "full_cost_pnl_computed":False,
        "accessibility":"UNPROVEN",
        "scientific_verdict":"NOT_OPEN",
        "raw_candidate_event_horizon_reached":len(tx)>=500 and len(dates)>=14,
        "note":"Counts are deduplicated raw candidate evidence only. The >=500 scientific eligible-event gate is NOT satisfied merely by accumulating 500 raw transactions; full frozen inclusion/cost eligibility must be established first."
    }
}

text=json.dumps(rollup,indent=2,sort_keys=True)
(LEDGER/"ROLLUP_V0.1.json").write_text(text,encoding="utf-8")
(EVID/"forward_ledger_rollup_v0_1.json").write_text(text,encoding="utf-8")
print(json.dumps({
    "snapshot_count":len(snapshots),
    "unique_transactions":len(tx),
    "unique_swaps":len(swaps),
    "distinct_utc_days":len(dates),
    "eligible_event_count_claimed":0,
    "scientific_verdict":"NOT_OPEN"
},indent=2,sort_keys=True))
