from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from io import BytesIO, TextIOWrapper
from math import isfinite

from dream_account.models import Candle


TIMEFRAME_MS = 15 * 60 * 1000
TIMEFRAME_US = TIMEFRAME_MS * 1000
EXPECTED_FIELDS = 12
EXPECTED_HEADER = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume", "ignore",
)
UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
CHECKSUM_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*$")
START = date(2023, 2, 1)
END = date(2025, 9, 1)
MICROSECOND_SPOT_START = date(2025, 1, 1)
TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT = (
    "efb5007ac77ff3d87e08f0be9012aba9deaff825557fbc489f802e3948d7602d"
)


@dataclass(frozen=True)
class H04Bar:
    candle: Candle
    quote_asset_volume: float
    number_of_trades: int
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float

    @property
    def flow_imbalance(self) -> float:
        volume = self.candle.volume
        if volume <= 0:
            raise ValueError("zero volume")
        value = (2 * self.taker_buy_base_asset_volume - volume) / volume
        if (
            not isfinite(value)
            or value < -1.000000000001
            or value > 1.000000000001
        ):
            raise ValueError("invalid flow imbalance")
        return max(-1.0, min(1.0, value))


@dataclass(frozen=True)
class H04DailyAdapterResult:
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
    bars: tuple[H04Bar, ...]
    reasons: tuple[str, ...]


def _expected_filename(symbol: str, day: str) -> str:
    if symbol not in UNIVERSE:
        raise ValueError("symbol outside H04 universe")
    parsed = date.fromisoformat(day)
    if parsed < START or parsed >= END:
        raise ValueError("day outside H04 discovery window")
    return f"{symbol}-15m-{day}.zip"


def _checksum(text: str, filename: str) -> str:
    match = CHECKSUM_RE.fullmatch(text.strip())
    if not match or match.group(2) != filename:
        raise ValueError("invalid checksum")
    return match.group(1).lower()


def _timestamp_unit(day: str) -> str:
    return "microseconds" if date.fromisoformat(day) >= MICROSECOND_SPOT_START else "milliseconds"


def _normalize_timestamps(day: str, source_open_time: int, source_close_time: int) -> tuple[int, int, bool]:
    """Normalize provider timestamp units without touching any market value.

    Binance public-data documentation states that Spot timestamps from 2025-01-01
    onward are expressed in microseconds. Earlier H04 rows are milliseconds.
    The unit rule is therefore date-based and frozen from provider documentation,
    never inferred from outcomes or price/flow values.
    """

    unit = _timestamp_unit(day)
    if unit == "microseconds":
        if source_open_time % 1000 != 0:
            raise ValueError("microsecond kline open_time is not millisecond-aligned")
        open_time_ms = source_open_time // 1000
        expected_source_close = source_open_time + TIMEFRAME_US - 1
        if source_close_time <= source_open_time or source_close_time > expected_source_close:
            raise ValueError("invalid microsecond source close_time")
        close_anomaly = source_close_time != expected_source_close
    else:
        open_time_ms = source_open_time
        expected_source_close = source_open_time + TIMEFRAME_MS - 1
        if source_close_time <= source_open_time or source_close_time > expected_source_close:
            raise ValueError("invalid millisecond source close_time")
        close_anomaly = source_close_time != expected_source_close

    canonical_close_time_ms = open_time_ms + TIMEFRAME_MS - 1
    return open_time_ms, canonical_close_time_ms, close_anomaly


