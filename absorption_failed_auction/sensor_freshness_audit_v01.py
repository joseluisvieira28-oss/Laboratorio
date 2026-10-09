#!/usr/bin/env python3
"""ABSORPTION-FAILED-AUCTION-001 source-only, read-only operational freshness gate.

This is NOT a scientific amendment or replacement for MM-V1 footprint fields.
Never fetches economic outcomes. Never fills missing candles or changes a frozen rule.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

BAR_MS = 300_000
EXPECTED_LAB = "ABSORPTION-FAILED-AUCTION-001"
SENSOR_LAB = "TV-FOOTPRINT-CALIBRATION-001"
EXPECTED_SENSOR = "MM-V1"
EXPECTED_SYMBOL = "BINANCE:BTCUSDT"


class FreshnessError(Exception):
    pass


def iso_to_ms(value):
    text = str(value).replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise FreshnessError("NOW_MUST_HAVE_UTC_OFFSET")
    return int(dt.timestamp() * 1000)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def intake_stats(path):
    seen = set()
    times = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                opened = int(row["bar_open_ms"])
                closed = int(row["bar_close_ms"])
            except (ValueError, TypeError, KeyError) as e:
                raise FreshnessError("INTAKE_TIMESTAMP_INVALID") from e
            if opened in seen or opened % BAR_MS or closed != opened + BAR_MS - 1:
                raise FreshnessError("INTAKE_DUPLICATE_OR_ALIGNMENT_INVALID")
            seen.add(opened)
            times.append(closed)
    if not times:
        raise FreshnessError("INTAKE_EMPTY")
    if any(b-a != BAR_MS for a, b in zip(times, times[1:])):
        raise FreshnessError("INTAKE_TIME_GAP_OR_UNORDERED")
    return len(times), times[0], times[-1]


def evaluate(trigger, forward, vault, intake, now_ms, *, max_intake_age_hours=24, max_vault_age_hours=48):
    if trigger.get("lab_id") != EXPECTED_LAB or trigger.get("economic_outcomes_unlocked") is not False:
        raise FreshnessError("TRIGGER_AUTHORITY_MISMATCH")
    if trigger.get("trading_authority") != "NONE":
        raise FreshnessError("TRADING_AUTHORITY_MISMATCH")
    if forward.get("lab_id") != EXPECTED_LAB or forward.get("economic_outcomes_unlocked") is not False:
        raise FreshnessError("FORWARD_AUTHORITY_MISMATCH")
    if forward.get("trading_authority") != "NONE" or forward.get("outcome_fields_present") is not False:
        raise FreshnessError("FORWARD_OUTCOMES_NOT_SEALED")
    if (vault.get("lab_id") != SENSOR_LAB or vault.get("sensor_version") != EXPECTED_SENSOR
            or vault.get("symbol") != EXPECTED_SYMBOL or str(vault.get("timeframe")) != "5"):
        raise FreshnessError("VAULT_SENSOR_IDENTITY_MISMATCH")
    n, first, last = intake
    frozen_boundary = int(trigger["event_open_boundary_ms"])
    latest_forward = int(forward["processed_through_bar_close_ms"])
    latest_vault = int(vault["last_bar_close_ms"])
    if int(trigger["intake_last_bar_close_ms"]) != last or int(trigger["intake_rows"]) != n:
        raise FreshnessError("TRIGGER_INTAKE_BINDING_MISMATCH")
    if latest_forward < frozen_boundary or latest_forward > last:
        raise FreshnessError("FORWARD_BOUNDARY_OR_FUTURE_INVALID")
    if last > now_ms or latest_vault > now_ms or latest_forward > now_ms:
        raise FreshnessError("OBSERVATION_TIMESTAMP_AFTER_AUDIT_TIME")
    if n <= 0 or int(trigger["intake_first_bar_close_ms"]) != first:
        raise FreshnessError("INTAKE_FIRST_BAR_BINDING_MISMATCH")
    intake_age_h = round((now_ms-last)/3_600_000,3)
    vault_age_h = round((now_ms-latest_vault)/3_600_000,3)
    ledger_lag_h = round((last-latest_forward)/3_600_000,3)
    reasons = []
    if intake_age_h > max_intake_age_hours:
        reasons.append("CURRENT_INTAKE_STALE")
    if vault_age_h > max_vault_age_hours:
        reasons.append("VAULT_ARCHIVE_STALE")
    if ledger_lag_h > 0:
        reasons.append("FORWARD_LEDGER_LAGS_INTAKE")
    state = ("SOURCE_OBSERVABILITY_OK" if not reasons
             else "SOURCE_STALE_OR_LEDGER_LAG__NO_NEW_FORWARD_EVIDENCE")
    return {
        "schema": "absorption.sensor_freshness.audit.v0.1",
        "lab_id": EXPECTED_LAB,
        "state": state,
        "reasons": reasons,
        "utc_now_ms": now_ms,
        "intake_rows": n,
        "intake_last_close_ms": last,
        "vault_last_close_ms": latest_vault,
        "forward_last_classified_close_ms": latest_forward,
        "intake_age_hours": intake_age_h,
        "vault_age_hours": vault_age_h,
        "ledger_lag_hours": ledger_lag_h,
        "max_intake_age_hours": max_intake_age_hours,
        "max_vault_age_hours": max_vault_age_hours,
        "economic_outcomes_unlocked": False,
        "trading_authority": "NONE",
        "source_reconstruction_permitted": False,
        "required_operator_action": (
            "Verify actual TradingView MM-V1 5m alert, research webhook receiver and "
            "Render TVFP_RECEIPT transport. Export authentic contiguous new receipts "
            "into immutable vault; do not synthesize missing footprints."
            if reasons else "No operational action required solely from freshness."
        ),
        "not_an_edge_verdict": True
    }


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--trigger", required=True)
    a.add_argument("--forward", required=True)
    a.add_argument("--intake", required=True)
    a.add_argument("--vault-manifest", required=True)
    a.add_argument("--now-utc")
    a.add_argument("--output", required=True)
    args = a.parse_args()
    try:
        now = iso_to_ms(args.now_utc) if args.now_utc else int(datetime.now(timezone.utc).timestamp()*1000)
        result = evaluate(read_json(args.trigger), read_json(args.forward),
                          read_json(args.vault_manifest), intake_stats(args.intake), now)
    except (FreshnessError, ValueError, KeyError, OSError) as e:
        result = {"state": "INTEGRITY_BLOCKED", "reason": str(e),
                  "economic_outcomes_unlocked": False, "trading_authority": "NONE"}
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(result), file=sys.stderr)
        return 2
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["state"] == "SOURCE_OBSERVABILITY_OK" else 3


if __name__ == "__main__":
    raise SystemExit(main())
