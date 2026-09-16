from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from tfg_ema_pullback_1d_discovery_runner_v01 import (
    BASE_COST_PCT,
    STRESS_COST_PCT,
    FROZEN_UNIVERSE,
    aggregate_15m_to_1d,
    bootstrap_expectancy,
    evaluate_universe,
    load_canonical,
    reprice_stress,
)

LAB_ID = "TFG-EMA-PULLBACK-1D-BINANCE-PREPERIOD-001"
START_MS = 1609459200000
END_MS = 1672531200000
MIN_RESOLVED = 100
ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "TFG_EMA_PULLBACK_1D_BINANCE_PREPERIOD_FREEZE_V0.1.json"


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_and_assert_freeze() -> dict:
    d = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert d["experiment_id"] == LAB_ID
    assert d["status"] == "FROZEN_BEFORE_ANY_REPLICATION_OUTCOME_EVALUATION"
    assert d["replication_type"] == "ROBUSTNESS_REPLICATION_NOT_FORWARD_OOS"
    assert d["independence"]["time_overlap_with_parent"] is False
    assert d["independence"]["pool_with_parent_for_classification"] is False
    assert tuple(d["market"]["symbols"]) == FROZEN_UNIVERSE
    assert d["source_authority"]["source_start_month"] == "2021-01"
    assert d["source_authority"]["source_end_month"] == "2022-12"
    assert d["source_authority"]["2023_access"] is False
    assert d["source_authority"]["2024_access"] is False
    assert d["source_authority"]["2025_access"] is False
    assert d["source_authority"]["2026_access"] is False
    assert d["indicator_definition"]["ema_fast_length"] == 20
    assert d["indicator_definition"]["ema_slow_length"] == 50
    assert d["indicator_definition"]["atr_length"] == 14
    assert d["signal_rules"]["stop"] == "signal_low - 0.25 * ATR14_signal"
    assert d["signal_rules"]["target"] == "entry + 2.0 * (entry - stop)"
    assert d["execution_semantics"]["max_holding_bars"] == 20
    assert d["costs"]["BASE_round_trip_pct"] == BASE_COST_PCT
    assert d["costs"]["STRESS_round_trip_pct"] == STRESS_COST_PCT
    assert d["sample_gate"]["minimum_resolved_trades"] == MIN_RESOLVED
    assert d["sample_gate"]["opportunistic_extension_allowed"] is False
    assert d["sample_gate"]["pooling_with_parent_allowed"] is False
    assert d["governance"]["post_outcome_tuning"] is False
    assert d["governance"]["rescue"] is False
    return d


