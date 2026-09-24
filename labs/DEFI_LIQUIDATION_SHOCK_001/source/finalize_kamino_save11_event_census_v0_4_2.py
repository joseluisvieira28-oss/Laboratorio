#!/usr/bin/env python3
import json
from pathlib import Path

base=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
cp=base/"KAMINO_SAVE11_SQD_EVENT_CENSUS_RECEIPT_V0.4.2.json"
rp=base/"KAMINO_SAVE11_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.4.2.json"

c=json.loads(cp.read_text()) if cp.exists() else {}
r=json.loads(rp.read_text()) if rp.exists() else {}

passed=(
    c.get("classification")=="SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE"
    and r.get("classification")=="RAW_SAMPLE_RECONCILIATION_PASS"
)

out={
    "schema_version":"0.4.2",
    "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
    "classification":"KAMINO_SAVE11_EVENT_CENSUS_SOURCE_PASS"
        if passed else "KAMINO_SAVE11_EVENT_CENSUS_BLOCKED_FAIL_CLOSED",
    "census_classification":c.get("classification"),
    "raw_sample_classification":r.get("classification"),
    "protocols":c.get("protocols"),
    "raw_sample_count":r.get("sample_count"),
    "raw_sample_pass_count":r.get("pass_count"),
    "no_economic_outcomes_opened":True,
    "firewall":{
        "prices":False,
        "returns":False,
        "pnl":False,
        "direction":False,
        "economic_outcomes":False,
        "protected_market_outcomes_2025_2026":False,
        "live_trading":False,
        "orders":False,
        "wallets":False,
        "exchange_mutation":False,
        "paid_source":False,
        "account_creation":False,
        "merge_main":False,
    },
}

p=base/"KAMINO_SAVE11_EVENT_CENSUS_FINAL_AUTHORITY_RECEIPT_V0.4.2.json"
p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))

if not passed:
    raise SystemExit(2)