def adapt_h04_binance_daily_archive_bytes(
    *,
    symbol: str,
    day: str,
    archive_filename: str,
    archive_bytes: bytes,
    checksum_text: str,
) -> H04DailyAdapterResult:
    expected = _expected_filename(symbol, day)
    if archive_filename != expected:
        raise ValueError("archive filename mismatch")

    raw = bytes(archive_bytes)
    actual = sha256(raw).hexdigest()
    if actual != _checksum(checksum_text, expected):
        return H04DailyAdapterResult(
            "BLOCKED_CHECKSUM_MISMATCH", symbol, day, expected, actual, False,
            0, 0, 0, 0, (), ("ARCHIVE_SHA256_MISMATCH",),
        )

    member = expected[:-4] + ".csv"
    reasons: list[str] = []
    rows: list[H04Bar] = []
    seen: set[int] = set()
    previous: int | None = None
    anomalies = 0
    start_ms = int(
        datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000
    )
    end_ms = start_ms + 86_400_000

    try:
        zf = zipfile.ZipFile(BytesIO(raw))
    except zipfile.BadZipFile:
        return H04DailyAdapterResult(
            "BLOCKED_INVALID_ZIP", symbol, day, expected, actual, True,
            0, 0, 0, 0, (), ("INVALID_ZIP",),
        )

    infos = zf.infolist()
    if len(infos) != 1 or infos[0].filename != member:
        return H04DailyAdapterResult(
            "BLOCKED_ZIP_MEMBER", symbol, day, expected, actual, True,
            0, 0, 0, 0, (), ("UNEXPECTED_MEMBER",),
        )

    with zf.open(infos[0], "r") as binary:
        reader = csv.reader(TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
        first = False
        for raw_row in reader:
            if not raw_row or all(not cell.strip() for cell in raw_row):
                continue
            normalized = tuple(cell.strip().lower().replace(" ", "_") for cell in raw_row)
            if not first and normalized == EXPECTED_HEADER:
                first = True
                continue
            first = True
            if len(raw_row) != EXPECTED_FIELDS:
                reasons.append("FIELD_COUNT")
                continue

            try:
                source_open_time = int(raw_row[0])
                open_price, high, low, close, volume = map(float, raw_row[1:6])
                source_close_time = int(raw_row[6])
                quote_volume = float(raw_row[7])
                number_of_trades = int(raw_row[8])
                taker_buy_base = float(raw_row[9])
                taker_buy_quote = float(raw_row[10])
                float(raw_row[11])
            except Exception:
                reasons.append("NUMERIC")
                continue

            try:
                open_time, canonical_close_time, close_anomaly = _normalize_timestamps(
                    day, source_open_time, source_close_time
                )
            except ValueError:
                reasons.append("TIMESTAMP_UNIT_OR_CLOSE_TIME")
                continue

            if close_anomaly:
                anomalies += 1

            values = (
                open_price, high, low, close, volume,
                quote_volume, taker_buy_base, taker_buy_quote,
            )
            if (
                not all(isfinite(value) for value in values)
                or min(open_price, high, low, close) <= 0
                or volume < 0
                or quote_volume < 0
                or number_of_trades < 0
                or taker_buy_base < 0
                or taker_buy_base > volume + max(1e-12, abs(volume) * 1e-10)
            ):
                reasons.append("VALUE")
            if high < max(open_price, close, low) or low > min(open_price, close, high):
                reasons.append("OHLC")
            if open_time in seen or (previous is not None and open_time <= previous):
                reasons.append("ORDER")
            seen.add(open_time)
            if previous is not None and (open_time - previous) % TIMEFRAME_MS != 0:
                reasons.append("SPACING")
            previous = open_time
            if open_time % TIMEFRAME_MS != 0 or not start_ms <= open_time < end_ms:
                reasons.append("TIME")

            rows.append(
                H04Bar(
                    Candle(
                        open_time, open_price, high, low, close, volume,
                        canonical_close_time, True,
                    ),
                    quote_volume,
                    number_of_trades,
                    taker_buy_base,
                    taker_buy_quote,
                )
            )

    gaps = 0
    missing = 0
    for left, right in zip(rows, rows[1:]):
        delta = right.candle.open_time - left.candle.open_time
        if delta > TIMEFRAME_MS and delta % TIMEFRAME_MS == 0:
            gaps += 1
            missing += delta // TIMEFRAME_MS - 1

    unique_reasons = tuple(sorted(set(reasons)))
    if unique_reasons:
        return H04DailyAdapterResult(
            "BLOCKED_BINANCE_DAILY_INTEGRITY", symbol, day, expected, actual, True,
            len(rows), gaps, missing, anomalies, (), unique_reasons,
        )

    return H04DailyAdapterResult(
        "PASS_BINANCE_DAILY_WITH_GAPS" if gaps else "PASS_BINANCE_DAILY",
        symbol,
        day,
        expected,
        actual,
        True,
        len(rows),
        gaps,
        missing,
        anomalies,
        tuple(rows),
        (),
    )
