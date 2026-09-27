import unittest
from research.microstructure_scalping.partition_guard_v01 import authorize_date


class PartitionGuardTests(unittest.TestCase):
    def test_discovery(self):
        self.assertTrue(authorize_date("2024-06-01","DISCOVERY"))

    def test_oos(self):
        self.assertTrue(authorize_date("2025-06-01","OOS"))

    def test_2026_locked(self):
        with self.assertRaisesRegex(PermissionError,"PROTECTED_2026_HOLDOUT_LOCKED"):
            authorize_date("2026-01-01","DISCOVERY")

    def test_no_discovery_on_2025(self):
        with self.assertRaisesRegex(PermissionError,"DATE_OUTSIDE_DISCOVERY"):
            authorize_date("2025-01-01","DISCOVERY")


if __name__=="__main__":
    unittest.main()
