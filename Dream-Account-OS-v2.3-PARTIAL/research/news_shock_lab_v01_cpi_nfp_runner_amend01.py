from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from research.news_shock_lab_v01_cpi_nfp_runner import (
    SYMBOLS,
    POST_WINDOWS,
    canonical_hash,
    control_ts_ms,
    event_consensus_rows,
    event_metrics,
    event_ts_ms,
    load_freeze,
    load_manifest,
    parse_day,
    required_days,
    summarize_group,
    valid_control_dates,
)

AMENDMENT_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V01_CONTROL_DATA_GAP_AMENDMENT_V0.1.json"
)
EXPECTED_AMENDMENT_FINGERPRINT = (
    "bc729693b5d16624053e9a105193e7f9fbadd49cdb770c62fa12bb20d2c2bae1"
)
EXPECTED_FREEZE_FINGERPRINT = (
    "55bba04ab42e1c457427a9ba87231c6ff4df52e9f0e083e320700618c38b2f70"
)
EXPECTED_MANIFEST_FINGERPRINT = (
    "baececa93f922a71d328373c94109652c911deae6ae03e76ea4e23d3f8d90560"
)
MIN_VALID_CONTROLS = 3


def load_amendment() -> dict:
    raw = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    recomputed = canonical_hash(unsigned)
    if supplied != EXPECTED_AMENDMENT_FINGERPRINT or recomputed != supplied:
        raise PermissionError("V0.1 Amendment 01 fingerprint mismatch")
    if raw.get("status") != "FROZEN_TECHNICAL_AMENDMENT_AFTER_INTAKE_BEFORE_VALID_RESULT":
        raise PermissionError("V0.1 Amendment 01 status mismatch")
    bindings = raw.get("bindings", {})
    if bindings.get("freeze_fingerprint") != EXPECTED_FREEZE_FINGERPRINT:
        raise PermissionError("V0.1 Amendment 01 freeze binding mismatch")
    if bindings.get("schedule_manifest_fingerprint") != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("V0.1 Amendment 01 manifest binding mismatch")
    policy = raw.get("frozen_gap_policy", {})
    if policy.get("event_day_missing_any_required_pre_or_post_endpoint") != "FAIL_CLOSED_NO_EVENT_EXCLUSION":
        raise PermissionError("event-day gap policy drift")
    if policy.get("control_day_missing_any_required_pre_or_post_endpoint") != "CONTROL_INVALID_SKIP":
        raise PermissionError("control-day gap policy drift")
    if int(policy.get("minimum_valid_controls_after_skips", -1)) != MIN_VALID_CONTROLS:
        raise PermissionError("minimum-control policy drift")
    if policy.get("no_synthetic_candles") is not True or policy.get("no_interpolation") is not True:
        raise PermissionError("synthetic-data guard drift")
    governance = raw.get("governance", {})
    for key in (
        "live_trading_authorized",
        "exchange_mutation_authorized",
        "main_merge_authorized",
        "render_deploy_authorized",
        "holdout_2026_authorized",
        "mexc_2025_09_through_2025_12_authorized",
    ):
        if governance.get(key) is not False:
            raise PermissionError(f"governance drift: {key}")
    return raw


