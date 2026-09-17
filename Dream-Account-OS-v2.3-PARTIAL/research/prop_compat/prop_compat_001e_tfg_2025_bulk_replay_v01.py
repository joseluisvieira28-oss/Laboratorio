from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
SYMBOL_IDS = {
    "BTCUSDT": "2fb942154ef44a4ab2ef98c8afb6a4a7",
    "ETHUSDT": "8ed9a7fe648142039edd564d55ac7bb7",
    "SOLUSDT": "2af5f2c57e6847ca8821ea4b6f267cca",
    "BNBUSDT": "7741cc6d9a7f42ffb5b32186691afc01",
    "XRPUSDT": "c9455c17227d429baed64edbcde887f6",
    "DOGEUSDT": "147deee5c2b24355acbe194b13233ec2",
}
BASE_URL = "https://www.mexc.com"
LISTING = BASE_URL + "/file-svc/history/download"
PORTAL = BASE_URL + "/market-data-download"
INTERVAL = "Min15"
FIFTEEN_MS = 900_000
DAY_MS = 86_400_000
UTC_DEC2024_START = int(datetime(2024, 12, 1, tzinfo=timezone.utc).timestamp() * 1000)
OOS_START = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
RIGHT_EDGE_OPEN = int(datetime(2025, 12, 31, tzinfo=timezone.utc).timestamp() * 1000)
OOS_END = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
RAW_HEADER = ("open_time", "open", "high", "low", "close", "volume", "amount", "close_time")
EXPECTED_LEDGER_FP = "e8838e706cc7d1b0538282253d1aff3811182fb138f451a375b6c0ebef6fac9b"
EXPECTED_RECEIPT_FP = "3f70d649a77b2c8f1afd675acef55b75f200cace512417e98e8eae74375184a1"
EXPECTED_BULK_GATE_FP = "a1fb36706125767f7ee647caef615557a03f2bda220a707601aea2499574659b"
EXPECTED_COUNTS = {"BNBUSDT": 9, "BTCUSDT": 7, "DOGEUSDT": 5, "ETHUSDT": 5, "SOLUSDT": 8, "XRPUSDT": 6}
EXPECTED_EXITS = {"STOP": 24, "TARGET": 12, "TIME_EXIT_NEXT_OPEN": 4}
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": PORTAL,
    "User-Agent": "PROP-COMPAT-001E TFG frozen 2025 bulk replay research/1.0",
}


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def request_bytes(url: str, retries: int = 4) -> tuple[bytes, dict[str, str]]:
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read(), {str(k).lower(): str(v) for k, v in resp.headers.items()}
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(1.0 + attempt)
    raise RuntimeError(f"FETCH_FAILED:{url}:{type(last).__name__}:{last}")


def request_json(url: str) -> Any:
    raw, _ = request_bytes(url)
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"JSON_DECODE:{url}:{raw[:160]!r}") from exc


def list_dir(path: str) -> list[Any]:
    url = LISTING + "?" + urllib.parse.urlencode({"filePath": path})
    payload = request_json(url)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise RuntimeError(f"LISTING_SCHEMA:{path}:{type(data).__name__}")
    return data


def pair_prefix(symbol: str) -> str:
    return f"{symbol[:-4]}_USDT"


def resolve_monthly_urls(symbol: str) -> dict[str, str]:
    sid = SYMBOL_IDS[symbol]
    path = f"SPOT2/kline/{sid}/monthly/{INTERVAL}/"
    rows = list_dir(path)
    found: dict[str, str] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        fn = item.get("fileName")
        url = item.get("maskedUrl")
        if isinstance(fn, str) and isinstance(url, str) and url.startswith("http"):
            found[fn] = url
    return found


