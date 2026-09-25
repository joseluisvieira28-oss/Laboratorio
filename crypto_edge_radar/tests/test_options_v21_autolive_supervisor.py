from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.options_v21_autolive_supervisor import (
    ARMING_ID,
    POLICY_ID,
    DayCache,
    _arm_valid,
    resolve_cycle_target,
)


class AutoLiveSupervisorTests(unittest.TestCase):
    def test_cache_survives_midnight_for_just_finished_signal_day(self):
        cache=DayCache(date(2026,9,25))
        now=datetime(2026,9,26,0,0,0,500000,tzinfo=timezone.utc)
        signal_day,target=resolve_cycle_target(now,cache)
        self.assertEqual(signal_day,date(2026,9,25))
        self.assertEqual(target,datetime(2026,9,26,0,0,0,tzinfo=timezone.utc))
        self.assertGreater((now-target).total_seconds(),0)

    def test_without_cache_targets_next_midnight(self):
        now=datetime(2026,9,25,12,0,0,tzinfo=timezone.utc)
        signal_day,target=resolve_cycle_target(now,None)
        self.assertEqual(signal_day,date(2026,9,25))
        self.assertEqual(target,datetime(2026,9,26,0,0,0,tzinfo=timezone.utc))

    def test_arm_file_is_strict_and_expiring(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"arm.json"
            path.write_text(json.dumps({
                "arming_id":ARMING_ID,
                "status":"ACTIVE",
                "policy_id":POLICY_ID,
                "candidate_id":"OPTIONS-SPOTPERP-001-V2.1",
                "allow_real_orders":True,
                "maximum_notional_usdt_equivalent":10.0,
                "expires_at_utc":"2026-10-25T00:00:00Z",
            }),encoding="utf-8")
            ok,reason=_arm_valid(path,datetime(2026,9,25,tzinfo=timezone.utc))
            self.assertTrue(ok,reason)
            ok,reason=_arm_valid(path,datetime(2026,10,25,tzinfo=timezone.utc))
            self.assertFalse(ok)
            self.assertEqual(reason,"ARMING_EXPIRED")

    def test_wrong_cap_disarms(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"arm.json"
            path.write_text(json.dumps({
                "arming_id":ARMING_ID,
                "status":"ACTIVE",
                "policy_id":POLICY_ID,
                "candidate_id":"OPTIONS-SPOTPERP-001-V2.1",
                "allow_real_orders":True,
                "maximum_notional_usdt_equivalent":11.0,
                "expires_at_utc":"2026-10-25T00:00:00Z",
            }),encoding="utf-8")
            ok,reason=_arm_valid(path,datetime(2026,9,25,tzinfo=timezone.utc))
            self.assertFalse(ok)
            self.assertEqual(reason,"ARMING_NOTIONAL_CAP_MISMATCH")


if __name__=="__main__":
    unittest.main()
