import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
p = ROOT / "MEV_001_PRE_SOURCE_FREEZE_V01.json"
x = json.loads(p.read_text(encoding="utf-8"))

assert x["lab_id"] == "MACRO-EXPECTATION-VIOLATION-001"
assert x["status"] == "FROZEN_PRE_SOURCE__TARGETS_LOCKED"
assert x["target_policy"]["calendar_year"] == 2027
assert x["target_policy"]["mode"] == "PROSPECTIVE_ONLY"
assert x["target_policy"]["target_observation_open"] is False
assert x["target_policy"]["outcomes_open"] is False
assert x["event_scope"]["decision_clock_seconds"] == 180
assert x["event_scope"]["future_horizon_seconds"] == 900
assert x["source_gate"]["required"] is True
assert x["traditional_reference"]["exact_contract_resolution"] == "UNARMED_PENDING_SOURCE_PASS"
assert x["traditional_reference"]["materiality_rule"] == "UNARMED_PENDING_SOURCE_PASS"

for key in (
    "paid_data_purchase",
    "live_trading",
    "paper_trading",
    "orders",
    "exchange_mutation",
    "wallet_action",
    "render_deployment",
    "main_merge",
    "post_outcome_tuning",
):
    assert x["prohibited"][key] is True, key

assert x["next_authorized_action"] == "SOURCE_FEASIBILITY_ONLY"

print("MEV001_FREEZE_VALIDATION_PASS")
print("TARGETS_LOCKED")
print("OUTCOMES_LOCKED")
print("NO_TRADING_AUTHORITY")
