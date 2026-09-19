#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"ATM_STRADDLE_BBO_SOURCE_AUTHORITY_V0.7.json").read_text())
IN=Path("artifacts/oeg_atm_straddle_bbo_source_v07_inputs")
OUT=Path("artifacts/oeg_atm_straddle_bbo_source_v07");OUT.mkdir(parents=True,exist_ok=True)
files=sorted(IN.glob("probe_*.json"))
if len(files)!=4:raise SystemExit(f"expected 4 probes got {len(files)}")
rows=[json.loads(f.read_text()) for f in files]
if sorted(x["date"] for x in rows)!=sorted(AUTH["deterministic_probe_dates"]):raise SystemExit("date mismatch")
tech=sum(bool(x.get("technical_error")) for x in rows);passed=sum(bool(x.get("pass")) for x in rows)
if tech:cls=AUTH["classifications"]["technical_failure"]
elif passed==4:cls=AUTH["classifications"]["pass"]
else:cls=AUTH["classifications"]["insufficient"]
result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":cls,"passing_dates":passed,"technical_error_dates":tech,
"dates":[{"date":x["date"],"pass":x.get("pass"),"selected_expiry":x.get("selected_expiry"),"selected_dte":x.get("selected_dte"),"entry_call_delay_seconds":x.get("entry_call_delay_seconds"),"entry_put_delay_seconds":x.get("entry_put_delay_seconds"),"exit_call_delay_seconds":x.get("exit_call_delay_seconds"),"exit_put_delay_seconds":x.get("exit_put_delay_seconds"),"gate_checks":x.get("gate_checks")} for x in rows],
"bid_ask_values_retained":False,"pnl_opened":False,"returns_opened":False,"open_btc_outcomes":False,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
p=OUT/"source_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))
