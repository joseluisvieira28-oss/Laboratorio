#!/usr/bin/env python3
import json,sys
from collections import Counter
from pathlib import Path
ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"ATM_STRADDLE_BBO_CORPUS_AUTHORITY_V0.8.json").read_text())
IN=Path("artifacts/oeg_atm_straddle_bbo_corpus_v08_inputs")
OUT=Path("artifacts/oeg_atm_straddle_bbo_corpus_v08");OUT.mkdir(parents=True,exist_ok=True)
files=sorted(IN.glob("shard_*.json"))
if len(files)!=AUTH["shard_count"]:raise SystemExit(f"expected {AUTH['shard_count']} shards got {len(files)}")
rows=[];seen=set()
for f in files:
    x=json.loads(f.read_text())
    if x["source_gate_id"]!=AUTH["source_gate_id"]:raise SystemExit("source id mismatch")
    for r in x["rows"]:
        if r["date"] in seen:raise SystemExit("duplicate date")
        seen.add(r["date"]);rows.append(r)
if set(seen)!=set(AUTH["deterministic_dates"]):raise SystemExit("date coverage mismatch")
passed=[r for r in rows if r.get("pass") and not r.get("technical_error")]
tech=[r for r in rows if r.get("technical_error")]
by=Counter(r["date"][:4] for r in passed);g=AUTH["aggregate_gates"]
checks={"total_passing":len(passed)>=g["minimum_passing_dates"],"per_year":all(by[str(y)]>=g["minimum_passing_dates_per_year"] for y in range(2021,2025)),
"years":sum(1 for y in range(2021,2025) if by[str(y)]>0)>=g["minimum_distinct_calendar_years"],"technical_errors":len(tech)<=g["technical_error_dates_maximum"]}
if len(tech)>g["technical_error_dates_maximum"]:cls=AUTH["classifications"]["technical_failure"]
elif all(checks.values()):cls=AUTH["classifications"]["pass"]
else:cls=AUTH["classifications"]["insufficient"]
result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":cls,"total_dates":len(rows),"passing_dates":len(passed),
"passing_dates_by_year":dict(sorted(by.items())),"technical_error_dates":len(tech),"gate_checks":checks,
"bid_ask_values_retained":False,"pnl_opened":False,"returns_opened":False,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
p=OUT/"source_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,indent=2,sort_keys=True))
