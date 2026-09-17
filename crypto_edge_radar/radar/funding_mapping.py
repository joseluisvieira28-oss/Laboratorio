from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode

from .friction import ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS, MEXC_API_TAKER_ONE_WAY_FRACTION
from .market import MEXCFuturesPublicFeed, MarketDataError

DAY_MS = 24 * 60 * 60 * 1000
TAKER_ROUND_TRIP_BPS = 2.0 * MEXC_API_TAKER_ONE_WAY_FRACTION * 10_000.0


def _midnight_ms(value: str) -> int:
    dt = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def load_frozen_event_schedule(path: str | Path) -> list[dict]:
    """Read only the frozen event/timing/direction columns from the OOS ledger.

    Outcome columns may exist in the source CSV but are deliberately ignored.
    This diagnostic is about implementation funding burden, not strategy rescue.
    """
    out: list[dict] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"as_of", "entry", "exit", "position"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("event ledger missing required frozen schedule columns")
        for row in reader:
            position = int(float(row["position"]))
            if position not in {-1, 0, 1}:
                raise ValueError("position must be -1, 0 or 1")
            out.append(
                {
                    "as_of": row["as_of"],
                    "entry": row["entry"],
                    "exit": row["exit"],
                    "position": position,
                }
            )
    if not out:
        raise ValueError("event ledger is empty")
    return out


def _funding_history_page(
    feed: MEXCFuturesPublicFeed,
    *,
    symbol: str,
    page_num: int,
    page_size: int,
) -> dict:
    """Return one public MEXC funding page including pagination metadata."""
    raw = feed._validate_contract_symbol(symbol)
    query = urlencode({"symbol": raw, "page_num": page_num, "page_size": page_size})
    payload = feed._get_json(f"/api/v1/contract/funding_rate/history?{query}")
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise MarketDataError("invalid MEXC funding history payload")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise MarketDataError("MEXC funding history missing data")
    rows = data.get("resultList")
    if not isinstance(rows, list):
        raise MarketDataError("MEXC funding history missing resultList")
    for key in ("currentPage", "totalPage", "totalCount", "pageSize"):
        if key not in data:
            raise MarketDataError(f"MEXC funding history missing pagination field {key}")
    return data


def fetch_funding_rows_for_window(
    feed: MEXCFuturesPublicFeed,
    *,
    symbol: str,
    start_ms: int,
    end_ms: int,
    page_size: int = 1000,
    max_pages: int = 100,
) -> tuple[list[dict], dict]:
    if start_ms >= end_ms:
        raise ValueError("funding window start must be before end")
    rows_by_time: dict[int, dict] = {}
    oldest_seen: int | None = None
    pagination_receipt: dict = {}

    for page in range(1, max_pages + 1):
        data = _funding_history_page(
            feed,
            symbol=symbol,
            page_num=page,
            page_size=page_size,
        )
        rows = data["resultList"]
        current_page = int(data["currentPage"])
        total_page = int(data["totalPage"])
        total_count = int(data["totalCount"])
        actual_page_size = int(data["pageSize"])
        if current_page != page:
            raise MarketDataError(
                f"MEXC funding pagination page mismatch requested={page} returned={current_page}"
            )
        pagination_receipt = {
            "requested_page_size": page_size,
            "reported_page_size": actual_page_size,
            "total_count": total_count,
            "total_pages": total_page,
            "last_page_requested": page,
        }
        if not rows:
            break

        page_times: list[int] = []
        for row in rows:
            try:
                settle = int(float(row["settleTime"]))
                float(row["fundingRate"])
            except (KeyError, TypeError, ValueError):
                continue
            rows_by_time[settle] = row
            page_times.append(settle)
        if not page_times:
            raise MarketDataError("MEXC funding page contained no valid settlement rows")

        page_oldest = min(page_times)
        if oldest_seen is not None and page_oldest >= oldest_seen:
            raise MarketDataError("MEXC funding pagination did not move backward")
        oldest_seen = page_oldest
        if page_oldest <= start_ms:
            break
        if page >= total_page:
            break
    else:
        raise MarketDataError("MEXC funding pagination exceeded fail-closed max_pages")

    all_times = sorted(rows_by_time)
    if not all_times:
        raise MarketDataError("MEXC funding history returned no valid rows")

    pagination_receipt["oldest_retrieved_ms"] = all_times[0]
    pagination_receipt["newest_retrieved_ms"] = all_times[-1]
    pagination_receipt["retrieved_unique_rows"] = len(all_times)

    selected = [
        rows_by_time[settle]
        for settle in all_times
        if start_ms <= settle <= end_ms
    ]
    if not selected:
        raise MarketDataError("no MEXC funding rows cover requested event window")

    selected_times = [int(float(row["settleTime"])) for row in selected]
    if min(selected_times) > start_ms + DAY_MS:
        raise MarketDataError(
            "MEXC funding history does not reach requested start; "
            f"requested_start={start_ms} oldest_retrieved={all_times[0]} "
            f"total_count={pagination_receipt.get('total_count')} total_pages={pagination_receipt.get('total_pages')}"
        )
    if max(selected_times) < end_ms - DAY_MS:
        raise MarketDataError(
            "MEXC funding history does not reach requested end; "
            f"requested_end={end_ms} newest_retrieved={all_times[-1]}"
        )
    return selected, pagination_receipt


