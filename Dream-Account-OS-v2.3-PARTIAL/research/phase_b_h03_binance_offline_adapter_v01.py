from __future__ import annotations

"""Pure/offline Binance Spot kline adapter primitives for H03.

No file is opened, no network is accessed and no stage is authorized here. Callers
must supply already-obtained archive bytes plus the corresponding official CHECKSUM
text. The functions verify checksum, ZIP/member identity, the frozen 12-field Binance
Spot kline schema and 15m integrity, then return closed Candle objects.

H03 adapter amendment V0.1 freezes a canonical 15m close boundary after a full-corpus,
pre-outcome metadata audit found 22 isolated source close_time anomalies among 420,090
rows while every open timestamp remained aligned, ordered and day-bounded. Source
close_time is still parsed and audited; OHLCV and open_time are never altered.
"""

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO, TextIOWrapper
from math import isfinite
import re
import zipfile

from dream_account.models import Candle


HYPOTHESIS_ID = "H03_BINANCE_CROSS_VENUE_US_EU_OVERLAP_REPLICATION"
H03_FREEZE_FINGERPRINT = "0c7c931bd48d4cd696e4a8f3188db64e497716dbc7020eb63db100aecca49fa7"
CLOSE_TIME_AMENDMENT_FINGERPRINT = "338c67b4275143d06dcda887b939e5aff8a683ac03c32beb120584c8e70c5f71"
TIMEFRAME_MS = 15 * 60 * 1000
EXPECTED_FIELDS = 12
EXPECTED_HEADER = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume", "ignore",
)
UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
CHECKSUM_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*$")

MARKET_DATA_ACCESS_AUTHORIZED = False
NETWORK_DOWNLOAD_AUTHORIZED = False
MEXC_VALIDATION_2025_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False
LIVE_TRADING_AUTHORIZED = False


@dataclass(frozen=True)
class BinanceDailyAdapterResult:
    status: str
    symbol: str
    date_utc: str
    archive_filename: str
    archive_sha256: str
    checksum_verified: bool
    row_count: int
    detected_gap_count: int
    missing_candle_count: int
    source_close_time_anomaly_count: int
    candles: tuple[Candle, ...]
    reasons: tuple[str, ...]


def expected_archive_filename(symbol: str, day: str) -> str:
    if symbol not in UNIVERSE:
        raise ValueError("symbol outside frozen H03 universe")
    parsed = date.fromisoformat(day)
    if parsed < date(2021, 2, 1) or parsed >= date(2023, 2, 1):
        raise ValueError("day outside frozen H03 confirmatory window")
    return f"{symbol}-15m-{day}.zip"


def _parse_checksum(checksum_text: str, expected_filename: str) -> str:
    if not isinstance(checksum_text, str):
        raise TypeError("checksum_text must be a string")
    match = CHECKSUM_RE.fullmatch(checksum_text.strip())
    if match is None:
        raise ValueError("invalid Binance CHECKSUM format")
    digest, filename = match.groups()
    if filename != expected_filename:
        raise ValueError("checksum filename mismatch")
    return digest.lower()


def _day_bounds_ms(day: str) -> tuple[int, int]:
    parsed = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = int(parsed.timestamp() * 1000)
    end = int((parsed + timedelta(days=1)).timestamp() * 1000)
    return start, end


def _is_header(row: list[str]) -> bool:
    normalized = tuple(cell.strip().lower().replace(" ", "_") for cell in row)
    return normalized == EXPECTED_HEADER


def _blocked(
    *, status: str, symbol: str, day: str, archive_filename: str,
    archive_sha256: str, checksum_verified: bool, reasons: tuple[str, ...],
    row_count: int = 0, gap_count: int = 0, missing_count: int = 0,
    close_time_anomaly_count: int = 0,
) -> BinanceDailyAdapterResult:
    return BinanceDailyAdapterResult(
        status=status,
        symbol=symbol,
        date_utc=day,
        archive_filename=archive_filename,
        archive_sha256=archive_sha256,
        checksum_verified=checksum_verified,
        row_count=row_count,
        detected_gap_count=gap_count,
        missing_candle_count=missing_count,
        source_close_time_anomaly_count=close_time_anomaly_count,
        candles=(),
        reasons=reasons,
    )


