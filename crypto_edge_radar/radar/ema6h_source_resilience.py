from __future__ import annotations

import csv
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.request import Request, urlopen
import zipfile

from .strategies.ema6h_50x200_regime_forward import (
    Candle,
    EMA6HRegimeSourceError,
    _duration_ms,
    _parse_kline,
    _validate_symbol,
)

BINANCE_PUBLIC_DATA_BASE_URL = "https://data.binance.vision"
DAY_MS = 86_400_000


def latest_archive_safe_now_ms(now_ms: int) -> int:
    """Return 00:00 UTC today.

    Passing this value as watcher now time makes the frozen 15-minute
    certification rule stop at the previous UTC day's 18:00 6H boundary.
    This is intentionally conservative for Binance daily archives, which are
    documented as becoming available on the next day.
    """

    return now_ms - (now_ms % DAY_MS)


def _normalise_archive_timestamp(value: Any) -> int:
    raw = int(value)
    if abs(raw) >= 100_000_000_000_000:
        raw //= 1000
    return raw


def _normalise_archive_row(row: list[str]) -> list[Any]:
    if len(row) < 7:
        raise EMA6HRegimeSourceError("invalid Binance public-data kline row")
    out: list[Any] = list(row)
    out[0] = _normalise_archive_timestamp(out[0])
    out[6] = _normalise_archive_timestamp(out[6])
    return out


def _utc_dates_for_range(start_ms: int, end_exclusive_ms: int) -> list[str]:
    if end_exclusive_ms <= start_ms:
        return []
    first = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc).date()
    last = datetime.fromtimestamp(
        (end_exclusive_ms - 1) / 1000.0,
        tz=timezone.utc,
    ).date()
    out = []
    day = first
    while day <= last:
        out.append(day.isoformat())
        day += timedelta(days=1)
    return out


