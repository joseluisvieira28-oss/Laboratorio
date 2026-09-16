#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from dream_account.models import Candle
from research.phase_b_research_evaluator_v01 import day_block_bootstrap_expectancy
from research.phase_b_signal_formation_v01 import CostAssumptions
from research.tfg_pbr01_4h_v01 import (
    FOUR_H_MS,
    ResearchParameters4H,
    aggregate_15m_to_4h,
    evaluate_universe_4h,
    records_as_dict_4h,
    reprice_fixed_cohort_4h,
)

LAB_ID = "TFG-PBR01-4H-BINANCE-PREPERIOD-001"
AUTHORITY_COMMIT = "bd22cd68765f73f4a644a3bb93515f8f0b406634"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
WINDOW_START = "2021-01-01T00:00:00.000Z"
WINDOW_END = "2023-02-01T00:00:00.000Z"
EXPECTED_ARCHIVES = 150
EXPECTED_MONTHS_PER_SYMBOL = 25
MIN_RESOLVED = 100
BOOTSTRAP_REPS = 5000
BOOTSTRAP_SEED = 230911
BOOTSTRAP_CONFIDENCE = 0.95
FIFTEEN_MIN_MS = 15 * 60 * 1000
REMEDIATION = "DROP_NONSTANDARD_CLOSE_TIME_ROWS_AS_INELIGIBLE_INCOMPLETE_15M_PER_FROZEN_GAP_RULE"
MANIFEST_NAME = "TFG_PBR01_4H_BINANCE_PREPERIOD_SOURCE_MANIFEST_V0.1.json"


def ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp() * 1000)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def base_costs() -> CostAssumptions:
    return CostAssumptions(name="BASE_SENSITIVITY", fee_pct_each_side=0.05, spread_pct=0.05, slippage_pct_each_side=0.025)


def stress_costs() -> CostAssumptions:
    return CostAssumptions(name="STRESS", fee_pct_each_side=0.05, spread_pct=0.10, slippage_pct_each_side=0.05)


def load_manifest(source_root: Path) -> dict:
    p = source_root / MANIFEST_NAME
    if not p.is_file():
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: source manifest missing")
    m = json.loads(p.read_text(encoding="utf-8"))
    if m.get("status") != "SOURCE_AUDIT_PASS":
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: source gate not PASS")
    if m.get("lab_id") != LAB_ID or m.get("authority_commit") != AUTHORITY_COMMIT:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: authority identity mismatch")
    if m.get("technical_remediation") != REMEDIATION:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: remediation identity mismatch")
    if tuple(m.get("symbols", [])) != SYMBOLS:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: universe mismatch")
    if m.get("accepted_archive_count") != EXPECTED_ARCHIVES or m.get("required_archive_count") != EXPECTED_ARCHIVES:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: archive count mismatch")
    if any(int(v) != EXPECTED_MONTHS_PER_SYMBOL for v in m.get("accepted_months_by_symbol", {}).values()):
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: per-symbol month count mismatch")
    if m.get("year_2025_accessed") is not False or m.get("year_2026_accessed") is not False:
        raise RuntimeError("SOURCE_OR_DATA_BLOCKED: protected year flag")
    for k in ("outcomes_computed", "signals_computed", "pnl_computed"):
        if m.get(k) is not False:
            raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: premature outcome flag {k}")
    return m


def load_symbol(source_root: Path, manifest: dict, symbol: str) -> list[Candle]:
    start, end = ms(WINDOW_START), ms(WINDOW_END)
    rows: list[Candle] = []
    entries = sorted((e for e in manifest["archives"] if e["symbol"] == symbol), key=lambda e: e["month"])
    if len(entries) != EXPECTED_MONTHS_PER_SYMBOL:
        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: {symbol} expected {EXPECTED_MONTHS_PER_SYMBOL} archives")
    seen: set[int] = set()
    dropped_incomplete = 0
    for e in entries:
        path = source_root / "raw" / e["file"]
        if not path.is_file() or sha256_path(path) != e["sha256"]:
            raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: archive integrity {symbol} {e['month']}")
        with zipfile.ZipFile(path) as zf:
            members = [n for n in zf.namelist() if not n.endswith("/")]
            if len(members) != 1:
                raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: bad zip members {path.name}")
            with zf.open(members[0]) as fh:
                for row in csv.reader(io.TextIOWrapper(fh, encoding="utf-8")):
                    if not row:
                        continue
                    t = int(row[0])
                    if not (start <= t < end):
                        continue
                    if t % FIFTEEN_MIN_MS != 0:
                        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: unaligned open_time {symbol} {t}")
                    if t in seen:
                        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: duplicate candle {symbol} {t}")
                    seen.add(t)
                    close_t = int(row[6])
                    if close_t != t + FIFTEEN_MIN_MS - 1:
                        dropped_incomplete += 1
                        continue
                    rows.append(Candle(t, float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]), close_t, True))
    expected_drop = int(manifest.get("ineligible_incomplete_15m_rows_by_symbol", {}).get(symbol, -1))
    if dropped_incomplete != expected_drop:
        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: incomplete-row reconciliation {symbol} expected={expected_drop} got={dropped_incomplete}")
    rows.sort(key=lambda c: c.open_time)
    if not rows:
        raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: empty filtered series {symbol}")
    return rows