def parse_raw_csv(raw: bytes, file_name: str, Candle: Any) -> tuple[list[Any], dict[str, Any]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    if tuple(reader.fieldnames or ()) != RAW_HEADER:
        raise RuntimeError(f"HEADER_MISMATCH:{file_name}:{reader.fieldnames}")
    candles: list[Any] = []
    first = last = None
    previous = None
    for row in reader:
        t = int(row["open_time"])
        close_t = int(row["close_time"])
        if t % FIFTEEN_MS != 0:
            raise RuntimeError(f"TIMESTAMP_ALIGNMENT:{file_name}:{t}")
        if close_t != t + FIFTEEN_MS:
            raise RuntimeError(f"RAW_CLOSE_TIME:{file_name}:{t}:{close_t}")
        if previous is not None and t - previous != FIFTEEN_MS:
            raise RuntimeError(f"INTERNAL_GAP:{file_name}:{previous}:{t}")
        values = [float(row[k]) for k in ("open", "high", "low", "close", "volume", "amount")]
        if not all(math.isfinite(v) for v in values):
            raise RuntimeError(f"NONFINITE:{file_name}:{t}")
        o, h, l, c, v, _amount = values
        if min(o, h, l, c) <= 0 or v < 0 or h < max(o, c, l) or l > min(o, c, h):
            raise RuntimeError(f"INVALID_OHLC:{file_name}:{t}")
        candles.append(Candle(t, o, h, l, c, v, close_t - 1))
        first = t if first is None else first
        last = t
        previous = t
    return candles, {
        "rows": len(candles),
        "first_open_time_ms": first,
        "last_open_time_ms": last,
        "sha256": sha256_bytes(raw),
    }


def load_parent_december(parent_root: Path, symbol: str, Candle: Any) -> tuple[list[Any], dict[str, Any]]:
    name = f"{pair_prefix(symbol)}-Min15-2024-12-01.csv"
    hits = sorted(parent_root.rglob(name))
    if len(hits) != 1:
        raise RuntimeError(f"PARENT_DEC_RESOLUTION:{symbol}:hits={len(hits)}")
    raw = hits[0].read_bytes()
    candles, meta = parse_raw_csv(raw, name, Candle)
    return candles, {"file": name, **meta}


def exact_manifest(authority_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    tf = authority_root / "research" / "timeframe_gap"
    amend = json.loads((tf / "TFG_DONCHIAN_1D_001_2025_OOS_BULK15M_SOURCE_AMENDMENT_V0.1D.json").read_text(encoding="utf-8"))
    correction = json.loads((tf / "TFG_DONCHIAN_1D_001_2025_OOS_BULK15M_MANIFEST_CLERICAL_CORRECTION_V0.1.json").read_text(encoding="utf-8"))
    records = list(amend["files"])
    if len(records) != 72:
        raise RuntimeError(f"AUTHORITY_MANIFEST_COUNT:{len(records)}")
    if correction["exact_ordered_72_file_manifest_sha256"] != "c3946f95fa81033d7566fe1114adb8f9c3ab5f076fb690caea2bb19d64762cbf":
        raise RuntimeError("AUTHORITY_ORDERED_MANIFEST_FP")
    return records, amend, correction


def validate_frozen_recovery(prop_root: Path) -> dict[str, Any]:
    p = prop_root / "research" / "prop_compat" / "PROP_COMPAT_001E_TFG_2025_BULK_REPLAY_FREEZE_V0.1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["status"] == "FROZEN_BEFORE_2025_BULK_ACCESS_AND_REPLAY"
    assert d["prerequisite_source_gate"]["receipt_fingerprint"] == EXPECTED_BULK_GATE_FP
    assert d["source"]["required_files"] == 72
    assert d["source"]["months"] == [f"2025-{m:02d}" for m in range(1, 13)]
    assert d["governance"]["2026_historical_outcome_access"] is False
    assert d["governance"]["live_trading"] is False
    assert d["governance"]["orders"] is False
    return d


def economic_targets(base_metrics: dict[str, Any], stress_metrics: dict[str, Any], records: list[Any]) -> tuple[bool, dict[str, Any]]:
    symbol_counts = dict(sorted(Counter(r.symbol for r in records if r.outcome.net_r is not None).items()))
    raw_exits = Counter(r.outcome.exit_reason for r in records if r.outcome.net_r is not None)
    collapsed = Counter()
    for k, v in raw_exits.items():
        if k.startswith("STOP"):
            collapsed["STOP"] += v
        else:
            collapsed[k] += v
    checks = {
        "selected_40": len(records) == 40,
        "resolved_40": int(base_metrics["resolved_trade_count"]) == 40,
        "symbol_counts": symbol_counts == EXPECTED_COUNTS,
        "exit_counts": dict(sorted(collapsed.items())) == EXPECTED_EXITS,
        "base_expectancy": math.isclose(float(base_metrics["net_expectancy_r"]), 0.3510844126, rel_tol=0.0, abs_tol=5e-10),
        "base_pf": math.isclose(float(base_metrics["profit_factor_r"]), 1.5851406877, rel_tol=0.0, abs_tol=5e-10),
        "base_total": math.isclose(float(base_metrics["total_net_r"]), 14.0433765048, rel_tol=0.0, abs_tol=5e-9),
        "stress_expectancy": math.isclose(float(stress_metrics["net_expectancy_r"]), 0.3275204173, rel_tol=0.0, abs_tol=5e-10),
        "stress_pf": math.isclose(float(stress_metrics["profit_factor_r"]), 1.5458673621, rel_tol=0.0, abs_tol=5e-10),
        "stress_total": math.isclose(float(stress_metrics["total_net_r"]), 13.1008166916, rel_tol=0.0, abs_tol=5e-9),
    }
    detail = {
        "checks": checks,
        "symbol_counts": symbol_counts,
        "raw_exit_counts": dict(sorted(raw_exits.items())),
        "collapsed_exit_counts": dict(sorted(collapsed.items())),
        "observed": {
            "selected": len(records),
            "resolved": int(base_metrics["resolved_trade_count"]),
            "base_expectancy_r": base_metrics["net_expectancy_r"],
            "base_profit_factor_r": base_metrics["profit_factor_r"],
            "base_total_r": base_metrics["total_net_r"],
            "stress_expectancy_r": stress_metrics["net_expectancy_r"],
            "stress_profit_factor_r": stress_metrics["profit_factor_r"],
            "stress_total_r": stress_metrics["total_net_r"],
        },
    }
    return all(checks.values()), detail


def run(authority_root: Path, prop_root: Path, parent_root: Path, output_dir: Path) -> int:
    validate_frozen_recovery(prop_root)
    records_manifest, amendment, correction = exact_manifest(authority_root)

    sys.path.insert(0, str(authority_root))
    from research import tfg_donchian_1d_oos_2025_runner_v01b as base
    from research import tfg_donchian_1d_discovery_runner_v01 as parent
    from research import tfg_ema_pullback_1d_discovery_runner_v01 as common

    # Verify code-lineage authority before opening any current 2025 source.
    base.verify_frozen_authority()
    if parent.FROZEN_UNIVERSE != SYMBOLS or parent.MAX_HOLD != 40 or parent.TARGET_R != 3.0:
        raise RuntimeError("AUTHORITY_RULE_CONSTANT_MISMATCH")

    expected_by_file = {str(r["file"]): r for r in records_manifest}
    if len(expected_by_file) != 72:
        raise RuntimeError("MANIFEST_FILENAME_UNIQUENESS")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_audit: list[dict[str, Any]] = []
    candles_2025: dict[str, list[Any]] = {}
    current_hash_match_count = 0
    current_hash_mismatch_count = 0

    # First and only current 2025 source access in this frozen run.
    for symbol in SYMBOLS:
        urls = resolve_monthly_urls(symbol)
        rows: list[Any] = []
        for month in range(1, 13):
            fn = f"{pair_prefix(symbol)}-{INTERVAL}-2025-{month:02d}-01.csv"
            expected = expected_by_file.get(fn)
            if expected is None:
                raise RuntimeError(f"EXPECTED_FILE_ABSENT_FROM_AUTHORITY:{fn}")
            url = urls.get(fn)
            if not url:
                raise RuntimeError(f"CURRENT_BULK_FILE_NOT_FOUND:{fn}")
            raw, headers = request_bytes(url)
            ctype = headers.get("content-type", "")
            if "html" in ctype.lower() or raw.lstrip().lower().startswith(b"<!doctype html"):
                raise RuntimeError(f"NON_CSV_PAYLOAD:{fn}:{ctype}")
            parsed, meta = parse_raw_csv(raw, fn, common.Candle)
            if meta["rows"] != int(expected["rows"]):
                raise RuntimeError(f"ROW_COUNT_MISMATCH:{fn}:{meta['rows']}:{expected['rows']}")
            if meta["first_open_time_ms"] != int(expected["first_open_time_ms"]):
                raise RuntimeError(f"FIRST_TIME_MISMATCH:{fn}:{meta['first_open_time_ms']}:{expected['first_open_time_ms']}")
            if meta["last_open_time_ms"] != int(expected["last_open_time_ms"]):
                raise RuntimeError(f"LAST_TIME_MISMATCH:{fn}:{meta['last_open_time_ms']}:{expected['last_open_time_ms']}")
            sha_match = meta["sha256"] == str(expected.get("sha256"))
            current_hash_match_count += int(sha_match)
            current_hash_mismatch_count += int(not sha_match)
            source_audit.append({
                "symbol": symbol,
                "file": fn,
                "rows": meta["rows"],
                "first_open_time_ms": meta["first_open_time_ms"],
                "last_open_time_ms": meta["last_open_time_ms"],
                "current_sha256": meta["sha256"],
                "committed_amendment_sha_string": expected.get("sha256"),
                "committed_sha_string_match": sha_match,
                "committed_zip_label": expected.get("zip"),
                "masked_url": url,
            })
            rows.extend(parsed)
        if len(rows) != 35040:
            raise RuntimeError(f"SYMBOL_TOTAL_ROWS:{symbol}:{len(rows)}")
        times = [c.open_time for c in rows]
        if len(times) != len(set(times)):
            raise RuntimeError(f"SYMBOL_DUPLICATE_TIMES:{symbol}")
        if any(b - a != FIFTEEN_MS for a, b in zip(times, times[1:])):
            raise RuntimeError(f"SYMBOL_15M_GAP:{symbol}")
        candles_2025[symbol] = rows

    # Build complete UTC daily bars only. No synthetic incomplete 2025-12-31 candle.
    candles_daily: dict[str, list[Any]] = {}
    right_edge_open_by_symbol: dict[str, float] = {}
    source_summary: dict[str, Any] = {}
    for symbol in SYMBOLS:
        parent_dec, parent_meta = load_parent_december(parent_root, symbol, common.Candle)
        current = candles_2025[symbol]
        right_rows = [c for c in current if c.open_time == RIGHT_EDGE_OPEN]
        if len(right_rows) != 1:
            raise RuntimeError(f"RIGHT_EDGE_OPEN_RESOLUTION:{symbol}:{len(right_rows)}")
        right_edge_open_by_symbol[symbol] = float(right_rows[0].open)
        combined = sorted(parent_dec + current, key=lambda c: c.open_time)
        complete_source = [c for c in combined if UTC_DEC2024_START <= c.open_time < RIGHT_EDGE_OPEN]
        expected_15m = (RIGHT_EDGE_OPEN - UTC_DEC2024_START) // FIFTEEN_MS
        if len(complete_source) != expected_15m:
            raise RuntimeError(f"COMPLETE_UTC_SOURCE_COUNT:{symbol}:{len(complete_source)}:{expected_15m}")
        times = [c.open_time for c in complete_source]
        if len(times) != len(set(times)) or any(b - a != FIFTEEN_MS for a, b in zip(times, times[1:])):
            raise RuntimeError(f"COMPLETE_UTC_SOURCE_CONTINUITY:{symbol}")
        daily, dropped = common.aggregate_15m_to_1d(complete_source)
        if dropped != 0:
            raise RuntimeError(f"INCOMPLETE_DAILY_BUCKETS_BEFORE_RIGHT_EDGE:{symbol}:{dropped}")
        common.validate_1d(daily, regular=True)
        if daily[0].open_time != UTC_DEC2024_START or daily[-1].open_time != RIGHT_EDGE_OPEN - DAY_MS:
            raise RuntimeError(f"DAILY_BOUNDARY:{symbol}:{daily[0].open_time}:{daily[-1].open_time}")
        candles_daily[symbol] = daily
        source_summary[symbol] = {
            "parent_december": parent_meta,
            "current_2025_rows": len(current),
            "complete_15m_rows_for_daily": len(complete_source),
            "complete_utc_daily_bars": len(daily),
            "first_daily_open_time": daily[0].open_time,
            "last_complete_daily_open_time": daily[-1].open_time,
            "right_edge_open_time": RIGHT_EDGE_OPEN,
            "right_edge_open_price": right_edge_open_by_symbol[symbol],
        }

    # Reproduce V0.1B frozen signal/execution semantics, with only the pre-frozen
    # V0.1D right-edge open-only time-exit capability added if it is actually needed.
    trade_records: list[Any] = []
    signal_diag: dict[str, Any] = {}
    right_edge_time_exit_uses = 0
    for symbol in SYMBOLS:
        series = candles_daily[symbol]
        signals, _, _ = parent.derive_signals(symbol, series)
        oos_signals = [s for s in signals if OOS_START <= s.entry_open_time < OOS_END]
        eligible = [s for s in oos_signals if s.entry_open_time + parent.MAX_HOLD * DAY_MS < OOS_END]
        active_until: int | None = None
        overlap_skipped = 0
        unresolved = 0
        selected = 0
        for sig in eligible:
            if active_until is not None and sig.entry_open_time <= active_until:
                overlap_skipped += 1
                continue
            outcome = parent.simulate(sig, series, parent.BASE_COST_PCT)
            if outcome.net_r is None:
                desired_exit = sig.entry_open_time + parent.MAX_HOLD * DAY_MS
                if desired_exit == RIGHT_EDGE_OPEN:
                    price = right_edge_open_by_symbol[symbol]
                    cost_fraction = parent.BASE_COST_PCT / 100.0
                    gross = (price - sig.entry) / sig.entry
                    denom = sig.initial_risk_fraction + cost_fraction
                    outcome = parent.Outcome("TIME_EXIT_NEXT_OPEN", RIGHT_EDGE_OPEN, price, parent.MAX_HOLD, gross * 100.0, (gross - cost_fraction) / denom, False)
                    right_edge_time_exit_uses += 1
                else:
                    unresolved += 1
            selected += 1
            trade_records.append(parent.TradeRecord(symbol, sig, outcome))
            active_until = outcome.exit_open_time if outcome.exit_open_time is not None else sig.entry_open_time + parent.MAX_HOLD * DAY_MS
        signal_diag[symbol] = {
            "all_2025_ready_signals": len(oos_signals),
            "full_path_eligible_signals": len(eligible),
            "right_censored_signals": len(oos_signals) - len(eligible),
            "selected_trades": selected,
            "overlap_skipped": overlap_skipped,
            "unresolved_execution_paths": unresolved,
        }
    trade_records.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))

    base_metrics = base.metrics(trade_records)
    stress_metrics = asdict(parent.reprice_stress(trade_records))
    bootstrap = asdict(parent.bootstrap_expectancy(trade_records))
    economic_pass, economic_detail = economic_targets(base_metrics, stress_metrics, trade_records)

    ledger = base.ledger_payload(trade_records)
    ledger_fp_match = ledger["fingerprint"] == EXPECTED_LEDGER_FP
    ledger_path = output_dir / "PROP_COMPAT_001E_TFG_2025_REGENERATED_LEDGER_V0.1.json"
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # A trade-by-trade digest independent of provenance labels, useful if historical
    # ledger JSON provenance serialization changed at V0.1D while economics did not.
    trade_core = [
        {"symbol": r.symbol, "signal": asdict(r.signal), "outcome": asdict(r.outcome), "entry_time_utc": iso(r.signal.entry_open_time)}
        for r in trade_records
    ]
    trade_core_fp = canonical_hash(trade_core)

    if economic_pass:
        classification = "TFG_SEMANTIC_REPRODUCTION_PASS_BYTE_IDENTITY_NOT_RECOVERED"
    else:
        classification = "TFG_RECOVERY_MISMATCH_FAIL_CLOSED"

    receipt: dict[str, Any] = {
        "document_id": "PROP_COMPAT_001E_TFG_2025_BULK_REPLAY_RECEIPT_V0.1",
        "campaign_id": "PROP-COMPAT-001E",
        "setup_id": "TFG-DONCHIAN-1D-001",
        "status": classification,
        "source_family": "OFFICIAL_MEXC_SPOT_HISTORICAL_MARKET_DATA_BULK",
        "authority_branch": "tfg-donchian-1d-oos-2025-v01",
        "authority_bulk_amendment_id": amendment.get("amendment_id"),
        "authority_manifest_correction_id": correction.get("correction_id"),
        "prerequisite_bulk_equivalence_receipt_fingerprint": EXPECTED_BULK_GATE_FP,
        "source_audit": {
            "required_files": 72,
            "resolved_files": len(source_audit),
            "per_symbol_expected_rows": 35040,
            "committed_member_sha_string_matches": current_hash_match_count,
            "committed_member_sha_string_mismatches": current_hash_mismatch_count,
            "member_sha_mismatch_policy": "DIAGNOSTIC_ONLY_DUE_COMMITTED_CLERICAL_CORRECTION",
            "records": source_audit,
            "summary_by_symbol": source_summary,
        },
        "signal_diagnostics": signal_diag,
        "right_edge_open_only_time_exit_uses": right_edge_time_exit_uses,
        "base_metrics": base_metrics,
        "stress_metrics": stress_metrics,
        "bootstrap": bootstrap,
        "economic_verification": economic_detail,
        "economic_reproduction_pass": economic_pass,
        "historical_ledger_fingerprint_target": EXPECTED_LEDGER_FP,
        "regenerated_v01b_lineage_ledger_fingerprint": ledger["fingerprint"],
        "historical_ledger_fingerprint_match": ledger_fp_match,
        "trade_core_fingerprint": trade_core_fp,
        "historical_receipt_fingerprint_target": EXPECTED_RECEIPT_FP,
        "original_three_zip_byte_identity_recovered": False,
        "exact_original_zip_packaging_available": False,
        "2025_data_accessed": True,
        "2025_outcome_evaluation_performed": True,
        "2026_accessed": False,
        "live_trading": False,
        "orders": False,
        "exchange_mutation": False,
        "exchange_authentication": False,
        "wallet_use": False,
        "post_outcome_tuning": False,
        "merge_to_main": False,
    }
    receipt["fingerprint"] = canonical_hash(receipt)
    receipt_path = output_dir / "PROP_COMPAT_001E_TFG_2025_BULK_REPLAY_RECEIPT_V0.1.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    source_manifest_path = output_dir / "PROP_COMPAT_001E_TFG_2025_REACQUIRED_SOURCE_MANIFEST_V0.1.json"
    source_manifest_body = {
        "source_family": receipt["source_family"],
        "records": source_audit,
        "2026_accessed": False,
        "fingerprint": canonical_hash({"source_family": receipt["source_family"], "records": source_audit, "2026_accessed": False}),
    }
    source_manifest_path.write_text(json.dumps(source_manifest_body, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": classification,
        "economic_reproduction_pass": economic_pass,
        "selected": len(trade_records),
        "resolved": base_metrics["resolved_trade_count"],
        "base_expectancy_r": base_metrics["net_expectancy_r"],
        "base_pf": base_metrics["profit_factor_r"],
        "base_total_r": base_metrics["total_net_r"],
        "stress_expectancy_r": stress_metrics["net_expectancy_r"],
        "stress_pf": stress_metrics["profit_factor_r"],
        "stress_total_r": stress_metrics["total_net_r"],
        "exit_counts": economic_detail["collapsed_exit_counts"],
        "symbol_counts": economic_detail["symbol_counts"],
        "right_edge_time_exit_uses": right_edge_time_exit_uses,
        "member_sha_matches": current_hash_match_count,
        "member_sha_mismatches": current_hash_mismatch_count,
        "ledger_fp": ledger["fingerprint"],
        "ledger_fp_match": ledger_fp_match,
        "trade_core_fp": trade_core_fp,
        "receipt_fp": receipt["fingerprint"],
    }, sort_keys=True))
    return 0 if economic_pass else 2


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--authority-root", required=True)
    p.add_argument("--prop-root", required=True)
    p.add_argument("--parent-root", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    return run(Path(args.authority_root), Path(args.prop_root), Path(args.parent_root), Path(args.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
