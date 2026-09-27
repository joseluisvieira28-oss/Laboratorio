from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import re
from typing import Any, Callable
from urllib.request import Request, urlopen
import zipfile

from .strategies.ema6h_50x200_regime_forward import Candle, EMA6HRegimeSourceError

ARCHIVE_BASE_URL = "https://data.binance.vision/data/spot/daily/klines"
_CHECKSUM_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$")


@dataclass(frozen=True)
class ArchiveReceipt:
    classification: str
    symbol: str
    interval: str
    day_utc: str
    checksum_verified: bool
    zip_sha256: str | None
    row_count: int | None
    normalized_microseconds_to_milliseconds: bool


def _archive_name(symbol: str, interval: str, day_utc: str) -> str:
    return f"{symbol.upper()}-{interval}-{day_utc}.zip"


def _archive_url(symbol: str, interval: str, day_utc: str) -> str:
    name = _archive_name(symbol, interval, day_utc)
    return f"{ARCHIVE_BASE_URL}/{symbol.upper()}/{interval}/{name}"


def _to_ms(value: str) -> tuple[int, bool]:
    n = int(value)
    if n >= 10**15:
        return n // 1000, True
    return n, False


class BinanceOfficialDailyKlineArchive:
    provider = "BINANCE_PUBLIC_DATA_DAILY_KLINES_V0.1"

    def __init__(
        self,
        *,
        timeout: int = 15,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.timeout = timeout
        self.opener = opener
        self.last_receipt: ArchiveReceipt | None = None

    def _download(self, url: str) -> bytes:
        req = Request(
            url,
            headers={"User-Agent": "crypto-edge-radar/ema6h-archive-recovery-v0.1"},
        )
        with self.opener(req, timeout=self.timeout) as response:
            if response.status != 200:
                raise EMA6HRegimeSourceError(
                    f"Binance archive HTTP {response.status}"
                )
            return response.read()

    def load_day(
        self,
        symbol: str,
        interval: str,
        day_utc: str,
    ) -> list[Candle]:
        url = _archive_url(symbol, interval, day_utc)
        name = _archive_name(symbol, interval, day_utc)
        zip_bytes = self._download(url)
        checksum_bytes = self._download(url + ".CHECKSUM")

        checksum_text = checksum_bytes.decode("utf-8").strip()
        match = _CHECKSUM_RE.match(checksum_text)
        if not match:
            raise EMA6HRegimeSourceError("invalid Binance archive CHECKSUM format")
        expected_sha, expected_name = match.groups()
        if expected_name != name:
            raise EMA6HRegimeSourceError("Binance archive CHECKSUM filename mismatch")

        actual_sha = hashlib.sha256(zip_bytes).hexdigest()
        if actual_sha.lower() != expected_sha.lower():
            raise EMA6HRegimeSourceError("Binance archive CHECKSUM mismatch")

        candles: list[Candle] = []
        normalized = False
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                members = [x for x in zf.namelist() if not x.endswith("/")]
                if len(members) != 1:
                    raise EMA6HRegimeSourceError(
                        "Binance archive must contain exactly one CSV"
                    )
                with zf.open(members[0]) as fh:
                    reader = csv.reader(
                        io.TextIOWrapper(fh, encoding="utf-8", newline="")
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
                        normalized = normalized or open_norm or close_norm
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

        candles.sort(key=lambda x: x.open_time)
        if any(
            candles[i].open_time >= candles[i + 1].open_time
            for i in range(len(candles) - 1)
        ):
            raise EMA6HRegimeSourceError(
                "Binance archive open times not strictly increasing"
            )

        self.last_receipt = ArchiveReceipt(
            classification="PASS_CHECKSUM_VERIFIED_DAILY_ARCHIVE",
            symbol=symbol.upper(),
            interval=interval,
            day_utc=day_utc,
            checksum_verified=True,
            zip_sha256=actual_sha,
            row_count=len(candles),
            normalized_microseconds_to_milliseconds=normalized,
        )
        return candles

    def klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int,
        end_ms: int,
        now_ms: int,
    ) -> list[Candle]:
        if end_ms <= start_ms:
            return []
        start_day = datetime.fromtimestamp(
            start_ms / 1000.0, tz=timezone.utc
        ).date()
        end_day = datetime.fromtimestamp(
            (end_ms - 1) / 1000.0, tz=timezone.utc
        ).date()
        if start_day != end_day:
            raise EMA6HRegimeSourceError(
                "archive recovery V0.1 supports one UTC day per request"
            )
        day_utc = start_day.isoformat()
        # Public daily archives are a T+1 recovery lane, never a same-day source.
        today = datetime.fromtimestamp(
            now_ms / 1000.0, tz=timezone.utc
        ).date()
        if start_day >= today:
            raise EMA6HRegimeSourceError(
                "daily archive not eligible before T+1"
            )
        rows = self.load_day(symbol, interval, day_utc)
        return [
            c
            for c in rows
            if c.open_time >= start_ms
            and c.open_time < end_ms
            and c.close_time < now_ms
        ]
