from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import zipfile

from research.phase_b_h04_binance_offline_adapter_v01 import (
    TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT,
    adapt_h04_binance_daily_archive_bytes,
)


def _archive(symbol: str, day: str, row: str) -> tuple[str, bytes, str]:
    filename = f"{symbol}-15m-{day}.zip"
    member = filename[:-4] + ".csv"
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, row + "\n")
    raw = buf.getvalue()
    checksum = f"{sha256(raw).hexdigest()}  {filename}\n"
    return filename, raw, checksum


def test_pre_2025_spot_kline_timestamps_remain_milliseconds() -> None:
    symbol = "BTCUSDT"
    day = "2024-12-31"
    open_ms = 1735603200000
    close_ms = open_ms + 15 * 60 * 1000 - 1
    row = (
        f"{open_ms},100,101,99,100.5,10,{close_ms},1005,20,6,603,0"
    )
    filename, raw, checksum = _archive(symbol, day, row)
    result = adapt_h04_binance_daily_archive_bytes(
        symbol=symbol,
        day=day,
        archive_filename=filename,
        archive_bytes=raw,
        checksum_text=checksum,
    )
    assert result.status == "PASS_BINANCE_DAILY"
    assert result.bars[0].candle.open_time == open_ms
    assert result.bars[0].candle.close_time == close_ms


def test_2025_spot_kline_microseconds_normalize_to_milliseconds() -> None:
    symbol = "BTCUSDT"
    day = "2025-01-01"
    open_us = 1735689600000000
    close_us = open_us + 15 * 60 * 1_000_000 - 1
    row = (
        f"{open_us},100,101,99,100.5,10,{close_us},1005,20,6,603,0"
    )
    filename, raw, checksum = _archive(symbol, day, row)
    result = adapt_h04_binance_daily_archive_bytes(
        symbol=symbol,
        day=day,
        archive_filename=filename,
        archive_bytes=raw,
        checksum_text=checksum,
    )
    assert result.status == "PASS_BINANCE_DAILY"
    assert result.bars[0].candle.open_time == open_us // 1000
    assert result.bars[0].candle.close_time == open_us // 1000 + 15 * 60 * 1000 - 1
    assert result.bars[0].taker_buy_base_asset_volume == 6
    assert TIMESTAMP_UNIT_AMENDMENT_FINGERPRINT == (
        "efb5007ac77ff3d87e08f0be9012aba9deaff825557fbc489f802e3948d7602d"
    )
