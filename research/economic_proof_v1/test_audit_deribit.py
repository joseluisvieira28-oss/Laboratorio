import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import audit_deribit as a


class AuditTests(unittest.TestCase):
    def test_all_actual_archives_reproduced(self):
        report = a.run()
        self.assertEqual(report["accepted_entries"], 0)
        self.assertEqual(report["observations"][0]["book_skew_ms"], 4161)
        self.assertAlmostEqual(float(report["observations"][1]["friction_pct"]), 13.959578947368406)
        self.assertAlmostEqual(float(report["observations"][2]["friction_pct"]), 17.599300611353698)
        self.assertIsNone(report["pnl"])

    def test_wrong_outer_hash(self):
        path = a.ROOT/"evidence/2026-11-05/entry-session.zip"
        with self.assertRaisesRegex(ValueError, "ARCHIVE_HASH"):
            a.audit(path, "0"*64, "2026-11-05")

    def mutate(self, change):
        path = a.ROOT/"evidence/2026-11-05/entry-session.zip"
        with zipfile.ZipFile(path) as z:
            files = {n: z.read(n) for n in z.namelist()}
        change(files)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/"altered.zip"
            with zipfile.ZipFile(target, "x") as z:
                for name, body in files.items():
                    z.writestr(name, body)
            a.audit(target, hashlib.sha256(target.read_bytes()).hexdigest(), "2026-11-05")

    def test_raw_tamper_even_rehashed_archive(self):
        with self.assertRaisesRegex(ValueError, "RAW_HASH"):
            self.mutate(lambda files: files.update({"raw/atm_put.json": b'{}'}))

    def test_forged_rejection_economics(self):
        def change(files):
            receipt = json.loads(files["raw/receipt.json"])
            receipt["structures"]["straddle"]["roundtrip_pct"] = 1
            files["raw/receipt.json"] = json.dumps(receipt).encode()
        with self.assertRaisesRegex(ValueError, "RECEIPT_ECONOMICS_roundtrip_pct"):
            self.mutate(change)


if __name__ == "__main__":
    unittest.main()
