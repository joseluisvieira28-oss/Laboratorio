#!/usr/bin/env python3
"""No-network source immutable gate tests; do not invoke production capture."""
import datetime as dt
import hashlib
import tempfile
import unittest
from pathlib import Path
from guard import FIRST,LAST,PINNED,git_blob_sha,check

class GateTest(unittest.TestCase):
    def test_git_blob_known_fixture(self):
        self.assertEqual(git_blob_sha(b"test\n"),"9daeafb9864cf43055ae93beb0afd6c7d144bfa4")
    def test_public_runner_can_only_use_utc_window(self):
        self.assertEqual(FIRST.isoformat(),"2026-11-23")
        self.assertEqual(LAST.isoformat(),"2026-12-23")
    def test_pinned_originals_exactly_five(self):
        self.assertEqual(len(PINNED),5)
        self.assertIn("research/binance_diamante004/study.py",PINNED)
    def test_repo_current_check(self):
        # This CI check uses today's frozen request marker, no market reads.
        if (FIRST<=dt.datetime.now(dt.timezone.utc).date()<=LAST):
            r=check()
            self.assertTrue(r["public_repo_runner_only"])
            self.assertTrue(r["no_trades"])
    def test_guard_rejects_private_repo(self):
        with self.assertRaisesRegex(RuntimeError,"PRIVATE_REPO"):
            check(private=True)
    def test_guard_rejects_future_day(self):
        with self.assertRaisesRegex(RuntimeError,"OUTSIDE_FROZEN"):
            check(today=dt.date(2027,1,1),private=False)
    def test_blob_tamper_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            for rel in PINNED:
                p=base/rel
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(b"malicious mutation\n")
            p=base/"research/binance_diamante005/requests/2026-11-23.txt"
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text("AUTHORIZE_READONLY_ONE_CAPTURE_UTC_DAY=2026-11-23\n")
            with self.assertRaisesRegex(RuntimeError,"SOURCE_DRIFT"):
                check(today=dt.date(2026,11,23),base=base,private=False)

if __name__=="__main__":
    unittest.main()
