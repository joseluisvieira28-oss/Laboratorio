from __future__ import annotations

"""Offline manifest planner for H03 official Binance Spot daily 15m archives.

This module constructs the exact expected archive/checksum object names for the frozen
H03 Discovery window. It performs no HTTP requests, opens no market-data files,
classifies no outcomes, and authorizes no data access. A later, separately frozen data
access authorization is required before any archive bytes may be downloaded or read.
"""

from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any


HYPOTHESIS_ID = "H03_BINANCE_CROSS_VENUE_US_EU_OVERLAP_REPLICATION"
FREEZE_FINGERPRINT = "0c7c931bd48d4cd696e4a8f3188db64e497716dbc7020eb63db100aecca49fa7"
BASE_URL = "https://data.binance.vision/data/spot/daily/klines"
TIMEFRAME = "15m"
UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_DATE = date(2021, 2, 1)
END_DATE_EXCLUSIVE = date(2023, 2, 1)
EXPECTED_DAY_COUNT = 730
EXPECTED_ARCHIVE_COUNT = EXPECTED_DAY_COUNT * len(UNIVERSE)

MARKET_DATA_ACCESS_AUTHORIZED = False
NETWORK_DOWNLOAD_AUTHORIZED = False
MEXC_VALIDATION_2025_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False
LIVE_TRADING_AUTHORIZED = False


def expected_h03_daily_objects() -> tuple[dict[str, Any], ...]:
    """Return the exact metadata-only H03 daily object manifest."""

    rows: list[dict[str, Any]] = []
    cursor = START_DATE
    while cursor < END_DATE_EXCLUSIVE:
        day = cursor.isoformat()
        for symbol in UNIVERSE:
            filename = f"{symbol}-{TIMEFRAME}-{day}.zip"
            archive_url = f"{BASE_URL}/{symbol}/{TIMEFRAME}/{filename}"
            rows.append(
                {
                    "symbol": symbol,
                    "date_utc": day,
                    "timeframe": TIMEFRAME,
                    "archive_filename": filename,
                    "archive_url": archive_url,
                    "checksum_url": archive_url + ".CHECKSUM",
                }
            )
        cursor += timedelta(days=1)

    if len(rows) != EXPECTED_ARCHIVE_COUNT:
        raise RuntimeError("H03 daily manifest cardinality drift")
    return tuple(rows)


def build_h03_manifest_receipt() -> dict[str, Any]:
    objects = expected_h03_daily_objects()
    body = {
        "document_type": "PHASE_B_H03_BINANCE_DAILY_OBJECT_MANIFEST",
        "version": "0.1",
        "hypothesis_id": HYPOTHESIS_ID,
        "status": "METADATA_PLAN_ONLY_NOT_DATA_ACCESS_AUTHORIZATION",
        "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY",
        "archive_granularity": "DAILY_ZIP_FILES",
        "timeframe": TIMEFRAME,
        "symbols": list(UNIVERSE),
        "start_date_utc_inclusive": START_DATE.isoformat(),
        "end_date_utc_exclusive": END_DATE_EXCLUSIVE.isoformat(),
        "calendar_day_count": EXPECTED_DAY_COUNT,
        "expected_archive_count": EXPECTED_ARCHIVE_COUNT,
        "expected_checksum_count": EXPECTED_ARCHIVE_COUNT,
        "first_archive_url": objects[0]["archive_url"],
        "last_archive_url": objects[-1]["archive_url"],
        "market_data_access_authorized": False,
        "network_download_authorized": False,
        "mexc_validation_2025_authorized": False,
        "holdout_2026_authorized": False,
        "exchange_mutation_authorized": False,
        "live_trading_authorized": False,
        "h03_freeze_fingerprint": FREEZE_FINGERPRINT,
    }
    body["fingerprint"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return body


def write_manifest_receipt(path: Path) -> Path:
    """Write metadata only. This never downloads or opens market data."""

    receipt = build_h03_manifest_receipt()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
