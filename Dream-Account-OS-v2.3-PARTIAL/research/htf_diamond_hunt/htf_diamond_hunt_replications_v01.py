from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

CAMPAIGN_ID = "HTF-DIAMOND-HUNT-001"
HISTORICAL_COMMIT = "62422965b23e91671f6720b818bb26686b9d5bd2"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
FIFTEEN_MIN_MS = 900_000
ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "research" / "htf_diamond_hunt" / "HTF_DIAMOND_HUNT_001_CAMPAIGN_FREEZE_V0.1.json"
BINDING = ROOT / "research" / "htf_diamond_hunt" / "HTF_DIAMOND_HUNT_001_SOURCE_BINDING_V0.1.json"
IMPLEMENTATION = ROOT / "research" / "htf_diamond_hunt" / "HTF_DIAMOND_HUNT_001_IMPLEMENTATION_AUTHORITY_V0.1.json"
OUT_DIR = ROOT / "research" / "local_data" / "htf_diamond_hunt_replications_v01"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_authority(source_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    bind = json.loads(BINDING.read_text(encoding="utf-8"))
    impl = json.loads(IMPLEMENTATION.read_text(encoding="utf-8"))
    assert freeze["campaign_id"] == CAMPAIGN_ID and freeze["status"] == "FROZEN_PRE_OUTCOME"
    assert freeze["execution_order"][:3] == ["DH-01", "DH-04", "DH-07"]
    assert bind["campaign_id"] == CAMPAIGN_ID and bind["status"] == "FROZEN_EXACT_SOURCE_BEFORE_ANY_CAMPAIGN_OUTCOME"
    assert bind["artifact_id"] == 10434938955
    assert bind["artifact_digest"] == "sha256:39fa00e9c3e022b6135f5efdeef0868c1dfb25a80e31331625ace79156212c62"
    assert bind["source_fingerprint"] == "08402ecb8931e42a0766370f55e46adc3de02474ce3a6128f4b2cdd89bb4ac78"
    assert impl["historical_authority_commit"] == HISTORICAL_COMMIT
    receipt_path = source_dir / "HTF_DIAMOND_HUNT_001_SOURCE_GATE_V0.1.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "SOURCE_DATA_PASS"
    assert receipt["source_fingerprint"] == bind["source_fingerprint"]
    assert receipt["monthly_archive_count"] == 144 and receipt["provider_checksum_verified_count"] == 144
    assert receipt["outcome_evaluation_performed"] is False
    assert receipt["market_return_calculation_performed"] is False
    assert receipt["signal_calculation_performed"] is False
    for y in (2023, 2024, 2025, 2026):
        assert receipt[f"access_{y}_performed"] is False
    for symbol in SYMBOLS:
        path = source_dir / "canonical_15m" / f"{symbol}_15m.csv"
        assert path.is_file()
        expected = bind["canonical_15m"][symbol]
        assert sha256_file(path) == expected["sha256"]
        assert expected["complete_count"] == 70013
    return freeze, bind, impl


def load_ema_candles(source_dir: Path, ema_module: Any) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for symbol in SYMBOLS:
        rows: list[Any] = []
        path = source_dir / "canonical_15m" / f"{symbol}_15m.csv"
        with path.open("r", encoding="utf-8", newline="") as h:
            reader = csv.DictReader(h)
            assert tuple(reader.fieldnames or ()) == ("open_time", "open", "high", "low", "close", "volume", "minute_count")
            for row in reader:
                t = int(row["open_time"])
                if int(row["minute_count"]) != 15:
                    raise ValueError(f"non-complete 15m row:{symbol}:{t}")
                rows.append(ema_module.Candle(t, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"]), t + FIFTEEN_MIN_MS - 1))
        result[symbol] = rows
    return result


def load_pbr_candles(source_dir: Path, models_module: Any) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for symbol in SYMBOLS:
        rows: list[Any] = []
        path = source_dir / "canonical_15m" / f"{symbol}_15m.csv"
        with path.open("r", encoding="utf-8", newline="") as h:
            reader = csv.DictReader(h)
            assert tuple(reader.fieldnames or ()) == ("open_time", "open", "high", "low", "close", "volume", "minute_count")
            for row in reader:
                t = int(row["open_time"])
                if int(row["minute_count"]) != 15:
                    raise ValueError(f"non-complete 15m row:{symbol}:{t}")
                rows.append(models_module.Candle(t, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"]), t + FIFTEEN_MIN_MS - 1, True))
        result[symbol] = rows
    return result


def summarize_cell(cell_id: str, base: Any, stress: Any, bootstrap: Any, decision: Any, derived_counts: dict[str, int], incomplete: int) -> dict[str, Any]:
    return {
        "cell_id": cell_id,
        "classification": decision.classification,
        "resolved_trade_count": base.resolved_trade_count,
        "selected_trade_count": base.selected_trade_count,
        "base_net_expectancy_r": base.net_expectancy_r,
        "base_profit_factor_r": base.profit_factor_r,
        "base_win_rate": base.win_rate,
        "base_median_net_r": base.median_net_r,
        "stress_net_expectancy_r": stress.net_expectancy_r,
        "stress_profit_factor_r": stress.profit_factor_r,
        "bootstrap_lower_95": bootstrap.lower,
        "bootstrap_point": bootstrap.point_estimate,
        "bootstrap_upper_95": bootstrap.upper,
        "failed_conditions": list(decision.failed_conditions),
        "derived_bar_count_by_symbol": derived_counts,
        "incomplete_bucket_count": incomplete,
        "symbol_distribution": base.symbol_distribution,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: htf_diamond_hunt_replications_v01.py SOURCE_ARTIFACT_DIR")
    source_dir = Path(argv[1]).resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        freeze, bind, impl = load_authority(source_dir)
        # These modules are materialized byte-exactly from the historical commit by the workflow before this process starts.
        from research import tfg_ema_pullback_1d_discovery_runner_v01 as ema
        from research import tfg_donchian_1d_discovery_runner_v01 as don
        from research import tfg_pbr01_4h_v01 as pbr
        from dream_account import models
        from research.phase_b_signal_formation_v01 import CostAssumptions
        from research.phase_b_research_evaluator_v01 import day_block_bootstrap_expectancy

        source_ema = load_ema_candles(source_dir, ema)
        daily_by_symbol: dict[str, list[Any]] = {}
        daily_counts: dict[str, int] = {}
        incomplete_daily = 0
        for symbol in SYMBOLS:
            daily, inc = ema.aggregate_15m_to_1d(source_ema[symbol])
            daily_by_symbol[symbol] = daily
            daily_counts[symbol] = len(daily)
            incomplete_daily += inc
            if len(daily) < 700:
                raise ValueError(f"unexpected low daily coverage:{symbol}:{len(daily)}")

        # DH-01 — exact historical Donchian implementation, new independent source/period.
        dh01_records, dh01_base = don.evaluate_universe(daily_by_symbol)
        dh01_stress = don.reprice_stress(dh01_records)
        dh01_boot = don.bootstrap_expectancy(dh01_records)
        dh01_decision = don.classify(dh01_base, dh01_stress, dh01_boot)
        dh01 = summarize_cell("DH-01", dh01_base, dh01_stress, dh01_boot, dh01_decision, daily_counts, incomplete_daily)
        print("DH-01", json.dumps(dh01, sort_keys=True), flush=True)

        # DH-04 — exact historical EMA Pullback implementation, same independent source/period.
        dh04_records, dh04_base = ema.evaluate_universe(daily_by_symbol)
        dh04_stress = ema.reprice_stress(dh04_records)
        dh04_boot = ema.bootstrap_expectancy(dh04_records)
        dh04_decision = ema.classify(dh04_base, dh04_stress, dh04_boot)
        dh04 = summarize_cell("DH-04", dh04_base, dh04_stress, dh04_boot, dh04_decision, daily_counts, incomplete_daily)
        print("DH-04", json.dumps(dh04, sort_keys=True), flush=True)

        # DH-07 — exact historical PBR core and exact historical dependency stack.
        source_pbr = load_pbr_candles(source_dir, models)
        bars4h: dict[str, list[Any]] = {}
        counts4h: dict[str, int] = {}
        incomplete4h = 0
        for symbol in SYMBOLS:
            possible = len({c.open_time - (c.open_time % pbr.FOUR_H_MS) for c in source_pbr[symbol]})
            derived = pbr.aggregate_15m_to_4h(source_pbr[symbol])
            bars4h[symbol] = derived
            counts4h[symbol] = len(derived)
            incomplete4h += max(0, possible - len(derived))
            if len(derived) < 4300:
                raise ValueError(f"unexpected low 4H coverage:{symbol}:{len(derived)}")
        params = pbr.ResearchParameters4H()
        params.validate()
        base_costs = CostAssumptions(name="BASE_SENSITIVITY", fee_pct_each_side=0.05, spread_pct=0.05, slippage_pct_each_side=0.025)
        stress_costs = CostAssumptions(name="STRESS", fee_pct_each_side=0.05, spread_pct=0.10, slippage_pct_each_side=0.05)
        dh07_records, dh07_base = pbr.evaluate_universe_4h(bars4h, params, base_costs)
        dh07_stress = pbr.reprice_fixed_cohort_4h(dh07_records, stress_costs, min_net_rr=params.min_net_rr)
        dh07_boot = day_block_bootstrap_expectancy(dh07_records, repetitions=5000, seed=230911, confidence=0.95)
        dh07_decision = pbr.classify_discovery_4h(dh07_base, dh07_stress, dh07_boot)
        dh07 = summarize_cell("DH-07", dh07_base, dh07_stress, dh07_boot, dh07_decision, counts4h, incomplete4h)
        print("DH-07", json.dumps(dh07, sort_keys=True), flush=True)

        receipt = {
            "campaign_id": CAMPAIGN_ID,
            "status": "EXACT_REPLICATION_BLOCK_COMPLETE",
            "source_artifact_id": bind["artifact_id"],
            "source_artifact_digest": bind["artifact_digest"],
            "source_fingerprint": bind["source_fingerprint"],
            "historical_implementation_commit": HISTORICAL_COMMIT,
            "execution_order": ["DH-01", "DH-04", "DH-07"],
            "results": {"DH-01": dh01, "DH-04": dh04, "DH-07": dh07},
            "access_2023_performed": False,
            "access_2024_performed": False,
            "access_2025_performed": False,
            "access_2026_performed": False,
            "network_access_performed_by_runner": False,
            "exchange_mutation_performed": False,
            "live_trading": False,
            "post_outcome_tuning": False
        }
        payload = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        receipt["fingerprint"] = hashlib.sha256(payload).hexdigest()
        (OUT_DIR / "HTF_DIAMOND_HUNT_001_REPLICATION_RECEIPT_V0.1.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        # Preserve exact selected ledgers for independent audit.
        (OUT_DIR / "DH01_LEDGER.json").write_text(json.dumps([asdict(r) for r in dh01_records], indent=2, sort_keys=True), encoding="utf-8")
        (OUT_DIR / "DH04_LEDGER.json").write_text(json.dumps([asdict(r) for r in dh04_records], indent=2, sort_keys=True), encoding="utf-8")
        (OUT_DIR / "DH07_LEDGER.json").write_text(json.dumps(pbr.records_as_dict_4h(dh07_records), indent=2, sort_keys=True), encoding="utf-8")
        return 0
    except Exception as exc:
        blocked = {
            "campaign_id": CAMPAIGN_ID,
            "status": "BLOCKED_PRE_OR_DURING_REPLICATION_EXECUTION",
            "reason": f"{type(exc).__name__}: {exc}",
            "access_2023_performed": False,
            "access_2024_performed": False,
            "access_2025_performed": False,
            "access_2026_performed": False,
            "exchange_mutation_performed": False,
            "live_trading": False,
            "post_outcome_tuning": False
        }
        (OUT_DIR / "HTF_DIAMOND_HUNT_001_REPLICATION_BLOCKED_V0.1.json").write_text(json.dumps(blocked, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(blocked, indent=2, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
