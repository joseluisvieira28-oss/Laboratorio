from __future__ import annotations

import argparse
import json
from pathlib import Path

from .friction import ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS
from .funding_mapping import (
    TAKER_ROUND_TRIP_BPS,
    _event_burden,
    _funding_history_page,
    _midnight_ms,
    load_frozen_event_schedule,
)
from .market import MEXCFuturesPublicFeed, MarketDataError


def fetch_all_available_funding_rows(
    feed: MEXCFuturesPublicFeed,
    *,
    symbol: str = "BTC_USDT",
    page_size: int = 1000,
    max_pages: int = 100,
) -> tuple[list[dict], dict]:
    first = _funding_history_page(
        feed,
        symbol=symbol,
        page_num=1,
        page_size=page_size,
    )
    total_pages = int(first["totalPage"])
    if total_pages < 1 or total_pages > max_pages:
        raise MarketDataError(f"funding totalPage outside fail-closed bound: {total_pages}")

    rows_by_time: dict[int, dict] = {}
    reported_page_size = int(first["pageSize"])
    total_count = int(first["totalCount"])
    for page in range(1, total_pages + 1):
        data = first if page == 1 else _funding_history_page(
            feed,
            symbol=symbol,
            page_num=page,
            page_size=page_size,
        )
        if int(data["currentPage"]) != page:
            raise MarketDataError("funding pagination currentPage mismatch")
        for row in data["resultList"]:
            try:
                settle = int(float(row["settleTime"]))
                float(row["fundingRate"])
            except (KeyError, TypeError, ValueError):
                continue
            rows_by_time[settle] = row

    times = sorted(rows_by_time)
    if not times:
        raise MarketDataError("no usable funding rows returned")
    return (
        [rows_by_time[t] for t in times],
        {
            "requested_page_size": page_size,
            "reported_page_size": reported_page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "retrieved_unique_rows": len(times),
            "oldest_retrieved_ms": times[0],
            "newest_retrieved_ms": times[-1],
        },
    )


def build_partial_2025_report(
    *,
    event_csv: str | Path,
    feed: MEXCFuturesPublicFeed | None = None,
    symbol: str = "BTC_USDT",
) -> dict:
    events = load_frozen_event_schedule(event_csv)
    feed = feed or MEXCFuturesPublicFeed(timeout=15)
    funding_rows, coverage = fetch_all_available_funding_rows(feed, symbol=symbol)
    oldest = int(coverage["oldest_retrieved_ms"])
    newest = int(coverage["newest_retrieved_ms"])

    covered: list[dict] = []
    excluded: list[dict] = []
    for event in events:
        if int(event["position"]) == 0:
            excluded.append({**event, "reason": "FLAT_EVENT"})
            continue
        entry_ms = _midnight_ms(event["entry"])
        exit_ms = _midnight_ms(event["exit"])
        if entry_ms < oldest or exit_ms > newest:
            excluded.append({**event, "reason": "OUTSIDE_MEXC_API_FUNDING_COVERAGE"})
            continue
        covered.append(_event_burden(event, funding_rows))

    if not covered:
        raise MarketDataError("no frozen directional events are fully covered by MEXC funding API")

    mean_min = sum(x["funding_burden_min_bps"] for x in covered) / len(covered)
    mean_max = sum(x["funding_burden_max_bps"] for x in covered) / len(covered)
    definitely_over = sum(
        x["fee_plus_funding_min_bps"] > ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS
        for x in covered
    )
    possibly_over = sum(
        x["fee_plus_funding_max_bps"] > ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS
        for x in covered
    )

    by_direction = {}
    for name, position in (("LONG", 1), ("SHORT", -1)):
        rows = [x for x in covered if x["position"] == position]
        by_direction[name] = {
            "count": len(rows),
            "mean_funding_burden_min_bps": (
                sum(x["funding_burden_min_bps"] for x in rows) / len(rows) if rows else None
            ),
            "mean_funding_burden_max_bps": (
                sum(x["funding_burden_max_bps"] for x in rows) / len(rows) if rows else None
            ),
            "definitely_over_break_even_with_current_taker_fee": sum(
                x["fee_plus_funding_min_bps"] > ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS
                for x in rows
            ),
            "possibly_over_break_even_with_current_taker_fee": sum(
                x["fee_plus_funding_max_bps"] > ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS
                for x in rows
            ),
        }

    return {
        "diagnostic_id": "ETF-CME-INSTFLOW-001-MEXC-FUNDING-PARTIAL-2025-V1",
        "classification": "PARTIAL_SOURCE_COVERAGE_DIAGNOSTIC_ONLY",
        "full_2025_source_coverage_pass": False,
        "promotion_allowed_from_this_report": False,
        "scientific_signal_changed": False,
        "trade_selection_changed": False,
        "market_outcome_columns_read": False,
        "capital_enabled": False,
        "orders_created": False,
        "symbol": symbol,
        "source_event_ledger": str(event_csv),
        "event_count_total": len(events),
        "fully_covered_directional_event_count": len(covered),
        "excluded_event_count": len(excluded),
        "long_covered_count": sum(x["position"] == 1 for x in covered),
        "short_covered_count": sum(x["position"] == -1 for x in covered),
        "funding_api_coverage": coverage,
        "taker_round_trip_fee_bps_current_2026_reference": TAKER_ROUND_TRIP_BPS,
        "historical_estimated_break_even_round_trip_bps": ETF_CME_BREAK_EVEN_ROUND_TRIP_BPS,
        "mean_directional_funding_burden_bps_range": [mean_min, mean_max],
        "events_fee_plus_funding_definitely_over_break_even": definitely_over,
        "events_fee_plus_funding_possibly_over_break_even": possibly_over,
        "by_direction": by_direction,
        "boundary_policy": {
            "interior_settlements": "included",
            "entry_exit_exact_settlement": "min/max range because settlement inclusion cannot be assumed",
        },
        "limitations": [
            "MEXC public API starts after the first frozen 2025 events; this report cannot represent the complete 50-event OOS year.",
            "No market outcome/return/PnL columns are read; this is implementation-friction diagnostics only.",
            "Current 2026 taker fee is a deployment reference, not asserted as the historical 2025 fee schedule.",
            "Historical spread, slippage, basis drift, fill probability and authenticated order latency are not reconstructed.",
        ],
        "excluded_events": excluded,
        "events": covered,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = build_partial_2025_report(event_csv=args.events)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"events", "excluded_events"}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
