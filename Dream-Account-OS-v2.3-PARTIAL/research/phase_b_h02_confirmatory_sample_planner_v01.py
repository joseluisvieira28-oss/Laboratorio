from __future__ import annotations

"""H02 confirmatory sample planner using provider availability metadata only.

This module must never read market candle bytes. It consumes a caller-supplied
month-availability manifest, selects the longest common contiguous suffix ending
2023-01 across the frozen six-symbol H02 universe, and applies the frozen
calendar-coverage adequacy gate. Even an adequate plan does NOT authorize market
data access; a separate explicit authorization must be frozen first.
"""

from collections.abc import Iterable, Mapping
import hashlib
import json
from pathlib import Path
import re
from typing import Any


HYPOTHESIS_ID = "H02_US_EU_OVERLAP_SESSION_GATE"
LIVE_AUTHORIZED = False
MARKET_DATA_ACCESS_AUTHORIZED = False
VALIDATION_2025_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False
NETWORK_DOWNLOAD_AUTHORIZED = False

CONTRACT_PATH = Path(__file__).with_name(
    "PHASE_B_H02_CONFIRMATORY_DATA_SAMPLE_CONTRACT_V0.1.json"
)
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    body.pop("fingerprint", None)
    encoded = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_h02_sample_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("document_type") != "PHASE_B_H02_CONFIRMATORY_DATA_SAMPLE_CONTRACT":
        raise ValueError("wrong H02 sample contract document type")
    expected = payload.get("fingerprint")
    actual = _canonical_fingerprint(payload)
    if not isinstance(expected, str) or expected != actual:
        raise ValueError("H02 sample contract fingerprint mismatch")
    if payload.get("status") != "FROZEN_SAMPLE_DESIGN_NO_MARKET_DATA_AUTHORIZED":
        raise ValueError("H02 sample contract status is not frozen fail-closed")
    authority = payload["authority_boundary"]
    if authority["this_file_authorizes_market_candle_bytes"] is not False:
        raise ValueError("sample contract must not authorize market candle bytes")
    if authority["this_file_authorizes_2026"] is not False:
        raise ValueError("sample contract must keep 2026 locked")
    return payload


def _month_index(month: str) -> int:
    if not isinstance(month, str) or _MONTH_RE.fullmatch(month) is None:
        raise ValueError(f"invalid source month: {month!r}")
    year, mon = map(int, month.split("-"))
    return year * 12 + (mon - 1)


def _month_from_index(index: int) -> str:
    year, zero_based_month = divmod(index, 12)
    return f"{year:04d}-{zero_based_month + 1:02d}"


def plan_h02_confirmatory_window(
    availability_by_symbol: Mapping[str, Iterable[str]],
    *,
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    """Plan from month-existence metadata only; never authorize candle access."""

    contract = load_h02_sample_contract(contract_path)
    route = contract["primary_confirmatory_discovery_route"]
    universe = tuple(route["universe"])
    if set(availability_by_symbol) != set(universe):
        raise ValueError("availability manifest must contain exactly the frozen H02 universe")

    cutoff = route["candidate_period"]["must_end_no_later_than_source_month"]
    cutoff_index = _month_index(cutoff)

    normalized: dict[str, set[int]] = {}
    for symbol in universe:
        month_indexes = set()
        for month in availability_by_symbol[symbol]:
            idx = _month_index(month)
            if idx <= cutoff_index:
                month_indexes.add(idx)
        normalized[symbol] = month_indexes

    common = set.intersection(*(normalized[symbol] for symbol in universe))
    if cutoff_index not in common:
        count = 0
        start = None
    else:
        cursor = cutoff_index
        while cursor in common:
            cursor -= 1
        start_index = cursor + 1
        count = cutoff_index - start_index + 1
        start = _month_from_index(start_index)

    minimum_months = int(
        route["calendar_coverage_gate"][
            "minimum_common_contiguous_calendar_months_before_market_data_access"
        ]
    )
    adequate = count >= minimum_months

    result = {
        "document_type": "PHASE_B_H02_CONFIRMATORY_CATALOG_PLAN",
        "version": "0.1",
        "hypothesis_id": HYPOTHESIS_ID,
        "status": (
            "CATALOG_ADEQUATE_FREEZE_EXACT_WINDOW_BEFORE_DATA_ACCESS"
            if adequate
            else "CATALOG_INADEQUATE_DO_NOT_OPEN_CONFIRMATORY_CANDLES"
        ),
        "planning_input_type": "PROVIDER_MONTH_AVAILABILITY_METADATA_ONLY",
        "market_candle_values_read": False,
        "common_contiguous_source_month_count": count,
        "proposed_source_month_start": start,
        "proposed_source_month_end": cutoff if count else None,
        "minimum_required_common_months": minimum_months,
        "realized_trade_minimum_after_future_access": int(
            route["realized_sample_gate"]["minimum_resolved_trades"]
        ),
        "eligible_for_separate_data_access_authorization": adequate,
        "separate_explicit_data_access_authorization_required": True,
        "validation_2025_09_through_2025_12_authorized": False,
        "holdout_2026_authorized": False,
        "network_download_authorized": False,
        "exchange_mutation_authorized": False,
        "live_trading_authorized": False,
        "contract_fingerprint": contract["fingerprint"],
    }
    result["fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return result
