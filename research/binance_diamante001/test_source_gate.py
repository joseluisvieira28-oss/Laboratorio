"""Offline source-integrity regression tests; NO network, keys, prices, or trading."""
import datetime as dt
import hashlib
import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_gate as g

def make_archive(day=g.DAY, gap=None, duplicate=False, ms=False, bad_price=False):
    first = int(dt.datetime.combine(day, dt.time(), tzinfo=dt.timezone.utc).timestamp() * 1_000_000)
    content = []
    for i in range(1440):
        if i == gap:
            continue
        j = i - 1 if duplicate and i == 17 else i
        timestamp = (first + j * 60_000_000) // (1000 if ms else 1)
        close = "0.1" if bad_price and i == 20 else "100.0"
        content.append(f"{timestamp},100,101,99,{close},10,{timestamp},1000,5,4,400,0\n")
    buf = io.BytesIO()
    name = f"BTCUSDT-1m-{day.isoformat()}.zip"
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(name[:-4] + ".csv", "".join(content))
    data = buf.getvalue()
    checksum = (hashlib.sha256(data).hexdigest() + "  " + name + "\n").encode()
    return data, checksum

class SourceGateTests(unittest.TestCase):
    def verify(self, **kw):
        data, chk = make_archive(**kw)
        return g.verify_archive(data, chk, "BTCUSDT", g.DAY)

    def test_valid_2026_microsecond_day(self):
        receipt = self.verify()
        self.assertEqual(receipt["rows"], 1440)
        self.assertEqual(receipt["status"], "SOURCE_PASS")
        self.assertFalse(receipt["economic_edge_claimed"])

    def test_reject_gap(self):
        with self.assertRaisesRegex(ValueError, "gap|incomplete"):
            self.verify(gap=66)

    def test_reject_duplicate(self):
        with self.assertRaisesRegex(ValueError, "gap/duplicate"):
            self.verify(duplicate=True)

    def test_reject_millisecond_archive_in_2026(self):
        with self.assertRaisesRegex(ValueError, "timestamp unit"):
            self.verify(ms=True)

    def test_reject_corrupt_official_checksum(self):
        data, checksum = make_archive()
        with self.assertRaisesRegex(ValueError, "SHA256"):
            g.verify_archive(data + b"tampered", checksum, "BTCUSDT", g.DAY)

    def test_reject_wrong_checksum_filename(self):
        data, chk = make_archive()
        with self.assertRaisesRegex(ValueError, "checksum line"):
            g.verify_archive(data, chk.replace(b"BTCUSDT", b"ETHUSDT"), "BTCUSDT", g.DAY)

    def test_reject_invalid_ohlc(self):
        with self.assertRaisesRegex(ValueError, "invalid OHLC"):
            self.verify(bad_price=True)

    def test_reject_unauthorized_symbols(self):
        with self.assertRaisesRegex(ValueError, "not authorized"):
            g.url_for("DOGEUSDT", g.DAY)

    def test_public_only_host(self):
        with self.assertRaisesRegex(ValueError, "URL denied"):
            g.public_get("https://api.binance.com/api/v3/order", 100)

if __name__ == "__main__":
    unittest.main()
