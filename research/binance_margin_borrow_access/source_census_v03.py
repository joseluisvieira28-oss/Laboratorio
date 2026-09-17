#!/usr/bin/env python3
"""BINANCE-MARGIN-BORROW-ACCESS-001 source census V0.3.

Adds a frozen upper-boundary preflight to V0.2:
- cursor before=6899;
- any >2024-12-31 timestamp = provenance failure;
- first-page max before 2024-12-31T00:00Z = enumeration incomplete;
- only then run the full backward V0.2 census.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import source_census_v02 as base

UPPER_CURSOR = 6899
END_DT = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
END_DAY_FLOOR_DT = datetime(2024, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
END_MS = int(END_DT.timestamp() * 1000)
END_DAY_FLOOR_MS = int(END_DAY_FLOOR_DT.timestamp() * 1000)
OUT = Path("source_census_v03_output")
OUT.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT / "BINANCE_MARGIN_BORROW_ACCESS_001_SOURCE_CENSUS_RECEIPT_V0_3.json"


def write_preflight_receipt(classification: str, failure: str | None, page: list[dict], protected: bool) -> int:
    receipt = {
        "lab_id": base.LAB_ID,
        "phase": "SOURCE_CENSUS_V0_3_UPPER_BOUNDARY_PREFLIGHT",
        "classification": classification,
        "transport": "official_binance_telegram_index_plus_official_support_detail",
        "upper_cursor": UPPER_CURSOR,
        "frozen_start_utc": "2023-01-01T00:00:00Z",
        "frozen_end_utc": "2024-12-31T23:59:59Z",
        "upper_boundary_requirement": "first-page max timestamp must fall on 2024-12-31 UTC",
        "protected_period_seen": protected,
        "first_page": page,
        "failure": failure,
        "safety": {
            "price_data_opened": False,
            "returns_opened": False,
            "basis_opened": False,
            "borrow_rate_opened": False,
            "borrow_inventory_opened": False,
            "authenticated_exchange_api_used": False,
            "account_data_opened": False,
            "pnl_opened": False,
            "win_rate_opened": False,
            "pf_opened": False,
            "drawdown_opened": False,
            "live_trading": False,
            "exchange_mutation": False,
            "protected_2025_2026_message_seen": protected,
        },
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "lab_id": base.LAB_ID,
        "classification": classification,
        "upper_cursor": UPPER_CURSOR,
        "protected_period_seen": protected,
        "prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "SOURCE_CENSUS_PASS" else 2


def main() -> int:
    try:
        raw, status = base.request_bytes(base.TELEGRAM_BASE, params={"before": str(UPPER_CURSOR)})
        page = base.parse_telegram_page(raw)
        if not page:
            return write_preflight_receipt(
                "SOURCE_ACQUISITION_TECHNICAL_FAILURE",
                "upper-boundary preflight returned no parseable Telegram messages",
                [],
                False,
            )
        max_ms = max(x["timestamp_ms"] for x in page)
        min_ms = min(x["timestamp_ms"] for x in page)
        page_summary = [{
            "http_status": status,
            "messages": len(page),
            "min_message_id": min(x["message_id"] for x in page),
            "max_message_id": max(x["message_id"] for x in page),
            "min_timestamp_ms": min_ms,
            "max_timestamp_ms": max_ms,
        }]
        if max_ms > END_MS:
            return write_preflight_receipt(
                "PROVENANCE_FAILURE",
                "protected-period firewall: cursor 6899 still returns timestamp after 2024-12-31",
                page_summary,
                True,
            )
        if max_ms < END_DAY_FLOOR_MS:
            return write_preflight_receipt(
                "SOURCE_ENUMERATION_INCOMPLETE",
                "upper cursor is protected-safe but does not cover 2024-12-31 UTC",
                page_summary,
                False,
            )

        base.UPPER_CURSOR = UPPER_CURSOR
        rc = base.main()
        src = Path("source_census_v02_output/BINANCE_MARGIN_BORROW_ACCESS_001_SOURCE_CENSUS_RECEIPT_V0_2.json")
        if not src.exists():
            return write_preflight_receipt(
                "SOURCE_ACQUISITION_TECHNICAL_FAILURE",
                "V0.2 engine did not emit a receipt after V0.3 preflight",
                page_summary,
                False,
            )
        receipt = json.loads(src.read_text(encoding="utf-8"))
        receipt["phase"] = "SOURCE_CENSUS_V0_3_ONLY_OUTCOME_BLIND"
        receipt["upper_cursor"] = UPPER_CURSOR
        receipt["v03_upper_boundary_preflight"] = page_summary[0]
        receipt["v03_upper_boundary_pass"] = True
        OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "lab_id": base.LAB_ID,
            "classification": receipt.get("classification"),
            "upper_cursor": UPPER_CURSOR,
            "upper_boundary_pass": True,
            "boundary_reached": receipt.get("enumeration_boundary_reached_before_start"),
            "qualifying_articles": receipt.get("qualifying_cross_margin_borrowable_articles"),
            "years_with_structural_phrase": receipt.get("years_with_structural_phrase"),
            "prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
        }, sort_keys=True))
        return rc
    except Exception as exc:
        return write_preflight_receipt(
            "SOURCE_ACQUISITION_TECHNICAL_FAILURE",
            f"{type(exc).__name__}: {str(exc)[:1000]}",
            [],
            False,
        )


if __name__ == "__main__":
    sys.exit(main())