class BinanceDailyArchiveKlineFeed:
    """Official Binance daily public-data archive adapter for EMA6H.

    The adapter changes transport only. It reuses the frozen EMA6H parser and
    Candle type after normalising Binance's documented post-2025 microsecond
    timestamps to the millisecond representation used by the frozen strategy.

    It is intentionally T+1: current UTC-day data is rejected.
    """

    provider = "BINANCE_SPOT_PUBLIC_DAILY_ARCHIVE_TPLUS1"
    base_url = BINANCE_PUBLIC_DATA_BASE_URL

    def __init__(
        self,
        timeout: int = 10,
        *,
        max_workers: int = 12,
        opener=urlopen,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self.timeout = int(timeout)
        self.max_workers = int(max_workers)
        self._opener = opener
        self._cache: dict[tuple[str, str, str], tuple[Candle, ...]] = {}
        self._cycle_stats: dict[str, Any] = {}
        self.begin_cycle()

    def begin_cycle(self) -> None:
        self._cycle_stats = {
            "schema_version": "EMA6H_BINANCE_DAILY_ARCHIVE_V0.1",
            "classification": "NOT_YET_USED",
            "provider": self.provider,
            "files_requested": 0,
            "files_downloaded": 0,
            "cache_hits": 0,
            "rows_returned": 0,
            "archive_dates": [],
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
            "science_changed": False,
            "future_data_used": False,
            "payloads_exposed": False,
        }

    def transport_receipt(self) -> dict[str, Any]:
        return deepcopy(self._cycle_stats)

    def _url(self, symbol: str, interval: str, day: str) -> str:
        name = f"{symbol}-{interval}-{day}.zip"
        return (
            f"{self.base_url}/data/spot/daily/klines/"
            f"{symbol}/{interval}/{name}"
        )

    def _download_day(
        self,
        symbol: str,
        interval: str,
        day: str,
    ) -> tuple[Candle, ...]:
        key = (symbol, interval, day)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        url = self._url(symbol, interval, day)
        req = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/ema6h-archive-v0.1"},
        )
        try:
            with self._opener(req, timeout=self.timeout) as response:
                if getattr(response, "status", 200) != 200:
                    raise EMA6HRegimeSourceError(
                        f"Binance public-data HTTP {response.status}"
                    )
                body = response.read()
        except EMA6HRegimeSourceError:
            raise
        except Exception as exc:
            raise EMA6HRegimeSourceError(
                "Binance public-data archive unavailable "
                f"{symbol} {interval} {day}: {type(exc).__name__}: {exc}"
            ) from exc

        try:
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise EMA6HRegimeSourceError(
                        f"Binance public-data ZIP CRC failure: {bad_member}"
                    )
                names = [
                    name
                    for name in archive.namelist()
                    if not name.endswith("/")
                ]
                if len(names) != 1:
                    raise EMA6HRegimeSourceError(
                        "Binance public-data ZIP must contain exactly one file"
                    )
                raw = archive.read(names[0]).decode("utf-8")
        except EMA6HRegimeSourceError:
            raise
        except Exception as exc:
            raise EMA6HRegimeSourceError(
                f"invalid Binance public-data ZIP: {type(exc).__name__}: {exc}"
            ) from exc

        parsed: list[Candle] = []
        reader = csv.reader(io.StringIO(raw))
        for row in reader:
            if not row:
                continue
            if row[0].strip().lower() in {"open_time", "open time"}:
                continue
            parsed.append(_parse_kline(_normalise_archive_row(row), interval))

        if not parsed:
            raise EMA6HRegimeSourceError(
                f"empty Binance public-data archive {symbol} {interval} {day}"
            )

        rows = tuple(sorted(parsed, key=lambda candle: candle.open_time))
        self._cache[key] = rows
        return rows

    def klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int,
        end_ms: int,
        now_ms: int,
    ) -> list[Candle]:
        symbol = _validate_symbol(symbol)
        step = _duration_ms(interval)
        if start_ms >= end_ms:
            raise EMA6HRegimeSourceError("invalid kline range")

        archive_safe_now_ms = latest_archive_safe_now_ms(now_ms)
        if now_ms != archive_safe_now_ms:
            raise EMA6HRegimeSourceError(
                "archive feed requires T+1 watcher horizon at 00:00 UTC"
            )

        cursor = start_ms - (start_ms % step)
        end_exclusive = end_ms - (end_ms % step)
        if end_exclusive <= cursor:
            return []
        if end_exclusive > archive_safe_now_ms:
            raise EMA6HRegimeSourceError(
                "archive request crosses into current UTC day"
            )

        dates = _utc_dates_for_range(cursor, end_exclusive)
        self._cycle_stats["classification"] = "OFFICIAL_DAILY_ARCHIVE_ACTIVE"
        self._cycle_stats["files_requested"] += len(dates)
        self._cycle_stats["archive_dates"] = sorted(
            set(self._cycle_stats["archive_dates"]) | set(dates)
        )

        cached: dict[str, tuple[Candle, ...]] = {}
        missing: list[str] = []
        for day in dates:
            key = (symbol, interval, day)
            if key in self._cache:
                cached[day] = self._cache[key]
                self._cycle_stats["cache_hits"] += 1
            else:
                missing.append(day)

        downloaded: dict[str, tuple[Candle, ...]] = {}
        if missing:
            workers = min(self.max_workers, len(missing))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(self._download_day, symbol, interval, day): day
                    for day in missing
                }
                for future in as_completed(futures):
                    day = futures[future]
                    downloaded[day] = future.result()
                    self._cycle_stats["files_downloaded"] += 1

        rows_by_open: dict[int, Candle] = {}
        for day in dates:
            for candle in cached.get(day, downloaded.get(day, ())):
                if (
                    start_ms <= candle.open_time < end_exclusive
                    and candle.close_time < now_ms
                ):
                    rows_by_open[candle.open_time] = candle

        rows = [rows_by_open[t] for t in sorted(rows_by_open)]
        self._cycle_stats["rows_returned"] += len(rows)
        self._cycle_stats["last_request"] = {
            "symbol": symbol,
            "interval": interval,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "row_count": len(rows),
        }
        return rows
