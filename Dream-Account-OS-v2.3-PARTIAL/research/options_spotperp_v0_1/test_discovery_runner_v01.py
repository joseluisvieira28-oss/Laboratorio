#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import math
import tempfile
import zipfile
from pathlib import Path

import discovery_runner_v01 as d

UTC = dt.timezone.utc


def test_frozen_constants() -> None:
    assert d.LAB_ID == "OPTIONS-SPOTPERP-001"
    assert d.VERSION == "V0.1"
    assert d.START == dt.date(2021, 4, 1)
    assert d.END == dt.date(2024, 12, 31)
    assert (d.MIN_DTE, d.MAX_DTE) == (30, 120)
    assert (d.CALL_MIN, d.CALL_MAX) == (1.05, 1.20)
    assert (d.PUT_MIN, d.PUT_MAX) == (0.80, 0.95)
    assert d.MIN_SIDE == 5
    assert d.MIN_VALID == 500
    assert d.BASE_COST_BPS == 10.0
    assert d.STRESS_COST_BPS == 20.0
    assert d.HAC_LAGS == 7


def test_hac_positive_signal() -> None:
    xs = [(-1.0 + 2.0*i/199.0) for i in range(200)]
    ys = [0.002 + 0.03*x + (0.0007 if i % 2 else -0.0007) for i,x in enumerate(xs)]
    r = d.ols_hac7(xs, ys)
    assert r["n"] == 200
    assert r["hac_lags"] == 7
    assert r["beta"] > 0.029
    assert r["one_sided_p_beta_gt_0"] < 0.10


