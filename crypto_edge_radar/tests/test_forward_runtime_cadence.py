import unittest
from datetime import datetime, timezone

from radar.forward_web import BNB_POLL_MS, DH03_RETRY_MS, _bnb_due, _dh03_due


class ForwardRuntimeCadenceTests(unittest.TestCase):
    def test_bnb_polls_immediately_then_waits_ten_minutes(self):
        now=1_000_000
        self.assertTrue(_bnb_due(now_ms=now,last_check_ms=None))
        self.assertFalse(_bnb_due(now_ms=now+BNB_POLL_MS-1,last_check_ms=now))
        self.assertTrue(_bnb_due(now_ms=now+BNB_POLL_MS,last_check_ms=now))

    def test_dh03_retries_after_six_hours_while_archive_missing(self):
        now=int(datetime(2026,9,18,8,0,tzinfo=timezone.utc).timestamp()*1000)
        state={"status":"WAITING_ARCHIVE_PUBLICATION","latest_archive_day":"2026-09-17"}
        self.assertFalse(_dh03_due(now_ms=now+DH03_RETRY_MS-1,last_check_ms=now,state=state))
        self.assertTrue(_dh03_due(now_ms=now+DH03_RETRY_MS,last_check_ms=now,state=state))

    def test_dh03_sleeps_after_yesterday_processed(self):
        now=int(datetime(2026,9,19,8,0,tzinfo=timezone.utc).timestamp()*1000)
        state={"status":"OK","latest_archive_day":"2026-09-18"}
        self.assertFalse(_dh03_due(now_ms=now+DH03_RETRY_MS*2,last_check_ms=now,state=state))

    def test_dh03_wakes_after_utc_day_changes(self):
        checked=int(datetime(2026,9,19,8,0,tzinfo=timezone.utc).timestamp()*1000)
        next_day=int(datetime(2026,9,20,8,0,tzinfo=timezone.utc).timestamp()*1000)
        state={"status":"OK","latest_archive_day":"2026-09-18"}
        self.assertTrue(_dh03_due(now_ms=next_day,last_check_ms=checked,state=state))


if __name__=="__main__":
    unittest.main()
