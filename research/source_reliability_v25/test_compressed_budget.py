"""Offline-only synthetic tests: no APIs, accounts, or live market capture."""
import gzip
import os
import tempfile
import unittest

from compressed_budget import ByteBudget, gzip_positions


class TestSourceCaps(unittest.TestCase):
    def test_gzip_tell_is_not_physical_disk_size(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "repetitive.gz")
            with gzip.open(p, "xb", compresslevel=4) as g:
                b = b"A" * 1_000_000
                g.write(b)
                logical, physical = gzip_positions(g)
                self.assertEqual(logical, 1_000_000)
                self.assertLess(physical, 50_000)
            self.assertLess(os.stat(p).st_size, 50_000)

    def test_compressible_data_does_not_trip_compressed_cap(self):
        cap = ByteBudget(max_compressed=450_000, max_uncompressed=2_000_000,
                         reserve=40_000, max_record=100_000, final_record_reserve=100)
        with tempfile.TemporaryDirectory() as d:
            with gzip.open(os.path.join(d, "r.gz"), "xb", compresslevel=4) as g:
                raw = 0
                for _ in range(15):
                    msg = b"A" * 90_000
                    self.assertIsNone(cap.decision(g, raw, msg))
                    g.write(msg)
                    raw += len(msg)
                self.assertGreater(g.tell(), 450_000)  # old bug would stop here
                self.assertLess(g.fileobj.tell(), 10_000)

    def test_incompressible_data_trips_compressed_cap_before_write(self):
        cap = ByteBudget(max_compressed=400_000, max_uncompressed=2_000_000,
                         reserve=32_000, max_record=80_000, final_record_reserve=100)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "random.gz")
            with gzip.open(p, "xb", compresslevel=4) as g:
                raw = 0
                decision = None
                for _ in range(30):
                    msg = os.urandom(70_000)
                    decision = cap.decision(g, raw, msg)
                    if decision:
                        break
                    g.write(msg)
                    raw += len(msg)
                self.assertEqual(decision, "COMPRESSED_CAP")
                self.assertLess(g.fileobj.tell(), cap.max_compressed)
            self.assertLess(os.stat(p).st_size, cap.max_compressed)

    def test_uncompressed_cap_independent_of_compressibility(self):
        cap = ByteBudget(max_compressed=5_000_000, max_uncompressed=300_000,
                         reserve=64_000, max_record=200_000, final_record_reserve=100)
        with tempfile.TemporaryDirectory() as d:
            with gzip.open(os.path.join(d, "a.gz"), "xb", compresslevel=4) as g:
                self.assertIsNone(cap.decision(g, 0, b"A" * 180_000))
                self.assertEqual(cap.decision(g, 180_000, b"B" * 180_000), "UNCOMPRESSED_CAP")

    def test_fails_closed_if_no_compressed_cursor(self):
        class Writer:
            pass
        self.assertEqual(ByteBudget().decision(Writer(), 0, b"abc"),
                         "COMPRESSED_POSITION_UNAVAILABLE")

    def test_rejects_oversize_raw_record(self):
        class Writer:
            pass
        self.assertEqual(ByteBudget(max_record=100).decision(Writer(), 0, b"a" * 101),
                         "FRAME_SIZE_LIMIT")


if __name__ == "__main__":
    unittest.main()
