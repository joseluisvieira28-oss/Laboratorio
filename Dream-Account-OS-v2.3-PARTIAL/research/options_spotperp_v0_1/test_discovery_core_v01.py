#!/usr/bin/env python3
from datetime import date, timedelta
import math

from discovery_core_v01 import (
    AlignedObservation,
    EligibleTrade,
    align_daily_outcomes,
    construct_daily_signals,
    hac_regression_beta,
    mve0_gate,
    strategy_metrics,
)


def test_instrument_then_side_medians():
    trades = []
    day = "2024-01-01"
    for i, iv in enumerate([60, 62, 64, 66, 68], start=1):
        trades.append(EligibleTrade(day, f"BTC-C{i}", "C", iv))
    trades.append(EligibleTrade(day, "BTC-C1", "C", 80))
    for i, iv in enumerate([50, 52, 54, 56, 58], start=1):
        trades.append(EligibleTrade(day, f"BTC-P{i}", "P", iv))
    s = construct_daily_signals(trades)
    assert len(s) == 1
    assert s[0].call_iv == 66
    assert s[0].put_iv == 54
    assert s[0].skew == 12
    assert s[0].call_instruments == 5
    assert s[0].put_instruments == 5


def test_invalid_under_5x5():
    day = "2024-01-01"
    trades = [EligibleTrade(day, f"C{i}", "C", 60+i) for i in range(4)] + [
        EligibleTrade(day, f"P{i}", "P", 50+i) for i in range(5)
    ]
    assert construct_daily_signals(trades) == []


def test_t_plus_1_t_plus_2_alignment():
    day = "2024-01-01"
    trades = [EligibleTrade(day, f"C{i}", "C", 60+i) for i in range(5)] + [
        EligibleTrade(day, f"P{i}", "P", 50+i) for i in range(5)
    ]
    s = construct_daily_signals(trades)
    px = {"2024-01-02": 100.0, "2024-01-03": 110.0}
    o = align_daily_outcomes(s, px)
    assert len(o) == 1
    assert abs(o[0].forward_log_return - math.log(1.1)) < 1e-15


def test_hac_positive_beta_and_strategy_costs():
    obs = []
    start = date(2021, 4, 1)
    for i in range(40):
        skew = -2.0 + 4.0 * i / 39.0
        ret = 0.002 * skew + (0.00001 if i % 2 else -0.00001)
        d = start + timedelta(days=i)
        obs.append(AlignedObservation(d.isoformat(), skew, ret, d.year))
    reg = hac_regression_beta(obs, 7)
    assert reg["beta"] > 0
    assert reg["one_sided_p_beta_gt_0"] < 0.10
    m10 = strategy_metrics(obs, 10)
    m20 = strategy_metrics(obs, 20)
    assert m10["n_positions"] == 40
    assert m10["net_mean_bps"] > m20["net_mean_bps"]


def test_gate_is_fail_closed_on_sample_and_provenance():
    obs = [AlignedObservation("2024-01-01", 1.0, 0.01, 2024)]
    reg = {"beta": 1.0, "one_sided_p_beta_gt_0": 0.01}
    metrics = {
        "net_mean_bps": 5.0,
        "profit_factor": 2.0,
        "annual_net_mean_bps": {"2021": 1, "2022": 1, "2023": 1, "2024": 1},
        "max_single_year_positive_gross_pnl_share": 0.25,
    }
    g = mve0_gate(obs, reg, metrics, True)
    assert g["mve0_pass"] is False
    assert g["gates"]["A_min_500_valid_signal_days"] is False
    g2 = mve0_gate(obs * 500, reg, metrics, False)
    assert g2["mve0_pass"] is False
    assert g2["gates"]["G_provenance_timestamp_leakage_coverage_pass"] is False


if __name__ == "__main__":
    test_instrument_then_side_medians()
    test_invalid_under_5x5()
    test_t_plus_1_t_plus_2_alignment()
    test_hac_positive_beta_and_strategy_costs()
    test_gate_is_fail_closed_on_sample_and_provenance()
    print("OPTIONS_DISCOVERY_CORE_SYNTHETIC_TESTS_PASS")
    print("NO NETWORK / NO REAL MARKET OUTCOMES / NO 2025 / NO 2026")