def classify(base: dict, stress: dict, bootstrap: dict) -> tuple[str, list[str]]:
    resolved = int(base["resolved_trade_count"])
    if resolved < MIN_RESOLVED:
        return "INSUFFICIENT_SAMPLE", ["resolved_trade_count_below_100"]
    failures: list[str] = []
    checks = (
        (base.get("net_expectancy_r"), 0.0, "base_net_expectancy_not_positive"),
        (base.get("profit_factor_r"), 1.0, "base_profit_factor_not_above_1"),
        (bootstrap.get("lower"), 0.0, "bootstrap_lower_95_not_positive"),
        (stress.get("net_expectancy_r"), 0.0, "fixed_cohort_stress_expectancy_not_positive"),
    )
    for value, threshold, reason in checks:
        if value is None or float(value) <= threshold:
            failures.append(reason)
    return ("PREPERIOD_REPLICATED" if not failures else "PREPERIOD_NOT_REPLICATED"), failures


def run(source_root: Path, output: Path) -> int:
    manifest = load_manifest(source_root)
    candles_4h: dict[str, list[Candle]] = {}
    source_counts: dict[str, int] = {}
    derived_counts: dict[str, int] = {}
    incomplete: dict[str, int] = {}
    start, end = ms(WINDOW_START), ms(WINDOW_END)
    expected_last = end - FOUR_H_MS

    for symbol in SYMBOLS:
        c15 = load_symbol(source_root, manifest, symbol)
        source_counts[symbol] = len(c15)
        possible = len({c.open_time - (c.open_time % FOUR_H_MS) for c in c15})
        c4 = aggregate_15m_to_4h(c15)
        if not c4 or c4[0].open_time != start or c4[-1].open_time != expected_last:
            raise RuntimeError(f"SOURCE_OR_DATA_BLOCKED: 4H boundary coverage {symbol}")
        candles_4h[symbol] = c4
        derived_counts[symbol] = len(c4)
        incomplete[symbol] = max(0, possible - len(c4))

    params = ResearchParameters4H()
    params.validate()
    # FIRST BINANCE PRE-PERIOD OUTCOME INSPECTION POINT.
    records, base_obj = evaluate_universe_4h(candles_4h, params, base_costs())
    stress_obj = reprice_fixed_cohort_4h(records, stress_costs(), min_net_rr=params.min_net_rr)
    boot_obj = day_block_bootstrap_expectancy(records, repetitions=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED, confidence=BOOTSTRAP_CONFIDENCE)
    base, stress, bootstrap = asdict(base_obj), asdict(stress_obj), asdict(boot_obj)
    classification, failures = classify(base, stress, bootstrap)

    resolved_values = [float(r.outcome.net_r) for r in records if r.outcome.net_r is not None]
    if resolved_values and abs(mean(resolved_values) - float(base["net_expectancy_r"])) > 1e-12:
        raise RuntimeError("TECHNICAL_FAILURE: expectancy reconciliation mismatch")

    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "TFG_PBR01_4H_BINANCE_PREPERIOD_LEDGER_V0.1.json"
    ledger_path.write_text(json.dumps(records_as_dict_4h(records), indent=2, sort_keys=True), encoding="utf-8")
    closeout = {
        "lab_id": LAB_ID,
        "parent_lab_id": "TFG-PBR01-4H-001",
        "prior_xvenue_lab_id": "TFG-PBR01-4H-XVENUE-BINANCE-001",
        "stage": "NONOVERLAPPING_TEMPORAL_PREPERIOD_REPLICATION",
        "classification": classification,
        "authority_commit": AUTHORITY_COMMIT,
        "source_remediation": REMEDIATION,
        "venue": "BINANCE_SPOT",
        "not_forward_oos": True,
        "nonoverlapping_with_prior_binance_block": True,
        "pooled_with_prior_xvenue_for_classification": False,
        "window": {"start": WINDOW_START, "end_exclusive": WINDOW_END},
        "source_eligible_15m_count_by_symbol": source_counts,
        "source_ineligible_incomplete_15m_rows_by_symbol": manifest["ineligible_incomplete_15m_rows_by_symbol"],
        "derived_4h_count_by_symbol": derived_counts,
        "incomplete_4h_bucket_count_by_symbol": incomplete,
        "base_20bps": base,
        "stress_30bps": stress,
        "bootstrap": bootstrap,
        "failed_conditions": failures,
        "minimum_resolved_trades": MIN_RESOLVED,
        "year_2025_accessed": False,
        "year_2026_accessed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "future_oos_unlocked_automatically": False,
        "interpretation": "Independent non-overlapping historical pre-period robustness evidence only; not a chronological forward OOS and not authorization for live trading.",
    }
    (output / "TFG_PBR01_4H_BINANCE_PREPERIOD_CLOSEOUT_V0.1.json").write_text(json.dumps(closeout, indent=2, sort_keys=True), encoding="utf-8")
    print("CLASSIFICATION=", classification)
    print("RESOLVED=", base["resolved_trade_count"])
    print("BASE_EXPECTANCY_R=", base["net_expectancy_r"])
    print("BASE_PF=", base["profit_factor_r"])
    print("BOOTSTRAP_LOWER95=", bootstrap["lower"])
    print("STRESS_EXPECTANCY_R=", stress["net_expectancy_r"])
    print("2025_ACCESSED=false")
    print("2026_ACCESSED=false")
    print("NO_LIVE_TRADING=true")
    return 0 if classification == "PREPERIOD_REPLICATED" else (5 if classification == "INSUFFICIENT_SAMPLE" else 3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    raise SystemExit(run(Path(args.source_root), Path(args.output)))
