from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import unittest
import zipfile

from radar.ema6h_archive_recovery import BinanceOfficialDailyKlineArchive
from radar.strategies.ema6h_50x200_regime_forward import EMA6HRegimeSourceError


def make_zip(csv_text: str, name: str) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, csv_text)
    return out.getvalue()


def ms(iso: str) -> int:
    return int(
        datetime.fromisoformat(
            iso.replace("Z", "+00:00")
        ).timestamp()
        * 1000
    )


def daily_row(open_ms: int, value: float = 100.0) -> str:
    close_ms = open_ms + 86_400_000 - 1
    return (
        f"{open_ms * 1000},{value},{value + 1},{value - 1},"
        f"{value + 0.5},10.0,{close_ms * 1000},0,0,0,0,0\n"
    )


class Resp:
    status = 200

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class ArchiveRecoveryTests(unittest.TestCase):
    def fixture(self):
        name = "BTCUSDT-15m-2026-09-26.zip"
        csv_text = (
            "1790380800000000,100.0,101.0,99.0,100.5,10.0,1790381699999999,0,0,0,0,0\n"
            "1790381700000000,100.5,102.0,100.0,101.0,11.0,1790382599999999,0,0,0,0,0\n"
        )
        body = make_zip(csv_text, name.replace(".zip", ".csv"))
        checksum = f"{hashlib.sha256(body).hexdigest()}  {name}\n".encode()
        return name, body, checksum

    def test_checksum_verified_archive_normalizes_microseconds(self):
        _name, body, checksum = self.fixture()

        def opener(req, timeout):
            return Resp(
                checksum
                if req.full_url.endswith(".CHECKSUM")
                else body
            )

        archive = BinanceOfficialDailyKlineArchive(opener=opener)
        rows = archive.klines(
            "BTCUSDT",
            "15m",
            start_ms=1790380800000,
            end_ms=1790382600000,
            now_ms=1790467200000,
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].open_time, 1790380800000)
        self.assertEqual(rows[0].close_time, 1790381699999)
        self.assertTrue(archive.last_receipt.checksum_verified)
        self.assertTrue(
            archive.last_receipt.normalized_microseconds_to_milliseconds
        )

    def test_checksum_mismatch_fails_closed(self):
        _name, body, _checksum = self.fixture()
        bad = (
            "0" * 64
            + "  BTCUSDT-15m-2026-09-26.zip\n"
        ).encode()

        def opener(req, timeout):
            return Resp(
                bad
                if req.full_url.endswith(".CHECKSUM")
                else body
            )

        archive = BinanceOfficialDailyKlineArchive(opener=opener)
        with self.assertRaisesRegex(
            EMA6HRegimeSourceError,
            "CHECKSUM mismatch",
        ):
            archive.load_day(
                "BTCUSDT",
                "15m",
                "2026-09-26",
            )

    def test_same_day_archive_is_not_eligible(self):
        _name, body, checksum = self.fixture()

        def opener(req, timeout):
            return Resp(
                checksum
                if req.full_url.endswith(".CHECKSUM")
                else body
            )

        archive = BinanceOfficialDailyKlineArchive(opener=opener)
        with self.assertRaisesRegex(
            EMA6HRegimeSourceError,
            "T\+1",
        ):
            archive.klines(
                "BTCUSDT",
                "15m",
                start_ms=1790380800000,
                end_ms=1790382600000,
                now_ms=1790388000000,
            )

    def test_monthly_plus_daily_tail_reconstructs_exact_range(self):
        payloads = {}
        specs = {
            "BTCUSDT-1d-2026-08.zip": daily_row(
                ms("2026-08-31T00:00:00Z"),
                100.0,
            ),
            "BTCUSDT-1d-2026-09-01.zip": daily_row(
                ms("2026-09-01T00:00:00Z"),
                101.0,
            ),
            "BTCUSDT-1d-2026-09-02.zip": daily_row(
                ms("2026-09-02T00:00:00Z"),
                102.0,
            ),
        }
        for name, csv_text in specs.items():
            body = make_zip(
                csv_text,
                name.replace(".zip", ".csv"),
            )
            payloads[name] = body
            payloads[name + ".CHECKSUM"] = (
                f"{hashlib.sha256(body).hexdigest()}  {name}\n"
            ).encode()

        calls = []

        def opener(req, timeout):
            name = req.full_url.rsplit("/", 1)[-1]
            calls.append(name)
            return Resp(payloads[name])

        archive = BinanceOfficialDailyKlineArchive(opener=opener)
        rows = archive.klines(
            "BTCUSDT",
            "1d",
            start_ms=ms("2026-08-31T00:00:00Z"),
            end_ms=ms("2026-09-03T00:00:00Z"),
            now_ms=ms("2026-09-03T12:00:00Z"),
        )
        self.assertEqual(
            [row.open_time for row in rows],
            [
                ms("2026-08-31T00:00:00Z"),
                ms("2026-09-01T00:00:00Z"),
                ms("2026-09-02T00:00:00Z"),
            ],
        )
        self.assertIn("BTCUSDT-1d-2026-08.zip", calls)
        self.assertIn("BTCUSDT-1d-2026-09-01.zip", calls)
        self.assertIn("BTCUSDT-1d-2026-09-02.zip", calls)
        self.assertEqual(
            [receipt.frequency for receipt in archive.last_receipts],
            ["monthly", "daily", "daily"],
        )

    def test_incomplete_recovery_range_fails_closed(self):
        specs = {
            "BTCUSDT-1d-2026-08.zip": daily_row(
                ms("2026-08-31T00:00:00Z"),
                100.0,
            ),
            "BTCUSDT-1d-2026-09-01.zip": "",
            "BTCUSDT-1d-2026-09-02.zip": daily_row(
                ms("2026-09-02T00:00:00Z"),
                102.0,
            ),
        }
        payloads = {}
        for name, csv_text in specs.items():
            body = make_zip(
                csv_text,
                name.replace(".zip", ".csv"),
            )
            payloads[name] = body
            payloads[name + ".CHECKSUM"] = (
                f"{hashlib.sha256(body).hexdigest()}  {name}\n"
            ).encode()

        def opener(req, timeout):
            return Resp(
                payloads[req.full_url.rsplit("/", 1)[-1]]
            )

        archive = BinanceOfficialDailyKlineArchive(opener=opener)
        with self.assertRaisesRegex(
            EMA6HRegimeSourceError,
            "incomplete range",
        ):
            archive.klines(
                "BTCUSDT",
                "1d",
                start_ms=ms("2026-08-31T00:00:00Z"),
                end_ms=ms("2026-09-03T00:00:00Z"),
                now_ms=ms("2026-09-03T12:00:00Z"),
            )

    def test_cache_avoids_redownload_for_same_archive_period(self):
        name, body, checksum = self.fixture()
        calls = {"count": 0}

        def opener(req, timeout):
            calls["count"] += 1
            return Resp(
                checksum
                if req.full_url.endswith(".CHECKSUM")
                else body
            )

        archive = BinanceOfficialDailyKlineArchive(opener=opener)
        archive.load_day("BTCUSDT", "15m", "2026-09-26")
        archive.load_day("BTCUSDT", "15m", "2026-09-26")
        self.assertEqual(calls["count"], 2)
        self.assertEqual(
            archive.last_receipt.period_utc,
            "2026-09-26",
        )


if __name__ == "__main__":
    unittest.main()
