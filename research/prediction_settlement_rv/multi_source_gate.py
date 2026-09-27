#!/usr/bin/env python3
"""PSRV multi-observation source reliability gate.

Five prospectively scheduled source-only cycles. Raw numerical values are sealed.
Only timing, schemas, hashes, counts, and timestamp-presence diagnostics are exposed.
"""

from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import source_probe as sp  # noqa: E402
import sync_capture_smoke as sc  # noqa: E402

OUT = Path("artifacts/prediction_settlement_rv/multi_source_gate")
RAW = OUT / "sealed_raw"

CYCLE_OFFSETS = [0, 60, 120, 180, 240]
MIN_LEAD_MIN = 15
MAX_LEAD_MIN = 90
MAX_CYCLE_LATENESS_S = 10.0
MAX_MIDPOINT_SKEW_S = 2.0
MAX_REQUEST_ELAPSED_S = 5.0
MIN_COVERAGE = 0.99


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(x: dt.datetime) -> str:
    return x.astimezone(dt.timezone.utc).isoformat()


def provider_timestamp_summary(leg: str, raw: bytes) -> dict[str, Any]:
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        return {"native_timestamp_present": False}
    if not isinstance(obj, dict):
        return {"native_timestamp_present": False}

    keys = []
    values = []
    for k in ("timestamp", "time", "ts", "updatedAt", "updated_at"):
        if k in obj and obj.get(k) is not None:
            keys.append(k)
            values.append(str(obj.get(k)))
    # Timestamps are source-timing metadata, not economic values.
    return {
        "native_timestamp_present": bool(keys),
        "timestamp_keys": keys,
        "timestamp_values": values,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    run_start = utcnow()
    receipt: dict[str, Any] = {
        "schema": "PSRV_MULTI_SOURCE_GATE_V0.1",
        "generated_at_utc": iso(run_start),
        "authority": "MULTI_OBSERVATION_SOURCE_GATE_V0.1.md",
        "schedule_offsets_seconds": CYCLE_OFFSETS,
        "frozen_limits": {
            "min_lead_minutes": MIN_LEAD_MIN,
            "max_lead_minutes": MAX_LEAD_MIN,
            "max_cycle_lateness_seconds": MAX_CYCLE_LATENESS_S,
            "max_midpoint_skew_seconds": MAX_MIDPOINT_SKEW_S,
            "max_request_elapsed_seconds": MAX_REQUEST_ELAPSED_S,
            "minimum_coverage": MIN_COVERAGE,
        },
        "economic_values_reported": False,
        "economic_outputs_computed": False,
        "matured_outcomes_read": False,
        "orders": False,
        "authenticated_trading_endpoints": False,
        "future_nearest_joins": 0,
        "silent_imputations": 0,
        "source_data_pass": False,
    }

    try:
        kalshi, _, _ = sp.fetch_kalshi(run_start)
        times = [sp.parse_iso(k["resolution_utc"]) for k in kalshi]
        times = [t for t in times if t is not None]
        poly, _ = sp.fetch_poly_for_times(times, run_start)
        pairs = sp.match(poly, kalshi)

        groups: dict[str, list[dict[str, Any]]] = {}
        for pair in pairs:
            t = sp.parse_iso(pair["resolution_utc"])
            if t is None:
                continue
            lead = (t - run_start).total_seconds() / 60.0
            if MIN_LEAD_MIN <= lead <= MAX_LEAD_MIN:
                groups.setdefault(pair["resolution_utc"], []).append(pair)

        if not groups:
            receipt["adjudication"] = {
                "classification": "WAITING_ELIGIBLE_EXPIRY",
                "source_schedule_gate_pass": False,
                "source_data_pass": False,
            }
            (OUT / "multi_source_gate_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
            print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
            return 0

        selected_resolution = min(groups.keys(), key=lambda x: sp.parse_iso(x))
        frozen_pairs = sorted(groups[selected_resolution], key=lambda x: float(x["nominal_strike"]))
        receipt["selected_resolution_utc"] = selected_resolution
        receipt["frozen_pair_count"] = len(frozen_pairs)

        epoch = utcnow()
        receipt["schedule_epoch_utc"] = iso(epoch)

        cycles: list[dict[str, Any]] = []
        prev_hash: dict[tuple[str, str], str | None] = {}
        successful_pair_observations = 0
        expected_pair_observations = len(frozen_pairs) * len(CYCLE_OFFSETS)
        all_cycle_timing_ok = True

        for cycle_index, offset_s in enumerate(CYCLE_OFFSETS):
            target = epoch + dt.timedelta(seconds=offset_s)
            delay = (target - utcnow()).total_seconds()
            if delay > 0:
                time.sleep(delay)

            cycle_start = utcnow()
            lateness = max(0.0, (cycle_start - target).total_seconds())
            cycle_timing_ok = lateness <= MAX_CYCLE_LATENESS_S
            all_cycle_timing_ok = all_cycle_timing_ok and cycle_timing_ok

            cycle_dir = RAW / f"cycle_{cycle_index:02d}"
            cycle_dir.mkdir(parents=True, exist_ok=True)
            cycle_pairs: list[dict[str, Any]] = []

            for idx, pair in enumerate(frozen_pairs):
                pair_id = f"{idx:03d}_{sc.safe_name(pair['nominal_strike'])}_{sc.safe_name(pair['kalshi_ticker'])}"
                pair_dir = cycle_dir / pair_id
                pair_dir.mkdir(parents=True, exist_ok=True)

                endpoints = {
                    "poly_yes": (sc.POLY_BOOK, {"token_id": pair["polymarket_yes_token_id"]}),
                    "poly_no": (sc.POLY_BOOK, {"token_id": pair["polymarket_no_token_id"]}),
                    "kalshi": (f"{sc.KALSHI_BASE}/markets/{urllib.parse.quote(str(pair['kalshi_ticker']))}/orderbook", None),
                    "coinbase": (sc.COINBASE_TICKER, None),
                }

                with cf.ThreadPoolExecutor(max_workers=4) as ex:
                    futures = {
                        leg: ex.submit(sc.request_raw, leg, url, params)
                        for leg, (url, params) in endpoints.items()
                    }
                    results = {leg: fut.result() for leg, fut in futures.items()}

                mids: list[dt.datetime] = []
                legs_summary: dict[str, Any] = {}
                pair_ok = True

                for leg, result in results.items():
                    raw = result.pop("raw")
                    raw_path = pair_dir / f"{leg}.json"
                    raw_path.write_bytes(raw)

                    schema = sc.schema_summary(leg, raw)
                    timing_meta = provider_timestamp_summary(leg, raw)
                    key = (pair_id, leg)
                    prior = prev_hash.get(key)
                    changed = None if prior is None else (prior != result["raw_sha256"])
                    prev_hash[key] = result["raw_sha256"]

                    if result["status"] != 200 or result["error"] is not None:
                        pair_ok = False
                    if result["elapsed_seconds"] > MAX_REQUEST_ELAPSED_S:
                        pair_ok = False
                    if not schema.get("schema_valid"):
                        pair_ok = False

                    mids.append(dt.datetime.fromisoformat(result["midpoint_utc"]))
                    legs_summary[leg] = {
                        "status": result["status"],
                        "elapsed_seconds": result["elapsed_seconds"],
                        "midpoint_utc": result["midpoint_utc"],
                        "raw_sha256": result["raw_sha256"],
                        "bytes": result["bytes"],
                        "schema": schema,
                        "provider_timing": timing_meta,
                        "raw_changed_since_previous_cycle": changed,
                        "sealed_raw_path": str(raw_path),
                        "error": result["error"],
                    }

                skew = (max(mids) - min(mids)).total_seconds() if len(mids) == 4 else None
                if skew is None or skew > MAX_MIDPOINT_SKEW_S:
                    pair_ok = False

                if pair_ok:
                    successful_pair_observations += 1

                cycle_pairs.append({
                    "nominal_strike": pair["nominal_strike"],
                    "polymarket_market_id": pair["polymarket_market_id"],
                    "kalshi_ticker": pair["kalshi_ticker"],
                    "midpoint_skew_seconds": skew,
                    "transport_pass": pair_ok,
                    "legs": legs_summary,
                })

            cycles.append({
                "cycle_index": cycle_index,
                "target_utc": iso(target),
                "started_utc": iso(cycle_start),
                "start_lateness_seconds": lateness,
                "cycle_timing_pass": cycle_timing_ok,
                "pair_count": len(cycle_pairs),
                "pairs": cycle_pairs,
            })

        coverage = (
            successful_pair_observations / expected_pair_observations
            if expected_pair_observations
            else 0.0
        )
        all_cycles_present = len(cycles) == len(CYCLE_OFFSETS)
        gate_pass = bool(
            frozen_pairs
            and all_cycles_present
            and all_cycle_timing_ok
            and coverage >= MIN_COVERAGE
        )

        # Hash-change diagnostics only; no values.
        change_stats: dict[str, dict[str, int]] = {
            leg: {"changed": 0, "unchanged": 0, "first_observation": 0}
            for leg in ("poly_yes", "poly_no", "kalshi", "coinbase")
        }
        for cycle in cycles:
            for pair in cycle["pairs"]:
                for leg, info in pair["legs"].items():
                    flag = info["raw_changed_since_previous_cycle"]
                    if flag is None:
                        change_stats[leg]["first_observation"] += 1
                    elif flag:
                        change_stats[leg]["changed"] += 1
                    else:
                        change_stats[leg]["unchanged"] += 1

        receipt["cycles"] = cycles
        receipt["hash_change_diagnostics"] = change_stats
        receipt["adjudication"] = {
            "classification": "SOURCE_SCHEDULE_GATE_PASS" if gate_pass else "SOURCE_SCHEDULE_GATE_FAIL",
            "cycle_count": len(cycles),
            "expected_cycle_count": len(CYCLE_OFFSETS),
            "all_cycle_timing_pass": all_cycle_timing_ok,
            "expected_pair_observations": expected_pair_observations,
            "successful_pair_observations": successful_pair_observations,
            "coverage": coverage,
            "minimum_coverage": MIN_COVERAGE,
            "source_schedule_gate_pass": gate_pass,
            "source_data_pass": False,
        }

        receipt["receipt_sha256"] = hashlib.sha256(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        (OUT / "multi_source_gate_receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
        print(json.dumps({"hash_change_diagnostics": change_stats}, indent=2, sort_keys=True))
        print("RAW_ECONOMIC_VALUES_SEALED_NOT_PRINTED")
        return 0

    except Exception as exc:
        receipt["adjudication"] = {
            "classification": "SOURCE_SCHEDULE_GATE_TECHNICAL_FAILURE",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "source_schedule_gate_pass": False,
            "source_data_pass": False,
        }
        (OUT / "multi_source_gate_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt["adjudication"], indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
