import json
import os
import tempfile
import unittest
from pathlib import Path

from radar.bnb_local import BNBLocalFastMonitor, normalized_bnb_local_interval


class FakeWatcher:
    def run_once(self, *, now_ms):
        return {
            "watcher_id":"BNB-LAUNCHPOOL-DEMAND-001-FORWARD-SHADOW-V3",
            "status":"OK",
            "eligible_events_visible":0,
            "clusters_visible":0,
            "inserted_events":0,
            "authenticated_exchange_api_used":False,
            "order_created":False,
            "exchange_mutation_performed":False,
        }


class BNBLocalFastMonitorTests(unittest.TestCase):
    def test_interval_floor_is_30_seconds(self):
        self.assertEqual(normalized_bnb_local_interval(1),30.0)
        self.assertEqual(normalized_bnb_local_interval(30),30.0)
        self.assertEqual(normalized_bnb_local_interval(45),45.0)
        with self.assertRaises(ValueError):
            normalized_bnb_local_interval(0)

    def test_cycle_is_public_only_and_writes_status(self):
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,"bnb_status.json")
            monitor=BNBLocalFastMonitor(FakeWatcher(),path,30)
            out=monitor.run_cycle(now_ms=1789720000000)
            self.assertEqual(out["status"],"OK")
            self.assertEqual(out["poll_interval_seconds"],30.0)
            self.assertFalse(out["authenticated_exchange_api_used"])
            self.assertFalse(out["orders_created"])
            self.assertFalse(out["exchange_mutation_performed"])
            self.assertFalse(out["live_capital_enabled"])
            self.assertFalse(out["micro_live_execution_enabled"])
            saved=json.loads(Path(path).read_text())
            self.assertEqual(saved["watcher_id"],"BNB-LAUNCHPOOL-DEMAND-001-FORWARD-SHADOW-V3")


if __name__=="__main__":
    unittest.main()