def _event_burden(event: dict, rows: list[dict]) -> dict:
    entry_ms = _midnight_ms(event["entry"])
    exit_ms = _midnight_ms(event["exit"])
    if exit_ms - entry_ms != 7 * DAY_MS:
        raise ValueError("frozen event is not exactly seven days")

    position = int(event["position"])
    if position == 0:
        return {
            **event,
            "direction": "FLAT",
            "funding_burden_min_bps": 0.0,
            "funding_burden_max_bps": 0.0,
            "fee_plus_funding_min_bps": 0.0,
            "fee_plus_funding_max_bps": 0.0,
            "interior_settlement_count": 0,
            "boundary_settlement_count": 0,
        }

    interior_rates: list[float] = []
    boundary_rates: list[float] = []
    for row in rows:
        settle_ms = int(float(row["settleTime"]))
        rate = float(row["fundingRate"])
        if entry_ms < settle_ms < exit_ms:
            interior_rates.append(rate)
        elif settle_ms in {entry_ms, exit_ms}:
            boundary_rates.append(rate)

    interior_signed = position * sum(interior_rates)
    possible_signed = [interior_signed]
    for rate in boundary_rates:
        delta = position * rate
        possible_signed = possible_signed + [value + delta for value in possible_signed]

    burden_min_bps = min(possible_signed) * 10_000.0
    burden_max_bps = max(possible_signed) * 10_000.0
    return {
        **event,
        "direction": "LONG" if position > 0 else "SHORT",
        "interior_settlement_count": len(interior_rates),
        "boundary_settlement_count": len(boundary_rates),
        "funding_burden_min_bps": burden_min_bps,
        "funding_burden_max_bps": burden_max_bps,
        "fee_plus_funding_min_bps": TAKER_ROUND_TRIP_BPS + burden_min_bps,
        "fee_plus_funding_max_bps": TAKER_ROUND_TRIP_BPS + burden_max_bps,
    }


def build_2025_funding_mapping_report(
    *,
    event_csv: str | Path,
    feed: MEXCFuturesPublicFeed | None = None,
    symbol: str = "BTC_USDT",
) -> dict:
    events = load_frozen_event_schedule(event_csv)
    directional = [event for event in events if event["position"] != 0]
    if not directional:
        raise ValueError("no directional events in frozen schedule")

    start_ms = min(_midnight_ms(event["entry"]) for event in directional)
    end_ms = max(_midnight_ms(event["exit"]) for event in directional)
    feed = feed or MEXCFuturesPublicFeed(timeout=15)
    funding_rows, pagination = fetch_funding_rows_for_window(
        feed,
        symbol=symbol,
        start_ms=start_ms,
        end_ms=end_ms,
    )
    event_rows = [_event_burden(event, funding_rows) for event in events]
    directional_rows = [row for row in event_rows if row["position"] != 0]

    mean_min = sum(row["funding_burden_min_bps"] for row in directional_rows) / len(directional_rows)
    mean_max = sum(row["funding_burden_max_bps"] for row in directional_rows) / len(directional_rows)
    fee_funding_upper_over_break_even = sum(
        row["fee_plus_funding_max_bps"] > ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS
        for row in directional_rows
    )
    fee_funding_lower_over_break_even = sum(
        row["fee_plus_funding_min_bps"] > ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS
        for row in directional_rows
    )

    return {
        "diagnostic_id": "ETF-CME-INSTFLOW-001-MEXC-FUNDING-MAPPING-2025-V1",
        "status": "IMPLEMENTATION_MAPPING_DIAGNOSTIC_ONLY",
        "scientific_signal_changed": False,
        "trade_selection_changed": False,
        "market_outcome_columns_read": False,
        "capital_enabled": False,
        "orders_created": False,
        "symbol": symbol,
        "source_event_ledger": str(event_csv),
        "event_count_total": len(events),
        "directional_event_count": len(directional_rows),
        "flat_event_count": len(events) - len(directional_rows),
        "long_event_count": sum(row["position"] == 1 for row in directional_rows),
        "short_event_count": sum(row["position"] == -1 for row in directional_rows),
        "funding_history_row_count": len(funding_rows),
        "funding_api_pagination": pagination,
        "coverage_start_ms": min(int(float(row["settleTime"])) for row in funding_rows),
        "coverage_end_ms": max(int(float(row["settleTime"])) for row in funding_rows),
        "taker_round_trip_fee_bps": TAKER_ROUND_TRIP_BPS,
        "historical_estimated_break_even_round_trip_bps": ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS,
        "mean_directional_funding_burden_bps_range": [mean_min, mean_max],
        "events_fee_plus_funding_definitely_over_break_even": fee_funding_lower_over_break_even,
        "events_fee_plus_funding_possibly_over_break_even": fee_funding_upper_over_break_even,
        "boundary_policy": {
            "interior_settlements": "always included",
            "settlement_exactly_at_entry_or_exit": "treated as ambiguous; min/max burden range reports both possibilities",
        },
        "limitations": [
            "Does not use spot or perpetual returns and does not adjudicate strategy profitability.",
            "Does not model historical bid/ask, slippage, basis drift, partial fills or order latency.",
            "Funding burden assumes constant position notional within each seven-day event for rate-sum comparison.",
            "Current 2026 API taker fee schedule is applied as a prospective execution-cost reference; it is not claimed to be the 2025 fee schedule.",
        ],
        "events": event_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = build_2025_funding_mapping_report(event_csv=args.events)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "events"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
