from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from research.news_shock_lab_v01_cpi_nfp_runner import (
    POST_WINDOWS,
    SYMBOLS,
    canonical_hash,
    control_ts_ms,
    event_consensus_rows,
    event_metrics,
    event_ts_ms,
    load_manifest,
    parse_day,
    summarize_group,
)
from research.news_shock_lab_v02_metadata_preflight import (
    EXPECTED_FREEZE_FINGERPRINT,
    EXPECTED_MANIFEST_FINGERPRINT,
    MIN_VALID_CONTROLS,
    candidate_control_dates,
    required_days,
)

PREFLIGHT_DOCUMENT_TYPE = "NEWS_SHOCK_LAB_V02_METADATA_PREFLIGHT_RECEIPT"


def load_preflight(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    if canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.2 preflight fingerprint mismatch")
    if raw.get("document_type") != PREFLIGHT_DOCUMENT_TYPE:
        raise PermissionError("V0.2 preflight document type mismatch")
    if raw.get("status") != "PASS_METADATA_PREFLIGHT":
        raise PermissionError("V0.2 preflight did not pass")
    if raw.get("freeze_fingerprint") != EXPECTED_FREEZE_FINGERPRINT:
        raise PermissionError("V0.2 preflight freeze binding mismatch")
    if raw.get("schedule_manifest_fingerprint") != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("V0.2 preflight manifest binding mismatch")
    boundary = raw.get("inspection_boundary", {})
    expected_false = (
        "prices_inspected",
        "returns_computed",
        "volume_inspected",
        "trade_count_inspected",
        "taker_flow_inspected",
        "outcomes_evaluated",
    )
    if boundary.get("timestamps_inspected") is not True or boundary.get("checksums_inspected") is not True:
        raise PermissionError("V0.2 preflight timestamp/checksum boundary mismatch")
    if any(boundary.get(k) is not False for k in expected_false):
        raise PermissionError("V0.2 preflight outcome boundary drift")
    if int(raw.get("minimum_valid_control_count_observed", -1)) < MIN_VALID_CONTROLS:
        raise PermissionError("V0.2 preflight minimum-control mismatch")
    return raw


def run(raw_root: Path, manifest_path: Path, preflight_path: Path, output_path: Path) -> dict:
    manifest = load_manifest(manifest_path)
    if manifest.get("fingerprint") != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("unexpected manifest fingerprint")
    preflight = load_preflight(preflight_path)
    days = required_days(manifest)
    if any(day.startswith("2026-") for day in days):
        raise PermissionError("2026 required-day guard violation")

    control_map: dict[tuple[str, str, str], list[str]] = {}
    for row in preflight["per_event_symbol"]:
        key = (row["symbol"], row["event_type"], row["event_date"])
        controls = list(row["valid_controls"])
        if len(controls) < MIN_VALID_CONTROLS:
            raise PermissionError(f"preflight control map inadequate: {key}")
        control_map[key] = controls

    cache: dict[str, dict[str, dict]] = {s: {} for s in SYMBOLS}
    for symbol in SYMBOLS:
        for day in days:
            cache[symbol][day] = parse_day(raw_root, symbol, day)

    rows: list[dict] = []
    event_dates = {e["event_date"] for e in manifest["events"]}
    for symbol in SYMBOLS:
        for event in manifest["events"]:
            event_date = event["event_date"]
            key = (symbol, event["event_type"], event_date)
            valid_controls = control_map.get(key)
            if valid_controls is None:
                raise RuntimeError(f"preflight mapping missing {key}")

            # Event-day gaps remain fatal; metadata preflight already proved coverage.
            metrics = event_metrics(cache[symbol][event_date], event_ts_ms(event_date))
            controls: list[dict] = []
            candidate_days = {
                d.isoformat() for d in candidate_control_dates(event_date, event_dates)
            }
            if not set(valid_controls).issubset(candidate_days):
                raise PermissionError(f"preflight control date outside frozen candidate pool: {key}")
            for day in valid_controls:
                from datetime import date
                cdate = date.fromisoformat(day)
                controls.append(event_metrics(cache[symbol][day], control_ts_ms(cdate)))

            if len(controls) < MIN_VALID_CONTROLS:
                raise RuntimeError(f"valid control count drift after preflight: {key}")

            row = {
                "symbol": symbol,
                "event_type": event["event_type"],
                "event_date": event_date,
                "release_utc": event["release_utc"],
                "control_count": len(controls),
                "control_dates": valid_controls,
            }
            row.update(metrics)
            for horizon in POST_WINDOWS:
                control_volume = mean(float(c[f"volume_{horizon}m"]) for c in controls)
                control_trades = mean(float(c[f"trades_{horizon}m"]) for c in controls)
                row[f"volume_ratio_{horizon}m"] = (
                    float(metrics[f"volume_{horizon}m"]) / control_volume
                    if control_volume > 0 else None
                )
                row[f"trade_ratio_{horizon}m"] = (
                    float(metrics[f"trades_{horizon}m"]) / control_trades
                    if control_trades > 0 else None
                )
            rows.append(row)

    summaries: dict[str, object] = {}
    for event_type in ("CPI", "NFP"):
        summaries[event_type] = {
            symbol: summarize_group([
                r for r in rows
                if r["event_type"] == event_type and r["symbol"] == symbol
            ])
            for symbol in SYMBOLS
        }

    consensus = event_consensus_rows(rows)
    consensus_summary = {
        event_type: summarize_group([
            r for r in consensus if r["event_type"] == event_type
        ])
        for event_type in ("CPI", "NFP")
    }

    largest = sorted(rows, key=lambda r: abs(float(r["ret_60m"])), reverse=True)[:20]
    body = {
        "document_type": "NEWS_SHOCK_LAB_V02_CPI_NFP_ROBUST_CONTROLS_RECEIPT",
        "version": "0.2",
        "status": "DIAGNOSTIC_COMPLETE",
        "authority": "HISTORICAL_DIAGNOSTIC_ONLY_NO_TRADING_AUTHORITY",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "schedule_manifest_fingerprint": manifest["fingerprint"],
        "metadata_preflight_fingerprint": preflight["fingerprint"],
        "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY",
        "event_counts": manifest["event_counts"],
        "symbols": list(SYMBOLS),
        "timeframe": "1m",
        "market_days_loaded": len(days),
        "asset_event_observations": len(rows),
        "event_consensus_observations": len(consensus),
        "control_count_distribution": {
            str(n): sum(1 for r in rows if r["control_count"] == n)
            for n in sorted({r["control_count"] for r in rows})
        },
        "summary_by_event_type_and_symbol": summaries,
        "summary_event_consensus": consensus_summary,
        "largest_abs_60m_moves": [
            {
                "event_type": r["event_type"],
                "symbol": r["symbol"],
                "event_date": r["event_date"],
                "ret_5m": r["ret_5m"],
                "ret_15m": r["ret_15m"],
                "incremental_ret_15_60m": r["incremental_ret_15_60m"],
                "ret_60m": r["ret_60m"],
                "flow_15m": r["flow_15m"],
                "volume_ratio_15m": r["volume_ratio_15m"],
                "control_count": r["control_count"],
            }
            for r in largest
        ],
        "all_event_rows": rows,
        "event_consensus_rows": consensus,
        "guards": {
            "live_trading": False,
            "exchange_mutation": False,
            "main_merge": False,
            "render_deploy": False,
            "holdout_2026_accessed": False,
            "mexc_2025_09_through_2025_12_accessed": False,
            "directional_rule_defined": False,
            "trading_edge_claimed": False,
            "event_exclusion_due_to_market_gap": False,
            "synthetic_candles_used": False,
            "interpolation_used": False,
        },
    }
    body["fingerprint"] = canonical_hash(body)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        raise SystemExit("usage: v02_runner <raw_root> <manifest.json> <preflight.json> <receipt.json>")
    receipt = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    print(json.dumps({
        "status": receipt["status"],
        "fingerprint": receipt["fingerprint"],
        "event_counts": receipt["event_counts"],
        "asset_event_observations": receipt["asset_event_observations"],
        "event_consensus_observations": receipt["event_consensus_observations"],
        "control_count_distribution": receipt["control_count_distribution"],
        "summary_by_event_type_and_symbol": receipt["summary_by_event_type_and_symbol"],
        "summary_event_consensus": receipt["summary_event_consensus"],
        "largest_abs_60m_moves": receipt["largest_abs_60m_moves"],
        "guards": receipt["guards"],
    }, indent=2, sort_keys=True))
