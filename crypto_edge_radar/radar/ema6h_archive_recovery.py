from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import re
from typing import Any, Callable
from urllib.request import Request, urlopen
import zipfile

from .strategies.ema6h_50x200_regime_forward import (
    DAY_MS,
    FIFTEEN_MIN_MS,
    Candle,
    EMA6HRegimeSourceError,
    validate_regular,
)

ARCHIVE_ROOT_URL = "https://data.binance.vision/data/spot"
_CHECKSUM_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$")
_INTERVAL_STEP_MS = {"15m": FIFTEEN_MIN_MS, "1d": DAY_MS}


@dataclass(frozen=True)
class ArchiveReceipt:
    classification: str
    symbol: str
    interval: str
    period_utc: str
    frequency: str
    checksum_verified: bool
    zip_sha256: str | None
    row_count: int | None
    normalized_microseconds_to_milliseconds: bool

    @property
    def day_utc(self) -> str:
        # Backward-compatible alias for the original daily-only V0.1 receipt.
        return self.period_utc


def _archive_name(
    symbol: str,
    interval: str,
    period_utc: str,
) -> str:
    return f"{symbol.upper()}-{interval}-{period_utc}.zip"


def _archive_url(
    symbol: str,
    interval: str,
    period_utc: str,
    *,
    frequency: str,
) -> str:
    if frequency not in {"daily", "monthly"}:
        raise EMA6HRegimeSourceError(
            f"unsupported Binance archive frequency: {frequency}"
        )
    name = _archive_name(symbol, interval, period_utc)
    return (
        f"{ARCHIVE_ROOT_URL}/{frequency}/klines/"
        f"{symbol.upper()}/{interval}/{name}"
    )


def _to_ms(value: str) -> tuple[int, bool]:
    n = int(value)
    if n >= 10**15:
        return n // 1000, True
    return n, False


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _next_month(day: date) -> date:
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


