"""Official historical 1m mark-proxy source gate synthetic security tests."""
import csv
import hashlib
import io
import unittest
import zipfile
from unittest.mock import patch
from research.convex_sol_bnb_gates_v01 import mark_1m_proxy_sensitivity as p

class ExactVsOneMinuteSeparation(unittest.TestCase):
    def test_invalid_symbol_or_period(self):
        with self.assertRaisesRegex(ValueError,"ONLY_TWO"):
            p.get_verified_mark_minute("XRPUSDT","2024-01")
        with self.assertRaisesRegex(ValueError,"UNFROZEN_MARK_MONTH"):
            p.get_verified_mark_minute("SOLUSDT","2026-01")

    def test_publisher_sha256_and_mark_open_values(self):
        content=(f"{p.prior.START},100,101,99,100,0\n"+f"{p.prior.START+60000},102,103,101,102,0\n")
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("SOLUSDT-1m-2023-01.csv",content)
        raw=blob.getvalue()
        checksum=hashlib.sha256(raw).hexdigest().encode()+b"  SOLUSDT-1m-2023-01.zip\n"
        with patch.object(p.src,"fetch",side_effect=[raw,checksum]):
            bars,proof=p.get_verified_mark_minute("SOLUSDT","2023-01")
        self.assertEqual(bars[p.prior.START],100.)
        self.assertEqual(bars[p.prior.START+60000],102.)
        self.assertEqual(proof["sha256_zip"],checksum.decode().split()[0])
        with patch.object(p.src,"fetch",side_effect=[raw,b"0"*64]):
            with self.assertRaisesRegex(ValueError,"PUBLISHER_MARK_1M_SHA256"):
                p.get_verified_mark_minute("SOLUSDT","2023-01")

    def test_exact_mark_451_never_renamed(self):
        self.assertNotEqual(p.__doc__.find("NEVER exact settlement mark"),-1)
        self.assertEqual(len(p.MONTHS),36)

if __name__=="__main__":unittest.main()
