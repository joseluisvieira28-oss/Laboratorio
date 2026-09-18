import os
import tempfile
import unittest

from radar.local_forward import (
    LOCAL_FORWARD_INTERVAL_SECONDS,
    LocalForwardSupervisor,
    build_local_forward_settings,
)


class FakeRuntime:
    def __init__(self, *, settings):
        self.settings=settings
        self.cycles=0
        self.loop_interval=None
    def run_cycle(self):
        self.cycles+=1
        return {"health":"OK"}
    def run_loop(self, *, interval_seconds):
        self.loop_interval=interval_seconds


class LocalForwardSupervisorTests(unittest.TestCase):
    def test_settings_are_local_isolated_and_no_postgres(self):
        with tempfile.TemporaryDirectory() as td:
            s=build_local_forward_settings(td)
            from pathlib import Path
            root = Path(td).resolve()
            self.assertTrue(Path(s.db_path).resolve().is_relative_to(root))
            self.assertTrue(Path(s.status_path).resolve().is_relative_to(root))
            self.assertTrue(Path(s.notification_path).resolve().is_relative_to(root))
            self.assertIsNone(s.database_url)
            self.assertEqual(s.provider,"mexc_futures_public")
            self.assertEqual(s.universe_mode,"core5")

    def test_supervisor_runs_initial_cycle_then_30s_loop(self):
        with tempfile.TemporaryDirectory() as td:
            sup=LocalForwardSupervisor(root=td,runtime_factory=FakeRuntime)
            sup.run_forever()
            self.assertEqual(sup.runtime.cycles,1)
            self.assertEqual(sup.runtime.loop_interval,LOCAL_FORWARD_INTERVAL_SECONDS)
            self.assertEqual(LOCAL_FORWARD_INTERVAL_SECONDS,30.0)


if __name__=="__main__":
    unittest.main()
