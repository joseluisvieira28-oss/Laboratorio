from __future__ import annotations

from typing import Any


def _progress(n: int | None, target: int | None) -> str | None:
    if n is None or target is None:
        return None
    return f"{n}/{target}"


def build_diamond_board(state: dict[str, Any]) -> dict[str, Any]:
    """Read-only governance view over already-existing runtime evidence.

    This function does not fetch market data, calculate new strategy outcomes,
    mutate evidence, change any scientific threshold, or authorize capital.
    """
    options = state.get("options_v21_metrics") or {}
    ced = state.get("ced1d_render_shadow") or {}
    bnb = state.get("bnb_launchpool") or {}
    etf_signal = state.get("etf_cme_signal") or {}
    etf_sched = state.get("etf_cme_exact_scheduler") or {}

    opt_n = int(options.get("resolved_forward_trades") or 0)
    opt_gate = options.get("tier1_forward_gate") or {}
    opt_target = int(opt_gate.get("minimum_resolved_forward_trades") or 50)
    if bool(opt_gate.get("first_50_window_locked")):
        if bool(opt_gate.get("statistical_gate_pass")):
            opt_state = "STATISTICAL_LAYER_PASS__OPERATIONAL_AUDIT_REQUIRED"
        else:
            opt_state = "DIAMOND_TEST_FAIL__NO_RESCUE"
    else:
        opt_state = "COLLECTING__NO_EARLY_VERDICT"

    ced_metrics = ced.get("metrics") or {}
    ced_n_raw = ced_metrics.get("resolved_trade_events")
    ced_n = int(ced_n_raw) if isinstance(ced_n_raw, (int, float)) else 0
    ced_weeks_raw = ced_metrics.get("complete_utc_signal_weeks")
    ced_weeks = int(ced_weeks_raw) if isinstance(ced_weeks_raw, (int, float)) else 0
    ced_routing = ced_metrics.get("routing")
    if ced_routing == "TIER1_ADJUDICATION_ELIGIBLE":
        ced_state = "PROSPECTIVE_GATE_PASS__DIAMOND_RECONCILIATION_ELIGIBLE"
    elif ced_n >= 60 and ced_weeks >= 8:
        ced_state = "PROSPECTIVE_GATE_REACHED__NOT_PASS"
    else:
        ced_state = "COLLECTING"

    etf_state = "Q4_OUTCOMES_SEALED__SOURCE_ONLY"
    if etf_signal.get("source_status") not in (None, "OK"):
        etf_state = "Q4_SOURCE_BLOCKED_FAIL_CLOSED"

    bnb_events = int(bnb.get("eligible_events_visible") or 0)

    return {
        "board_id": "CRYPTO-LAB-DIAMOND-BOARD-V0.1",
        "mode": "READ_ONLY_GOVERNANCE_VIEW",
        "automatic_promotion": False,
        "capital_authority": False,
        "candidates": {
            "OPTIONS-SPOTPERP-001-V2.1": {
                "authority": "OPTIONS-SPOTPERP-001-V2.1-FORWARD-EVIDENCE-GATE-V0.1",
                "state": opt_state,
                "resolved": opt_n,
                "target": opt_target,
                "progress": _progress(opt_n, opt_target),
                "base_mean_bps_descriptive": options.get("base_net_mean_bps"),
                "base_pf_descriptive": options.get("base_profit_factor"),
                "stress_mean_bps_descriptive": options.get("stress_net_mean_bps"),
                "integrity_pass": (options.get("integrity") or {}).get("pass"),
                "verdict_allowed_now": bool(opt_gate.get("first_50_window_locked")),
            },
            "CED1D-0031": {
                "authority": "CED1D_RENDER_SHADOW_ACTIVATION_V0.3 + frozen 60-event/8-week gate",
                "state": ced_state,
                "runtime_status": ced.get("status"),
                "resolved_events": ced_n,
                "minimum_events": 60,
                "complete_weeks": ced_weeks,
                "minimum_complete_weeks": 8,
                "progress_events": _progress(ced_n, 60),
                "progress_weeks": _progress(ced_weeks, 8),
                "cross_venue_support": "FROZEN_SUPPORTING_EVIDENCE_PR32__FOUR_OF_FOUR_SURVIVAL",
                "cross_venue_support_is_independent_time_oos": False,
                "verdict_allowed_now": ced_routing == "TIER1_ADJUDICATION_ELIGIBLE",
            },
            "ETF-CME-INSTFLOW-001": {
                "authority": "ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1A",
                "state": etf_state,
                "source_status": etf_signal.get("source_status"),
                "watcher_status": etf_signal.get("status"),
                "scheduler_status": etf_sched.get("status"),
                "missed_expected_observations": etf_signal.get("missed_expected_observation_count"),
                "minimum_evaluable_observations": 12,
                "outcomes_sealed_until_utc": "2027-01-01T00:00:00Z",
                "interim_pnl_allowed": False,
                "interim_pf_allowed": False,
                "verdict_allowed_now": False,
            },
            "BNB-LAUNCHPOOL-DEMAND-001": {
                "authority": "PARENT_FORWARD_WATCHER_CANONICAL__DIAMOND_V0.2_DRAFT_PR88",
                "state": "WAITING_GENUINELY_PROSPECTIVE_EVENT",
                "runtime_status": bnb.get("status"),
                "eligible_events_visible": bnb_events,
                "diamond_contract_canonical": False,
                "automatic_promotion": False,
                "verdict_allowed_now": False,
            },
        },
        "safety": {
            "authenticated_exchange_api_used": bool(state.get("authenticated_exchange_api_used")),
            "orders_created": bool(state.get("orders_created")),
            "exchange_mutation_performed": bool(state.get("exchange_mutation_performed")),
            "live_capital_enabled": bool(state.get("live_capital_enabled")),
        },
    }
