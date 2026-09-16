import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CONTRACT = HERE / "V2_ADJUDICATION_CONTRACT_V01.json"
PROTO = BASE / "FROZEN_PROTOCOL_V01.json"
RESULT = BASE / "evidence" / "BOER_FINAL_RESULT_V01.json"
OUT = HERE / "BOER_V2_ADJUDICATION_RESULT_V01.json"


def profit_factor(values):
    pos = sum(x for x in values if x > 0)
    neg = -sum(x for x in values if x < 0)
    if neg == 0:
        return math.inf if pos > 0 else None
    return pos / neg


def compounded_stats(values):
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in values:
        equity *= (1.0 + r)
        if equity > peak:
            peak = equity
        dd = 1.0 - equity / peak
        if dd > max_dd:
            max_dd = dd
    return equity - 1.0, max_dd


def frozen_bootstrap(values, reps, seed):
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(reps):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    q10_idx = max(0, min(reps - 1, int(math.floor(0.10 * reps))))
    q025_idx = max(0, min(reps - 1, int(math.floor(0.025 * reps))))
    q975_idx = max(0, min(reps - 1, int(math.floor(0.975 * reps)) - 1))
    tail_le_zero = sum(x <= 0 for x in means) / reps
    return {
        "one_sided_90pct_lower_bound": means[q10_idx],
        "two_sided_95pct_ci_recomputed": [means[q025_idx], means[q975_idx]],
        "bootstrap_tail_mass_mean_le_zero": tail_le_zero,
    }