def test_strategy_costs_and_year_gate_components() -> None:
    rows = []
    for year, gross in [(2021, 30.0), (2022, 25.0), (2023, 20.0), (2024, 5.0)]:
        for i in range(20):
            rows.append({
                "signal_date": dt.date(year, 4 if year == 2021 else 1, 1) + dt.timedelta(days=i),
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
    assert dt.date(2024, 12, 29) + dt.timedelta(days=2) == d.END
    assert dt.date(2024, 12, 30) + dt.timedelta(days=2) > d.END
    assert dt.date(2024, 12, 31) + dt.timedelta(days=1) > d.END


def iter_days(start: dt.date, end: dt.date):
    x = start
    while x <= end:
        yield x
        x += dt.timedelta(days=1)


def iter_months():
    y, m = 2021, 4
    while (y, m) <= (2024, 12):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def build_synthetic_source(root: Path) -> None:
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True)
    days = list(iter_days(d.START, d.END))
    skews: dict[dt.date, float] = {}
    trades: list[dict] = []
    coverage_rows: list[dict] = []
    index_price = 10000.0

    for i, day in enumerate(days):
        sign = 1.0 if i % 2 == 0 else -1.0
        skew = sign * (0.04 + 0.002 * (i % 5))
        skews[day] = skew
        expiry = day + dt.timedelta(days=60)
        exp = expiry.strftime("%d%b%y").upper()
        ts = int(dt.datetime.combine(day, dt.time(12, 0), tzinfo=UTC).timestamp() * 1000)
        call_iv = 0.60 + skew / 2.0
        put_iv = 0.60 - skew / 2.0
        for j, strike in enumerate((10600, 10900, 11200, 11500, 11800)):
            trades.append({
                "timestamp": ts + j,
                "instrument_name": f"BTC-{exp}-{strike}-C",
                "iv": call_iv,
                "index_price": index_price,
            })
        for j, strike in enumerate((8200, 8500, 8800, 9100, 9400)):
            trades.append({
                "timestamp": ts + 100 + j,
                "instrument_name": f"BTC-{exp}-{strike}-P",
                "iv": put_iv,
                "index_price": index_price,
            })
        coverage_rows.append({
            "date": day.isoformat(),
            "distinct_eligible_calls": 5,
            "distinct_eligible_puts": 5,
            "valid_min_5_each_side": True,
        })

    raw_path = raw_dir / "response_000001.json.gz"
    raw_path.write_bytes(gzip.compress(json.dumps({"result": {"trades": trades}}).encode("utf-8")))
    (root / "source_manifest.json").write_text(json.dumps({
        "source_fetch_complete": True,
        "probe_mode": False,
        "holdout_accessed": False,
        "locked_2026_accessed": False,
        "raw_pages": [{"page": raw_path.name, "sha256": d.sha256_file(raw_path)}],
    }), encoding="utf-8")
    (root / "source_gate_calendar_day_daily_coverage.json").write_text(
        json.dumps({"rows": coverage_rows}, sort_keys=True), encoding="utf-8"
    )

    # Synthetic BTC path: for signal t, return from t+1 open to t+2 open
    # is positively related to the frozen skew, plus deterministic noise.
    opens: dict[dt.date, float] = {days[0]: 50000.0}
    idx = {day: i for i, day in enumerate(days)}
    for day in days[1:]:
        prev = day - dt.timedelta(days=1)
        signal_day = day - dt.timedelta(days=2)
        if signal_day >= d.START:
            i = idx[signal_day]
            r = 0.05 * skews[signal_day] + 0.0001 * math.sin(i * 0.71)
        else:
            r = 0.0
        opens[day] = opens[prev] * math.exp(r)

    bdir = root / "raw_binance_btcusdt_1d"
    bdir.mkdir()
    btc_entries = []
    for y, m in iter_months():
        name = f"BTCUSDT-1d-{y:04d}-{m:02d}.zip"
        sio = io.StringIO()
        w = csv.writer(sio, lineterminator="\n")
        for day in days:
            if day.year == y and day.month == m:
                ms = int(dt.datetime.combine(day, dt.time(0, 0), tzinfo=UTC).timestamp() * 1000)
                op = opens[day]
                w.writerow([ms, f"{op:.12f}", f"{op:.12f}", f"{op:.12f}", f"{op:.12f}", "1", ms+86399999, "1", "1", "1", "1", "0"])
        zp = bdir / name
        with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(name.replace(".zip", ".csv"), sio.getvalue().encode("utf-8"))
        btc_entries.append({"file": name, "sha256": d.sha256_file(zp)})
    assert len(btc_entries) == 45

    (root / "source_gate_calendar_day_reconciled_receipt.json").write_text(json.dumps({
        "status": "SOURCE_AUDIT_PASS",
        "authority": {"authority_sha256": d.AUTHORITY_SHA256, "pass": True},
        "skew_values_computed": False,
        "signals_computed": False,
        "forward_returns_computed": False,
        "pnl_computed": False,
        "holdout_2025_accessed": False,
        "year_2026_accessed": False,
        "calendar_day_coverage_audit": {"coverage_pass": True, "valid_signal_coverage_days": len(days)},
        "btc_price_audit": {"exact_discovery_cutoff_verified": True},
        "btc_price_raw_archives": btc_entries,
    }), encoding="utf-8")


def test_end_to_end_synthetic_discovery() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "source"
        output = Path(td) / "out"
        root.mkdir()
        build_synthetic_source(root)
        result = d.run(root, output)
        assert result["evaluable_valid_signal_days"] >= 500
        assert result["regression"]["beta"] > 0
        assert result["regression"]["one_sided_p_beta_gt_0"] <= 0.10
        assert result["base_10bps"]["net_mean_bps_per_trade"] > 0
        assert result["base_10bps"]["profit_factor"] > 1.0
        assert result["years_nonnegative_net_mean_10bps"] >= 3
        assert result["base_10bps"]["single_year_max_share_of_total_positive_gross_pnl"] <= 0.60
        assert result["mve0_pass"] is True
        assert result["classification"] == "MVE0_PASS"
        assert result["holdout_2025_accessed"] is False
        assert result["year_2026_accessed"] is False
        assert (output / "OPTIONS_SPOTPERP_001_DISCOVERY_CLOSEOUT_V01.json").exists()
        assert (output / "OPTIONS_SPOTPERP_001_DISCOVERY_LEDGER_V01.csv").exists()


def main() -> None:
    test_frozen_constants()
    test_hac_positive_signal()
    test_strategy_costs_and_year_gate_components()
    test_receipt_fail_closed()
    test_protected_cutoff_semantics()
    test_end_to_end_synthetic_discovery()
    print("OPTIONS_DISCOVERY_SYNTHETIC_TESTS_PASS")
    print("NO NETWORK / NO REAL MARKET OUTCOMES / NO 2025 / NO 2026")


if __name__ == "__main__":
    main()
