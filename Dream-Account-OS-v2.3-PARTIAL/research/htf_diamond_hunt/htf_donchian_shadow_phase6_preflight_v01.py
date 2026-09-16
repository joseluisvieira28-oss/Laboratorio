#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
PARENT_FREEZE = HERE / "HTF_DIAMOND_HUNT_001_PHASE5_FORWARD_HOLDOUT_FREEZE_V0.1.json"
PARENT_CLOSEOUT = HERE / "HTF_DIAMOND_HUNT_001_PHASE5_CLOSEOUT_V0.1.json"
PHASE6_FREEZE = HERE / "HTF_DONCHIAN_SHADOW_001_PHASE6_PREPROD_FREEZE_V0.1.json"
OUT_DIR = HERE / "phase6_preflight_artifacts"
OUT = OUT_DIR / "HTF_DONCHIAN_SHADOW_001_PHASE6_PREFLIGHT_RECEIPT_V0.1.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def require(condition: bool, message: str, failures: list[str]):
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    for path in (PARENT_FREEZE, PARENT_CLOSEOUT, PHASE6_FREEZE):
        require(path.exists(), f"missing_required_file:{path.name}", failures)
    if failures:
        print("PREFLIGHT_FAIL", failures)
        return 2

    pf = load(PARENT_FREEZE)
    pc = load(PARENT_CLOSEOUT)
    p6 = load(PHASE6_FREEZE)

    # Immutable parent scientific state.
    require(pf.get("primary_candidate") == "DH-02-HO1", "parent_primary_changed", failures)
    require(pc.get("scientific_classification") == "NO_RESEARCH_GRADE_PROMOTION", "parent_closeout_rewritten", failures)
    require(pc.get("DH-02-HO1", {}).get("classification") == "EXACT_RULE_FORWARD_HOLDOUT_FAIL", "parent_primary_classification_changed", failures)
    require(pc.get("DH-02-HO1", {}).get("failed_conditions") == ["bootstrap_lower_95_not_positive"], "parent_failure_set_changed", failures)
    require(pc.get("decision", {}).get("live_trading_authorized") is False, "parent_live_trading_flag_changed", failures)
    require(pc.get("decision", {}).get("2026_opened") is False, "parent_2026_state_changed", failures)

    # Exact signal inheritance: no rule rescue.
    parent_cell = next(c for c in pf.get("cells", []) if c.get("cell_id") == "DH-02-HO1")
    s = p6.get("primary_shadow_candidate", {})
    r = parent_cell.get("rule", {})
    require(s.get("cell_id") == "DH-02-HO1", "shadow_primary_not_DH02", failures)
    require(s.get("timeframe") == parent_cell.get("signal_timeframe"), "timeframe_changed", failures)
    require(s.get("direction") == r.get("direction"), "direction_changed", failures)
    require(s.get("donchian_lookback_complete_bars") == r.get("donchian_lookback_complete_bars"), "donchian_lookback_changed", failures)
    require(s.get("atr_length") == r.get("atr_length"), "atr_length_changed", failures)
    require(s.get("entry") == r.get("entry"), "entry_rule_changed", failures)
    require(s.get("stop") == r.get("stop"), "stop_rule_changed", failures)
    require(s.get("target_r") == r.get("target_r"), "target_changed", failures)
    require(s.get("max_hold_bars") == r.get("max_hold_bars"), "max_hold_changed", failures)
    require(s.get("one_active_trade_per_symbol") == r.get("one_active_trade_per_symbol"), "active_trade_rule_changed", failures)
    require(s.get("symbols") == pf.get("dataset", {}).get("symbols"), "symbol_universe_changed", failures)
    require(s.get("base_round_trip_cost_pct") == pf.get("costs", {}).get("base_round_trip_pct"), "base_cost_changed", failures)
    require(s.get("stress_round_trip_cost_pct") == pf.get("costs", {}).get("stress_round_trip_pct"), "stress_cost_changed", failures)

    # Hard production firewall.
    g = p6.get("governance", {})
    x = p6.get("shadow_execution_contract", {})
    d = p6.get("protected_data_gate", {})
    require(g.get("research_only") is True, "research_only_disabled", failures)
    require(g.get("fail_closed") is True, "fail_closed_disabled", failures)
    require(g.get("no_live_trading") is True, "live_trading_not_blocked", failures)
    require(g.get("no_exchange_mutation") is True, "exchange_mutation_not_blocked", failures)
    require(g.get("no_orders") is True, "orders_not_blocked", failures)
    require(g.get("no_alerts_webhooks") is True, "alerts_webhooks_not_blocked", failures)
    require(g.get("no_merge_to_main") is True, "main_merge_not_blocked", failures)
    require(g.get("no_post_outcome_tuning") is True, "post_outcome_tuning_not_blocked", failures)
    require(x.get("mode") == "PAPER_SHADOW_ONLY", "shadow_mode_not_paper_only", failures)
    require(x.get("real_capital_allocation") == 0, "real_capital_nonzero", failures)
    require(x.get("authenticated_exchange_api_allowed") is False, "authenticated_exchange_api_allowed", failures)
    require(x.get("api_keys_allowed") is False, "api_keys_allowed", failures)
    require(x.get("order_submission_allowed") is False, "order_submission_allowed", failures)
    require(x.get("order_cancel_allowed") is False, "order_cancel_allowed", failures)
    require(x.get("position_mutation_allowed") is False, "position_mutation_allowed", failures)
    require(d.get("2025_access_authorized_by_this_freeze") is False, "2025_access_accidentally_authorized", failures)
    require(d.get("2026_access_authorized_by_this_freeze") is False, "2026_access_accidentally_authorized", failures)

    receipt = {
        "experiment_id": "HTF-DONCHIAN-SHADOW-001",
        "phase": "PHASE_6_PREPRODUCTION_SHADOW",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "classification": "PREFLIGHT_PASS" if not failures else "PREFLIGHT_FAIL",
        "failures": failures,
        "market_data_access_performed": False,
        "2025_access_performed": False,
        "2026_access_performed": False,
        "signal_calculation_performed": False,
        "return_calculation_performed": False,
        "live_trading_performed": False,
        "exchange_mutation_performed": False,
        "orders_created": False,
        "files": {
            PARENT_FREEZE.name: sha256(PARENT_FREEZE),
            PARENT_CLOSEOUT.name: sha256(PARENT_CLOSEOUT),
            PHASE6_FREEZE.name: sha256(PHASE6_FREEZE),
        },
        "verified": {
            "historical_phase5_verdict_preserved": not any(x in failures for x in ["parent_closeout_rewritten", "parent_primary_classification_changed", "parent_failure_set_changed"]),
            "DH02_exact_rule_inherited": not any(x.endswith("_changed") or x == "shadow_primary_not_DH02" for x in failures),
            "DH03_rescue_forbidden": p6.get("secondary_family_cell", {}).get("may_rescue_primary") is False,
            "paper_shadow_only": x.get("mode") == "PAPER_SHADOW_ONLY",
            "2026_still_locked": d.get("2026_access_authorized_by_this_freeze") is False,
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not failures else 3


if __name__ == "__main__":
    sys.exit(main())