class BinanceOfficialKlineArchiveRecovery:
    provider = "BINANCE_PUBLIC_DATA_KLINES_RECOVERY_V0.2"

    def __init__(
        self,
        *,
        timeout: int = 15,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.timeout = timeout
        self.opener = opener
        self.last_receipt: ArchiveReceipt | None = None
        self.last_receipts: list[ArchiveReceipt] = []
        self._cache: dict[tuple[str, str, str, str], list[Candle]] = {}

    def _download(self, url: str) -> bytes:
        req = Request(
            url,
            headers={"User-Agent": "crypto-edge-radar/ema6h-archive-recovery-v0.2"},
        )
        with self.opener(req, timeout=self.timeout) as response:
            if response.status != 200:
                raise EMA6HRegimeSourceError(
                    f"Binance archive HTTP {response.status}"
                )
            return response.read()

    def _load_period(
        self,
        symbol: str,
        interval: str,
        period_utc: str,
        *,
        frequency: str,
    ) -> list[Candle]:
        if interval not in _INTERVAL_STEP_MS:
            raise EMA6HRegimeSourceError(
                f"unsupported archive interval: {interval}"
            )
        symbol = symbol.upper()
        cache_key = (frequency, symbol, interval, period_utc)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return list(cached)

        url = _archive_url(
            symbol,
            interval,
            period_utc,
            frequency=frequency,
        )
        name = _archive_name(symbol, interval, period_utc)
        zip_bytes = self._download(url)
        checksum_bytes = self._download(url + ".CHECKSUM")

        checksum_text = checksum_bytes.decode("utf-8").strip()
        match = _CHECKSUM_RE.match(checksum_text)
        if not match:
            raise EMA6HRegimeSourceError(
                "invalid Binance archive CHECKSUM format"
            )
        expected_sha, expected_name = match.groups()
        if expected_name != name:
            raise EMA6HRegimeSourceError(
                "Binance archive CHECKSUM filename mismatch"
            )

        actual_sha = hashlib.sha256(zip_bytes).hexdigest()
        if actual_sha.lower() != expected_sha.lower():
            raise EMA6HRegimeSourceError(
                "Binance archive CHECKSUM mismatch"
            )

        candles: list[Candle] = []
        normalized = False
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                members = [
                    member
                    for member in zf.namelist()
                    if not member.endswith("/")
                ]
                if len(members) != 1:
                    raise EMA6HRegimeSourceError(
                        "Binance archive must contain exactly one CSV"
                    )
                with zf.open(members[0]) as fh:
                    reader = csv.reader(
                        io.TextIOWrapper(
                            fh,
                            encoding="utf-8",
                            newline="",
                        )
                    )
                    for row in reader:
                        if not row:
                            continue
                        if len(row) < 7:
                            raise EMA6HRegimeSourceError(
                                "invalid Binance archive kline row"
                            )
                        open_ms, open_norm = _to_ms(row[0])
                        close_ms, close_norm = _to_ms(row[6])
                        normalized = (
                            normalized or open_norm or close_norm
                        )
                        candles.append(
                            Candle(
                                open_time=open_ms,
                                open=float(row[1]),
                                high=float(row[2]),
                                low=float(row[3]),
                                close=float(row[4]),
                                volume=float(row[5]),
                                close_time=close_ms,
                            )
                        )
        except zipfile.BadZipFile as exc:
            raise EMA6HRegimeSourceError(
                "invalid Binance archive ZIP"
            ) from exc

        candles.sort(key=lambda row: row.open_time)
        if candles:
            validate_regular(
                candles,
                _INTERVAL_STEP_MS[interval],
            )

        receipt = ArchiveReceipt(
            classification=(
                "PASS_CHECKSUM_VERIFIED_MONTHLY_ARCHIVE"
                if frequency == "monthly"
                else "PASS_CHECKSUM_VERIFIED_DAILY_ARCHIVE"
            ),
            symbol=symbol,
            interval=interval,
            period_utc=period_utc,
            frequency=frequency,
            checksum_verified=True,
            zip_sha256=actual_sha,
            row_count=len(candles),
            normalized_microseconds_to_milliseconds=normalized,
        )
        self.last_receipt = receipt
        self.last_receipts.append(receipt)
        self._cache[cache_key] = list(candles)
        return list(candles)

    def load_day(
        self,
        symbol: str,
        interval: str,
        day_utc: str,
    ) -> list[Candle]:
        return self._load_period(
            symbol,
            interval,
            day_utc,
            frequency="daily",
        )

    def load_month(
        self,
        symbol: str,
        interval: str,
        month_utc: str,
    ) -> list[Candle]:
        return self._load_period(
            symbol,
            interval,
            month_utc,
            frequency="monthly",
        )

    def _period_plan(
        self,
        *,
        start_day: date,
        end_day_inclusive: date,
        today: date,
    ) -> list[tuple[str, str]]:
        periods: list[tuple[str, str]] = []
        cursor = _month_start(start_day)
        current_month = _month_start(today)

        while cursor < current_month and cursor <= end_day_inclusive:
            periods.append(("monthly", cursor.strftime("%Y-%m")))
            cursor = _next_month(cursor)

        daily_cursor = max(start_day, current_month)
        while daily_cursor <= end_day_inclusive:
            periods.append(("daily", daily_cursor.isoformat()))
            daily_cursor += timedelta(days=1)

        return periods

    def klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int,
        end_ms: int,
        now_ms: int,
    ) -> list[Candle]:
        if interval not in _INTERVAL_STEP_MS:
            raise EMA6HRegimeSourceError(
                f"unsupported archive interval: {interval}"
            )
        if end_ms <= start_ms:
            return []

        today = datetime.fromtimestamp(
            now_ms / 1000.0,
            tz=timezone.utc,
        ).date()
        today_start_ms = int(
            datetime(
                today.year,
                today.month,
                today.day,
                tzinfo=timezone.utc,
            ).timestamp()
            * 1000
        )

        # T+1 only. Never truncate a requested range silently.
        if end_ms > today_start_ms:
            raise EMA6HRegimeSourceError(
                "archive recovery range includes non-T+1 data"
            )

        start_day = datetime.fromtimestamp(
            start_ms / 1000.0,
            tz=timezone.utc,
        ).date()
        end_day_inclusive = datetime.fromtimestamp(
            (end_ms - 1) / 1000.0,
            tz=timezone.utc,
        ).date()

        self.last_receipts = []
        rows_by_open: dict[int, Candle] = {}
        for frequency, period in self._period_plan(
            start_day=start_day,
            end_day_inclusive=end_day_inclusive,
            today=today,
        ):
            source_rows = self._load_period(
                symbol,
                interval,
                period,
                frequency=frequency,
            )
            for candle in source_rows:
                if (
                    start_ms <= candle.open_time < end_ms
                    and candle.close_time < now_ms
                ):
                    prior = rows_by_open.get(candle.open_time)
                    if prior is not None and prior != candle:
                        raise EMA6HRegimeSourceError(
                            "archive overlap divergence"
                        )
                    rows_by_open[candle.open_time] = candle

        rows = [
            rows_by_open[key]
            for key in sorted(rows_by_open)
        ]
        step = _INTERVAL_STEP_MS[interval]
        aligned_start = start_ms - (start_ms % step)
        if aligned_start < start_ms:
            aligned_start += step
        expected_open_times = list(
            range(aligned_start, end_ms, step)
        )
        actual_open_times = [row.open_time for row in rows]
        if actual_open_times != expected_open_times:
            missing = sorted(
                set(expected_open_times) - set(actual_open_times)
            )
            raise EMA6HRegimeSourceError(
                "archive recovery incomplete range"
                + (
                    f": first_missing_open_ms={missing[0]}"
                    if missing
                    else ""
                )
            )
        if rows:
            validate_regular(rows, step)
        return rows


# Backward-compatible name retained for already frozen tests/receipts.
BinanceOfficialDailyKlineArchive = BinanceOfficialKlineArchiveRecovery
