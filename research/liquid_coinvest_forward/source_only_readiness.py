#!/usr/bin/env python3
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBS_DIR = ROOT / "observations"

MONEY_REL_TOL = 1e-12
MONEY_ABS_TOL = 1e-6
BIAS_REL_TOL = 1e-12
BIAS_ABS_TOL = 1e-12

REQUIRED_CLUSTERS = 60
REQUIRED_DATES = 7
REQUIRED_ROWS = 150
REQUIRED_PER_SYMBOL = 40

def parse_iso(s):
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)

def tiers_equal(a, b):
    if len(a) != len(b):
        return False
    def key(t):
        return (
            -1 if t.get("min") is None else int(t["min"]),
            -1 if t.get("max") is None else int(t["max"]),
            str(t.get("size")),
        )
    for x, y in zip(sorted(a, key=key), sorted(b, key=key)):
        if key(x) != key(y):
            return False
        if int(x["position_count"]) != int(y["position_count"]):
            return False
        for f in ("total_position_value","total_position_value_long","value_close_to_liquidation"):
            if not math.isclose(float(x[f]), float(y[f]), rel_tol=MONEY_REL_TOL, abs_tol=MONEY_ABS_TOL):
                return False
        if not math.isclose(float(x["bias"]), float(y["bias"]), rel_tol=BIAS_REL_TOL, abs_tol=BIAS_ABS_TOL):
            return False
    return True

rows=[]
for p in sorted(OBS_DIR.glob("*.json")):
    payload=json.loads(p.read_text(encoding="utf-8"))
    observed=parse_iso(payload["observed_at_utc"])
    for row in payload["observations"]:
        rows.append((observed,row))
rows.sort(key=lambda z:(z[0],z[1]["symbol"],z[1]["observation_id"]))

prev={}
events=[]
conflicts=[]
classes=defaultdict(int)
for observed,row in rows:
    symbol=row["symbol"]
    src=parse_iso(row["source_created_at_utc"])
    tiers=row["tiers"]
    if symbol not in prev:
        cls="BASELINE_ONLY"
    else:
        ps,pt=prev[symbol]
        same=tiers_equal(tiers,pt)
        if src < ps:
            cls="SOURCE_TIMESTAMP_REGRESSION"
            conflicts.append(row["observation_id"])
        elif src == ps and same:
            cls="DUPLICATE_SOURCE_SNAPSHOT"
        elif src > ps and not same:
            cls="EVENT_ELIGIBLE"
        elif src > ps and same:
            cls="SOURCE_TIMESTAMP_ONLY"
        else:
            cls="SOURCE_INTEGRITY_CONFLICT"
            conflicts.append(row["observation_id"])
    classes[cls]+=1
    if cls=="EVENT_ELIGIBLE":
        events.append((observed,row))
    prev[symbol]=(src,tiers)

# Cluster source versions within 5 seconds.
event_times=sorted({parse_iso(r["source_created_at_utc"]) for _,r in events})
clusters=[]
for t in event_times:
    if not clusters or (t-clusters[-1][-1]).total_seconds()>5:
        clusters.append([t])
    else:
        clusters[-1].append(t)

dates={obs.date().isoformat() for obs,_ in events}
per_symbol=defaultdict(int)
distinct_div=defaultdict(set)
for _,r in events:
    per_symbol[r["symbol"]]+=1
    if r.get("cohort_divergence_pp") is not None:
        distinct_div[r["symbol"]].add(float(r["cohort_divergence_pp"]))

overall_div=set().union(*distinct_div.values()) if distinct_div else set()
readiness = (
    len(clusters)>=REQUIRED_CLUSTERS
    and len(dates)>=REQUIRED_DATES
    and len(events)>=REQUIRED_ROWS
    and all(per_symbol[s]>=REQUIRED_PER_SYMBOL for s in ("BTC","ETH","SOL"))
    and not conflicts
)

status = {
    "classification":"SOURCE_ONLY_READINESS",
    "confirmatory_state":"READY_FOR_OUTCOME_COMPLETENESS_CHECK" if readiness else "FORWARD_INSUFFICIENT",
    "receipt_files":len(list(OBS_DIR.glob("*.json"))),
    "total_rows":len(rows),
    "event_eligible_rows":len(events),
    "unique_source_version_clusters":len(clusters),
    "distinct_event_utc_dates":len(dates),
    "event_rows_by_symbol":{s:per_symbol[s] for s in ("BTC","ETH","SOL")},
    "class_counts":dict(sorted(classes.items())),
    "unresolved_integrity_conflicts":conflicts,
    "cohort_divergence_distinct_overall":len(overall_div),
    "cohort_divergence_distinct_by_symbol":{s:len(distinct_div[s]) for s in ("BTC","ETH","SOL")},
    "fixed_gate":{
        "required_source_version_clusters":REQUIRED_CLUSTERS,
        "required_distinct_utc_dates":REQUIRED_DATES,
        "required_event_rows":REQUIRED_ROWS,
        "required_event_rows_per_symbol":REQUIRED_PER_SYMBOL,
    },
    "outcomes_read":False,
}
print(json.dumps(status,indent=2,sort_keys=True))
