from __future__ import annotations

import csv
import io
import json
import urllib.parse
import urllib.request
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from .etf_cme_instflow_001 import (
    CFTCObservation,
    CFTC_CONTRACT_CODE,
    compute_frozen_signal,
)

CFTC_DATASET = "6dca-aqww"
CFTC_BASE = f"https://publicreporting.cftc.gov/resource/{CFTC_DATASET}.csv"


def _parse_row(row: dict[str, str]) -> CFTCObservation:
    raw_date = row["report_date_as_yyyy_mm_dd"]
    as_of = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).date().isoformat()
    return CFTCObservation(
        as_of_date=as_of,
        open_interest=float(row["open_interest_all"]),
        noncommercial_long=float(row["noncomm_positions_long_all"]),
        noncommercial_short=float(row["noncomm_positions_short_all"]),
    )


def fetch_latest_two(timeout: int = 30) -> tuple[CFTCObservation, CFTCObservation]:
    where = f"cftc_contract_market_code='{CFTC_CONTRACT_CODE}'"
    params = {
        "$limit": "2",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$where": where,
    }
    url = CFTC_BASE + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "crypto-edge-radar-etf-cme-source/0.6"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        rows = list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig"))))

    if len(rows) != 2:
        raise RuntimeError(f"expected exactly 2 CFTC rows, got {len(rows)}")

    current = _parse_row(rows[0])
    previous = _parse_row(rows[1])
    if previous.as_of_date >= current.as_of_date:
        raise RuntimeError("CFTC chronology invalid or duplicate latest rows")
    return previous, current


def signal_receipt_from_observations(
    previous: CFTCObservation,
    current: CFTCObservation,
    now: datetime,
) -> dict:
    """Evaluate the frozen signal from already-fetched observations.

    This helper exists so runtime code can cache the slow public CFTC rows while
    re-evaluating the time gate on every radar cycle. It does not alter the
    scientific signal or create a late-entry tolerance.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)

    signal = compute_frozen_signal(previous, current)

    as_of_date = datetime.fromisoformat(current.as_of_date).date()
    information_safe_time = datetime.combine(
        as_of_date + timedelta(days=signal.information_lag_days),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    exact_entry_time = information_safe_time
    exact_exit_time = exact_entry_time + timedelta(days=signal.hold_days)

    if now < information_safe_time:
        state = "WAITING_INFORMATION_SAFE_TIME"
        entry_eligible_now = False
    elif now == exact_entry_time:
        state = "EXACT_ENTRY_TIME"
        entry_eligible_now = signal.direction.value != "NONE"
    else:
        # The frozen historical implementation enters at the exact first 00:00 UTC
        # at/after the conservative information-safe time. V0.6 still refuses to
        # invent discretionary late-entry tolerance.
        state = "ENTRY_WINDOW_PASSED_DO_NOT_CHASE"
        entry_eligible_now = False

    return {
        "strategy_id": signal.strategy_id,
        "source": "CFTC_PUBLIC_REPORTING",
        "dataset": CFTC_DATASET,
        "contract_code": CFTC_CONTRACT_CODE,
        "checked_at_utc": now.isoformat().replace("+00:00", "Z"),
        "previous_observation": asdict(previous),
        "current_observation": asdict(current),
        "signal_value": signal.signal_value,
        "direction": signal.direction.value,
        "information_safe_time_utc": information_safe_time.isoformat().replace("+00:00", "Z"),
        "exact_entry_time_utc": exact_entry_time.isoformat().replace("+00:00", "Z"),
        "exact_exit_time_utc": exact_exit_time.isoformat().replace("+00:00", "Z"),
        "state": state,
        "entry_eligible_now": entry_eligible_now,
        "micro_live_eligible": False,
        "micro_live_blocker": "EXECUTION_INSTRUMENT_AND_STRATEGY_RISK_MODEL_NOT_FROZEN",
        "authenticated_exchange_api": False,
        "order_created": False,
    }


def current_signal_receipt(now: datetime | None = None, timeout: int = 30) -> dict:
    now = now or datetime.now(timezone.utc)
    previous, current = fetch_latest_two(timeout=timeout)
    return signal_receipt_from_observations(previous, current, now)


def current_signal_json(now: datetime | None = None, timeout: int = 30) -> str:
    return json.dumps(current_signal_receipt(now=now, timeout=timeout), sort_keys=True)
