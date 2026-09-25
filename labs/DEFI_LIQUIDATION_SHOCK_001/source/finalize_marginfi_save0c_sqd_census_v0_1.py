#!/usr/bin/env python3
import json
from pathlib import Path
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
C=BASE/"MARGINFI_SAVE0C_SQD_EVENT_CENSUS_RECEIPT_V0.1.json"
R=BASE/"MARGINFI_SAVE0C_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.1.json"
OUT=BASE/"MARGINFI_SAVE0C_EVENT_CENSUS_FINAL_AUTHORITY_RECEIPT_V0.1.json"
c=json.loads(C.read_text()) if C.exists() else {}
r=json.loads(R.read_text()) if R.exists() else {}
protos=c.get("protocols") or {}
class_ok=all((protos.get(p) or {}).get("successful_instruction_count",0)>0 for p in ("marginfi","save0c"))
passed=(c.get("classification")=="MARGINFI_SAVE0C_SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE"
        and r.get("classification")=="MARGINFI_SAVE0C_RAW_SAMPLE_RECONCILIATION_PASS"
        and class_ok and r.get("sample_count")==r.get("pass_count") and int(r.get("sample_count") or 0)>0)
out={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
     "classification":"MARGINFI_SAVE0C_EVENT_CENSUS_SOURCE_PASS" if passed else "MARGINFI_SAVE0C_EVENT_CENSUS_BLOCKED_FAIL_CLOSED",
     "census_classification":c.get("classification"),"raw_sample_classification":r.get("classification"),
     "both_protocols_observed_successfully":class_ok,"protocols":protos,
     "raw_sample_count":r.get("sample_count"),"raw_sample_pass_count":r.get("pass_count"),
     "no_economic_outcomes_opened":True,
     "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
     "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
if not passed:raise SystemExit(2)