def run(raw_root: Path, manifest_path: Path, output_path: Path) -> dict:
    freeze = load_freeze()
    amendment = load_amendment()
    manifest = load_manifest(manifest_path)
    if manifest.get("fingerprint") != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("unexpected BLS manifest fingerprint")

    event_dates = {e["event_date"] for e in manifest["events"]}
    days = required_days(manifest)
    if any(day.startswith("2026-") for day in days):
        raise PermissionError("2026 required-day guard violation")

    cache: dict[str, dict[str, dict]] = {symbol: {} for symbol in SYMBOLS}
    for symbol in SYMBOLS:
        for day in days:
            cache[symbol][day] = parse_day(raw_root, symbol, day)

    rows: list[dict] = []
    invalid_control_ledger: list[dict] = []

    for symbol in SYMBOLS:
        for event in manifest["events"]:
            event_date = event["event_date"]
            ts = event_ts_ms(event_date)

            # Frozen Amendment 01 rule: event-day gaps remain fatal. We do not
            # catch this exception and we never exclude an event because of it.
            metrics = event_metrics(cache[symbol][event_date], ts)

            controls: list[dict] = []
            invalid_controls: list[dict] = []
            for control_date in valid_control_dates(event_date, event_dates):
                control_day = control_date.isoformat()
                cts = control_ts_ms(control_date)
                try:
                    control_metrics = event_metrics(cache[symbol][control_day], cts)
                except ValueError as exc:
                    item = {
                        "symbol": symbol,
                        "event_type": event["event_type"],
                        "event_date": event_date,
                        "control_date": control_day,
                        "reason": str(exc),
                    }
                    invalid_controls.append(item)
                    invalid_control_ledger.append(item)
                    continue
                controls.append(control_metrics)

            if len(controls) < MIN_VALID_CONTROLS:
                raise RuntimeError(
                    f"insufficient valid controls after frozen gap skips: "
                    f"{symbol} {event['event_type']} {event_date} "
                    f"valid={len(controls)} invalid={len(invalid_controls)}"
                )

            row = {
                "symbol": symbol,
                "event_type": event["event_type"],
                "event_date": event_date,
                "release_utc": event["release_utc"],
                "control_count": len(controls),
                "invalid_control_count": len(invalid_controls),
                "invalid_controls": invalid_controls,
            }
            row.update(metrics)
            for horizon in POST_WINDOWS:
                control_volume = mean(float(c[f"volume_{horizon}m"]) for c in controls)
                control_trades = mean(float(c[f"trades_{horizon}m"]) for c in controls)
                row[f"volume_ratio_{horizon}m"] = (
                    float(metrics[f"volume_{horizon}m"]) / control_volume
                    if control_volume > 0
                    else None
                )
                row[f"trade_ratio_{horizon}m"] = (
                    float(metrics[f"trades_{horizon}m"]) / control_trades
                    if control_trades > 0
                    else None
                )
            rows.append(row)

    summaries: dict[str, object] = {}
    for event_type in ("CPI", "NFP"):
        summaries[event_type] = {
            symbol: summarize_group(
                [
                    row
                    for row in rows
                    if row["event_type"] == event_type and row["symbol"] == symbol
                ]
            )
            for symbol in SYMBOLS
        }

    consensus = event_consensus_rows(rows)
    consensus_summary = {
        event_type: summarize_group(
            [row for row in consensus if row["event_type"] == event_type]
        )
        for event_type in ("CPI", "NFP")
    }

    largest = sorted(
        rows, key=lambda row: abs(float(row["ret_60m"])), reverse=True
    )[:20]

    body = {
        "document_type": "NEWS_SHOCK_LAB_V01_CPI_NFP_REPLICATION_RECEIPT",
        "version": "0.1-amend01",
        "status": "DIAGNOSTIC_COMPLETE",
        "authority": "HISTORICAL_REPLICATION_ONLY_NO_TRADING_AUTHORITY",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "control_gap_amendment_fingerprint": EXPECTED_AMENDMENT_FINGERPRINT,
        "schedule_manifest_fingerprint": manifest["fingerprint"],
        "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY",
        "event_counts": manifest["event_counts"],
        "symbols": list(SYMBOLS),
        "timeframe": "1m",
        "market_days_loaded": len(days),
        "asset_event_observations": len(rows),
        "event_consensus_observations": len(consensus),
        "invalid_control_observations": len(invalid_control_ledger),
        "invalid_control_ledger": invalid_control_ledger,
        "summary_by_event_type_and_symbol": summaries,
        "summary_event_consensus": consensus_summary,
        "largest_abs_60m_moves": [
            {
                "event_type": row["event_type"],
                "symbol": row["symbol"],
                "event_date": row["event_date"],
                "ret_5m": row["ret_5m"],
                "ret_15m": row["ret_15m"],
                "incremental_ret_15_60m": row["incremental_ret_15_60m"],
                "ret_60m": row["ret_60m"],
                "flow_15m": row["flow_15m"],
                "volume_ratio_15m": row["volume_ratio_15m"],
            }
            for row in largest
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
        "audit": {
            "original_failed_run_id": amendment["bindings"]["failed_run_id"],
            "control_gap_policy": amendment["frozen_gap_policy"],
            "original_freeze_status": freeze["status"],
        },
    }
    body["fingerprint"] = canonical_hash(body)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return body


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: amend01_runner <raw_root> <schedule_manifest.json> <out_receipt.json>"
        )
    receipt = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "fingerprint": receipt["fingerprint"],
                "event_counts": receipt["event_counts"],
                "asset_event_observations": receipt["asset_event_observations"],
                "event_consensus_observations": receipt["event_consensus_observations"],
                "invalid_control_observations": receipt["invalid_control_observations"],
                "summary_by_event_type_and_symbol": receipt[
                    "summary_by_event_type_and_symbol"
                ],
                "summary_event_consensus": receipt["summary_event_consensus"],
                "largest_abs_60m_moves": receipt["largest_abs_60m_moves"],
                "guards": receipt["guards"],
            },
            indent=2,
            sort_keys=True,
        )
    )