def main():
    c = json.loads(CONTRACT.read_text())
    p = json.loads(PROTO.read_text())
    r = json.loads(RESULT.read_text())

    assert c["governing_policy_id"] == "ND-PROMOTION-POLICY-V2.0-FROZEN-2026-09-14"
    assert c["status"] == "FROZEN_DERIVED_METRICS_ONLY_NO_NEW_MARKET_OUTCOMES"
    assert r["classification"] == c["historical_parent_classification_must_remain"]
    assert r["guards"]["year_2024_price_fields_opened"] is False
    assert r["guards"]["year_2025_market_data_requested"] is False
    assert r["guards"]["year_2026_market_data_requested"] is False
    assert r["guards"]["live_trading"] is False
    assert r["guards"]["exchange_mutation"] is False
    assert p["hard_firewalls"]["no_post_outcome_tuning"] is True
    assert p["hard_firewalls"]["no_event_exclusion_after_outcomes"] is True

    trades = [t for t in r["discovery"]["trades"] if t.get("resolved")]
    assert len(trades) == r["discovery"]["summary"]["resolved_trades"] == 36
    base = [float(t["base_net_return"]) for t in trades]
    gross = [float(t["gross_trade_return"]) for t in trades]
    stress = [float(t["stress_net_return"]) for t in trades]

    # Verify exact frozen reversal direction on every persisted trade.
    direction_consistent = all(
        (t["pre_return"] > 0 and t["direction"] == "SHORT") or
        (t["pre_return"] < 0 and t["direction"] == "LONG")
        for t in trades
    )

    mean_base = sum(base) / len(base)
    mean_gross = sum(gross) / len(gross)
    mean_stress = sum(stress) / len(stress)
    pf = profit_factor(base)
    cumulative_additive = sum(base)
    cumulative_compounded, max_dd = compounded_stats(base)
    positives = [x for x in base if x > 0]
    max_positive_share = max(positives) / sum(positives) if positives else None
    loo_means = [(sum(base) - base[i]) / (len(base) - 1) for i in range(len(base))]
    min_loo = min(loo_means)

    reps = int(c["support_path_1"]["bootstrap_repetitions"])
    seed = int(c["support_path_1"]["bootstrap_seed"])
    boot = frozen_bootstrap(base, reps, seed)

    original_ci = r["discovery"]["summary"]["base_mean_bootstrap_95pct_ci"]
    # Exact reproduction guard for the original primary bootstrap.
    tol = 1e-15
    assert abs(boot["two_sided_95pct_ci_recomputed"][0] - original_ci[0]) <= tol
    assert abs(boot["two_sided_95pct_ci_recomputed"][1] - original_ci[1]) <= tol

    year_means = r["discovery"]["summary"]["calendar_year_base_mean_net_returns"]
    positive_years = sum(float(v) > 0 for v in year_means.values())
    temporal_fraction = positive_years / len(year_means)

    A = (
        r["source_receipt"]["classification"] == "SOURCE_DATA_PASS" and
        r["source_receipt"]["archive_count"] == 48 and
        r["source_receipt"]["qualified_events"] == 48 and
        not r["source_receipt"]["failures"]
    )
    B = (
        p["hard_firewalls"]["no_post_outcome_tuning"] is True and
        p["hard_firewalls"]["no_event_exclusion_after_outcomes"] is True and
        p["strategy"]["threshold_tuning"] == "NONE; every non-zero pre_return event is traded"
    )
    C = len(trades) >= int(p["discovery"]["resolved_trade_floor"])
    D = mean_base > 0 and pf is not None and pf >= 1.0
    E = direction_consistent and mean_gross > 0
    fatal_risk_rule = (max_dd > 0.50 and cumulative_additive < 0.05)
    F = not fatal_risk_rule
    G = (
        len(trades) == 36 and
        r["discovery"]["summary"]["scheduled_events"] == 36 and
        r["discovery"]["summary"]["unresolved_trades"] == 0 and
        r["discovery"]["summary"]["long_trades"] >= p["discovery"]["minimum_long_trades"] and
        r["discovery"]["summary"]["short_trades"] >= p["discovery"]["minimum_short_trades"]
    )

    path1_stat = boot["one_sided_90pct_lower_bound"] > 0
    path1_temporal = temporal_fraction >= 0.50
    path1 = path1_stat and path1_temporal
    hard_all = all([A, B, C, D, E, F, G])

    if hard_all and path1:
        v2_tier = "TIER_2_PROMOTED_CANDIDATE"
        operational_label = "QUASE_DIAMANTE"
    else:
        # Positive usable Discovery without Tier-2 support and without V2 rejection evidence.
        v2_tier = "TIER_3_WATCHLIST_WEAK_CANDIDATE"
        operational_label = "NOT_QUASE_DIAMANTE"

    out = {
        "adjudication_id": c["adjudication_id"],
        "governing_policy_id": c["governing_policy_id"],
        "historical_parent_classification_preserved": r["classification"],
        "v2_classification": v2_tier,
        "operational_label": operational_label,
        "tier2_hard_eligibility": {
            "A_provenance_clean_reproducible": A,
            "B_no_leakage_hindsight_or_post_outcome_selection": B,
            "C_sample_adequate": C,
            "D_base_economics_positive_and_pf_ge_1": D,
            "E_expected_reversal_relationship_correct": E,
            "F_no_fatal_execution_risk_pathology": F,
            "G_not_posthoc_subgroup_selection": G,
            "all_A_to_G": hard_all,
        },
        "support_path_1": {
            "statistical_component_pass": path1_stat,
            "temporal_component_pass": path1_temporal,
            "path_1_pass": path1,
            "one_sided_90pct_bootstrap_lower_bound": boot["one_sided_90pct_lower_bound"],
            "bootstrap_tail_mass_mean_le_zero": boot["bootstrap_tail_mass_mean_le_zero"],
            "positive_calendar_years": positive_years,
            "calendar_year_count": len(year_means),
            "positive_temporal_block_fraction": temporal_fraction,
            "two_sided_95pct_ci_recomputed": boot["two_sided_95pct_ci_recomputed"],
        },
        "derived_metrics_existing_discovery_only": {
            "resolved_trades": len(base),
            "base_mean_net_return": mean_base,
            "base_profit_factor": pf,
            "gross_mean_return": mean_gross,
            "stress_mean_net_return": mean_stress,
            "base_win_rate": r["discovery"]["summary"]["base_win_rate"],
            "base_cumulative_net_additive": cumulative_additive,
            "base_cumulative_net_compounded": cumulative_compounded,
            "base_max_drawdown_compounded": max_dd,
            "max_single_trade_share_of_positive_net": max_positive_share,
            "minimum_leave_one_trade_out_base_mean": min_loo,
            "calendar_year_base_mean_returns": year_means,
        },
        "fragility_flags": {
            "original_95pct_bootstrap_ci_crosses_zero": original_ci[0] <= 0 <= original_ci[1],
            "stress_win_rate_below_50pct": r["discovery"]["summary"]["stress_win_rate"] < 0.50,
            "one_calendar_year_negative": positive_years < len(year_means),
            "leave_one_trade_out_mean_can_turn_nonpositive": min_loo <= 0,
            "single_trade_positive_pnl_share_gt_25pct": (max_positive_share is not None and max_positive_share > 0.25),
        },
        "guards": {
            "new_market_data_accessed": False,
            "year_2024_price_fields_opened": False,
            "year_2025_market_data_requested": False,
            "year_2026_market_data_requested": False,
            "signal_changed": False,
            "costs_changed": False,
            "event_exclusions_added": False,
            "live_trading": False,
            "exchange_mutation": False,
            "orders": False,
            "merge_to_main": False,
            "render_deployment": False,
        },
        "next_action": (
            "TIER_2_REQUIRES_SEPARATE_PROSPECTIVE_NEXT_GATE; 2024 remains unopened"
            if v2_tier == "TIER_2_PROMOTED_CANDIDATE"
            else "TIER_3_ONLY; a new prospectively frozen replication concept would be required before any protected holdout access"
        )
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