def adapt_binance_daily_archive_bytes(
    *, symbol: str, day: str, archive_filename: str,
    archive_bytes: bytes, checksum_text: str,
) -> BinanceDailyAdapterResult:
    """Verify and adapt one already-obtained Binance daily Spot 15m ZIP in memory."""

    expected = expected_archive_filename(symbol, day)
    if archive_filename != expected:
        raise ValueError("archive filename mismatch")
    if not isinstance(archive_bytes, (bytes, bytearray)):
        raise TypeError("archive_bytes must be bytes")
    raw = bytes(archive_bytes)
    actual_sha = sha256(raw).hexdigest()
    expected_sha = _parse_checksum(checksum_text, expected)
    if actual_sha != expected_sha:
        return _blocked(
            status="BLOCKED_CHECKSUM_MISMATCH", symbol=symbol, day=day,
            archive_filename=archive_filename, archive_sha256=actual_sha,
            checksum_verified=False, reasons=("ARCHIVE_SHA256_MISMATCH",),
        )

    expected_member = expected[:-4] + ".csv"
    try:
        zf = zipfile.ZipFile(BytesIO(raw))
    except zipfile.BadZipFile:
        return _blocked(
            status="BLOCKED_INVALID_ZIP", symbol=symbol, day=day,
            archive_filename=archive_filename, archive_sha256=actual_sha,
            checksum_verified=True, reasons=("INVALID_ZIP_ARCHIVE",),
        )

    infos = zf.infolist()
    if len(infos) != 1 or infos[0].filename != expected_member:
        return _blocked(
            status="BLOCKED_ZIP_MEMBER_IDENTITY", symbol=symbol, day=day,
            archive_filename=archive_filename, archive_sha256=actual_sha,
            checksum_verified=True, reasons=("UNEXPECTED_ZIP_MEMBER_SET",),
        )
    info = infos[0]
    if info.is_dir() or info.flag_bits & 0x1:
        return _blocked(
            status="BLOCKED_ZIP_MEMBER_SAFETY", symbol=symbol, day=day,
            archive_filename=archive_filename, archive_sha256=actual_sha,
            checksum_verified=True, reasons=("DIRECTORY_OR_ENCRYPTED_ZIP_MEMBER",),
        )

    start_ms, end_ms = _day_bounds_ms(day)
    rows: list[tuple[int, float, float, float, float, float, int]] = []
    reasons: list[str] = []
    seen: set[int] = set()
    previous: int | None = None
    close_time_anomaly_count = 0

    try:
        with zf.open(info, "r") as binary:
            wrapper = TextIOWrapper(binary, encoding="utf-8-sig", newline="")
            reader = csv.reader(wrapper)
            first_data_seen = False
            for raw_row in reader:
                if not raw_row or all(not cell.strip() for cell in raw_row):
                    continue
                if not first_data_seen and _is_header(raw_row):
                    first_data_seen = True
                    continue
                first_data_seen = True
                if len(raw_row) != EXPECTED_FIELDS:
                    reasons.append("MALFORMED_FIELD_COUNT")
                    continue
                try:
                    open_time = int(raw_row[0])
                    open_price = float(raw_row[1])
                    high = float(raw_row[2])
                    low = float(raw_row[3])
                    close = float(raw_row[4])
                    volume = float(raw_row[5])
                    source_close_time = int(raw_row[6])
                    float(raw_row[7])
                    int(raw_row[8])
                    float(raw_row[9])
                    float(raw_row[10])
                    float(raw_row[11])
                except (TypeError, ValueError, OverflowError):
                    reasons.append("MALFORMED_NUMERIC_FIELD")
                    continue

                numeric = (open_price, high, low, close, volume)
                if not all(isfinite(value) for value in numeric):
                    reasons.append("NON_FINITE_VALUE")
                if open_time in seen:
                    reasons.append("DUPLICATE_OPEN_TIME")
                seen.add(open_time)
                if previous is not None and open_time <= previous:
                    reasons.append("OUT_OF_ORDER_ROWS")
                if previous is not None:
                    delta = open_time - previous
                    if delta <= 0 or delta % TIMEFRAME_MS != 0:
                        reasons.append("IRREGULAR_INTERVAL_SPACING")
                previous = open_time
                if open_time % TIMEFRAME_MS != 0:
                    reasons.append("OPEN_TIME_ALIGNMENT_VIOLATION")
                if not start_ms <= open_time < end_ms:
                    reasons.append("UTC_DAY_BOUNDARY_VIOLATION")

                canonical_close_time = open_time + TIMEFRAME_MS - 1
                if source_close_time <= open_time:
                    reasons.append("SOURCE_CLOSE_TIME_NOT_AFTER_OPEN")
                elif source_close_time > canonical_close_time:
                    reasons.append("SOURCE_CLOSE_TIME_EXCEEDS_CANONICAL_BOUNDARY")
                elif source_close_time != canonical_close_time:
                    close_time_anomaly_count += 1

                if volume < 0:
                    reasons.append("NEGATIVE_VOLUME")
                if (
                    open_price <= 0 or high <= 0 or low <= 0 or close <= 0
                    or high < max(open_price, close) or low > min(open_price, close) or high < low
                ):
                    reasons.append("OHLC_INTEGRITY_VIOLATION")

                # Only close-time metadata is normalized. All market values and open_time
                # are preserved byte-for-value from the official source row.
                rows.append((open_time, open_price, high, low, close, volume, canonical_close_time))
    except (OSError, UnicodeError, csv.Error, RuntimeError):
        reasons.append("ZIP_CSV_READ_FAILURE")

    if not rows:
        reasons.append("EMPTY_DATASET")

    gap_count = 0
    missing_count = 0
    for left, right in zip(rows, rows[1:]):
        delta = right[0] - left[0]
        if delta > TIMEFRAME_MS and delta % TIMEFRAME_MS == 0:
            gap_count += 1
            missing_count += delta // TIMEFRAME_MS - 1

    unique_reasons = tuple(sorted(set(reasons)))
    if unique_reasons:
        return _blocked(
            status="BLOCKED_BINANCE_DAILY_INTEGRITY", symbol=symbol, day=day,
            archive_filename=archive_filename, archive_sha256=actual_sha,
            checksum_verified=True, reasons=unique_reasons, row_count=len(rows),
            gap_count=gap_count, missing_count=missing_count,
            close_time_anomaly_count=close_time_anomaly_count,
        )

    candles = tuple(
        Candle(open_time, open_price, high, low, close, volume, canonical_close_time, True)
        for open_time, open_price, high, low, close, volume, canonical_close_time in rows
    )
    return BinanceDailyAdapterResult(
        status="PASS_BINANCE_DAILY_WITH_GAPS" if gap_count else "PASS_BINANCE_DAILY",
        symbol=symbol,
        date_utc=day,
        archive_filename=archive_filename,
        archive_sha256=actual_sha,
        checksum_verified=True,
        row_count=len(rows),
        detected_gap_count=gap_count,
        missing_candle_count=missing_count,
        source_close_time_anomaly_count=close_time_anomaly_count,
        candles=candles,
        reasons=(),
    )