def classify(base: dict, stress: dict, bootstrap: dict) -> tuple[str, list[str]]:
    failures: list[str] = []
    resolved = int(base["resolved_trade_count"])
    if resolved < MIN_RESOLVED:
        return "INSUFFICIENT_SAMPLE", ["resolved_trade_count_below_100"]
    checks = [
        (base.get("net_expectancy_r"), 0.0, "base_net_expectancy_not_positive"),
        (base.get("profit_factor_r"), 1.0, "base_profit_factor_not_above_1"),
        (bootstrap.get("lower"), 0.0, "bootstrap_lower_95_not_positive"),
        (stress.get("net_expectancy_r"), 0.0, "fixed_cohort_stress_expectancy_not_positive"),
    ]
    for value, threshold, reason in checks:
        if value is None or float(value) <= threshold:
            failures.append(reason)
    return ("REPLICATION_SURVIVES" if not failures else "REPLICATION_FAIL"), failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    freeze = load_and_assert_freeze()
    source_receipt_path = source_dir / "SOURCE_RECEIPT.json"
    source_receipt = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    if source_receipt["classification"] != "SOURCE_READY":
        raise RuntimeError("SOURCE_NOT_READY")
    if source_receipt["accepted_archive_count"] != 144:
        raise RuntimeError("ARCHIVE_COUNT_MISMATCH")
    if any(source_receipt[f"accessed_{y}"] for y in ("2023", "2024", "2025", "2026")):
        raise RuntimeError("PROTECTED_PERIOD_ACCESSED")

    daily_by_symbol = {}
    source_counts = {}
    daily_counts = {}
    incomplete_total = 0
    source_hashes = {}
    for symbol in FROZEN_UNIVERSE:
        p = source_dir / f"{symbol}_15m_2021_2022.csv"
        expected_hash = source_receipt["symbol_receipts"][symbol]["canonical_csv_sha256"]
        observed_hash = sha256_path(p)
        if observed_hash != expected_hash:
            raise RuntimeError(f"SOURCE_HASH_MISMATCH:{symbol}")
        candles = load_canonical(p, START_MS, END_MS)
        source_counts[symbol] = len(candles)
        daily, incomplete = aggregate_15m_to_1d(candles)
        if not daily:
            raise RuntimeError(f"NO_DAILY_DATA:{symbol}")
        if daily[0].open_time != START_MS:
            raise RuntimeError(f"DAILY_START_MISMATCH:{symbol}:{daily[0].open_time}")
        if daily[-1].open_time >= END_MS:
            raise RuntimeError(f"DAILY_END_VIOLATION:{symbol}:{daily[-1].open_time}")
        daily_by_symbol[symbol] = daily
        daily_counts[symbol] = len(daily)
        incomplete_total += incomplete
        source_hashes[symbol] = observed_hash

    # FIRST AND ONLY REAL-MARKET OUTCOME EVALUATION FOR THIS FROZEN REPLICATION.
    records, base_metrics_obj = evaluate_universe(daily_by_symbol)
    stress_obj = reprice_stress(records)
    bootstrap_obj = bootstrap_expectancy(records)
    base = asdict(base_metrics_obj)
    stress = asdict(stress_obj)
    bootstrap = asdict(bootstrap_obj)
    classification, failures = classify(base, stress, bootstrap)

    ledger_path = output_dir / "TFG_EMA_PULLBACK_1D_BINANCE_PREPERIOD_LEDGER_V0.1.csv"
    with ledger_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "symbol", "signal_open_time_ms", "entry_open_time_ms", "entry", "stop", "target",
            "exit_reason", "exit_open_time_ms", "exit_price", "bars_held", "gross_return_pct",
            "base_net_r", "signal_fingerprint"
        ])
        for r in records:
            w.writerow([
                r.symbol, r.signal.signal_open_time, r.signal.entry_open_time, r.signal.entry,
                r.signal.stop, r.signal.target, r.outcome.exit_reason, r.outcome.exit_open_time,
                r.outcome.exit_price, r.outcome.bars_held, r.outcome.gross_return_pct,
                r.outcome.net_r, r.signal.fingerprint,
            ])

    closeout = {
        "lab_id": LAB_ID,
        "stage": "BINANCE_NONOVERLAPPING_PREPERIOD_REPLICATION_V0.1",
        "replication_type": "ROBUSTNESS_REPLICATION_NOT_FORWARD_OOS",
        "classification": classification,
        "failed_conditions": failures,
        "parent_experiment_id": freeze["parent_experiment"]["experiment_id"],
        "parent_terminal_classification": freeze["parent_experiment"]["terminal_classification"],
        "pool_with_parent_for_classification": False,
        "source_provider": "BINANCE_DATA_VISION",
        "market": "SPOT",
        "source_period": "2021-01-01T00:00:00Z/2023-01-01T00:00:00Z",
        "source_counts_15m": source_counts,
        "derived_daily_counts": daily_counts,
        "incomplete_daily_buckets_dropped": incomplete_total,
        "source_csv_sha256": source_hashes,
        "source_receipt_sha256": sha256_path(source_receipt_path),
        "base_metrics": base,
        "fixed_cohort_stress_metrics": stress,
        "bootstrap": bootstrap,
        "minimum_resolved_trades": MIN_RESOLVED,
        "ledger_sha256": sha256_path(ledger_path),
        "protected_period_access": {"2023": False, "2024": False, "2025": False, "2026": False},
        "live_trading": False,
        "exchange_mutation": False,
        "orders": False,
        "alerts_webhooks": False,
        "merge_to_main": False,
        "post_outcome_tuning": False,
        "rescue": False,
        "terminal_stop": True,
        "interpretation": (
            "INSUFFICIENT_SAMPLE is not a formal economic rejection; descriptive economics remain reportable. "
            "REPLICATION_FAIL requires >=100 resolved trades. This replication must not be pooled with the parent "
            "to manufacture the minimum sample gate."
        ),
    }
    payload = json.dumps(closeout, sort_keys=True, indent=2)
    closeout["closeout_sha256_without_self"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    closeout_path = output_dir / "TFG_EMA_PULLBACK_1D_BINANCE_PREPERIOD_CLOSEOUT_V0.1.json"
    closeout_path.write_text(json.dumps(closeout, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "classification": classification,
        "failed_conditions": failures,
        "resolved_trade_count": base["resolved_trade_count"],
        "base_net_expectancy_r": base["net_expectancy_r"],
        "base_profit_factor_r": base["profit_factor_r"],
        "stress_net_expectancy_r": stress["net_expectancy_r"],
        "stress_profit_factor_r": stress["profit_factor_r"],
        "bootstrap_lower_95": bootstrap["lower"],
        "bootstrap_upper_95": bootstrap["upper"],
        "symbol_distribution": base["symbol_distribution"],
        "accessed_2023": False,
        "accessed_2024": False,
        "accessed_2025": False,
        "accessed_2026": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
