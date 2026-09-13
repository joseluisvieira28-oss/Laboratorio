#!/usr/bin/env python3
from __future__ import annotations
import json
import math
import tempfile
from pathlib import Path

import discovery_runner_v01 as d


def test_hac_positive_signal() -> None:
    # Deterministic synthetic relationship with small alternating residuals.
    xs = [(-1.0 + 2.0*i/199.0) for i in range(200)]
    ys = [0.002 + 0.03*x + (0.0007 if i % 2 else -0.0007) for i,x in enumerate(xs)]
    r = d.ols_hac7(xs, ys)
    assert r["n"] == 200
    assert r["hac_lags"] == 7
    assert r["beta"] > 0.029
    assert r["one_sided_p_beta_gt_0"] < 0.10


def test_strategy_costs_and_year_gate_components() -> None:
    rows = []
    # Four years; three profitable after 10 bps, one mildly negative.
    for year, gross in [(2021, 30.0), (2022, 25.0), (2023, 20.0), (2024, 5.0)]:
        for i in range(20):
            rows.append({
                "signal_date": __import__('datetime').date(year, 4 if year == 2021 else 1, 1) + __import__('datetime').timedelta(days=i),
                "position": 1,
                "aligned_gross_bps": gross,
            })
    m = d.strategy_metrics(rows, 10.0)
    assert m["entered_trades"] == 80
    assert m["net_mean_bps_per_trade"] > 0
    assert m["profit_factor"] > 1.0
    assert sum(1 for v in m["annual"].values() if v["net_mean_bps"] >= 0) == 3
    assert 0 <= m["single_year_max_share_of_total_positive_gross_pnl"] <= 1


def test_receipt_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        p = root / "source_gate_calendar_day_reconciled_receipt.json"
        p.write_text(json.dumps({
            "status": "SOURCE_AUDIT_BLOCKED",
            "authority": {"authority_sha256": d.AUTHORITY_SHA256, "pass": True},
            "skew_values_computed": False,
            "signals_computed": False,
            "forward_returns_computed": False,
            "pnl_computed": False,
            "holdout_2025_accessed": False,
            "year_2026_accessed": False,
        }), encoding="utf-8")
        try:
            d.load_and_bind_receipt(root)
        except RuntimeError as exc:
            assert "DISCOVERY_BLOCKED" in str(exc)
        else:
            raise AssertionError("blocked source receipt must not authorize Discovery")


def test_protected_cutoff_semantics() -> None:
    import datetime as dt
    assert d.END == dt.date(2024, 12, 31)
    assert dt.date(2024, 12, 29) + dt.timedelta(days=2) == d.END
    assert dt.date(2024, 12, 30) + dt.timedelta(days=2) > d.END
    assert dt.date(2024, 12, 31) + dt.timedelta(days=1) > d.END


def main() -> None:
    test_hac_positive_signal()
    test_strategy_costs_and_year_gate_components()
    test_receipt_fail_closed()
    test_protected_cutoff_semantics()
    print("OPTIONS_DISCOVERY_SYNTHETIC_TESTS_PASS")
    print("NO MARKET DATA / NO SKEW OUTCOMES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED")


if __name__ == "__main__":
    main()
