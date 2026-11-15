"""Independent larger stress regressions; deterministic synthetic input only."""
import gzip
import json
import os
from pathlib import Path
import random
import tempfile
import unittest

from compressed_budget import ByteBudget


class TestLongSyntheticCaps(unittest.TestCase):
    def test_20_randomized_streams_never_exceed_compressed_cap(self):
        for seed in range(20):
            rng = random.Random(seed)
            guard = ByteBudget(
                max_compressed=250_000, max_uncompressed=2_000_000,
                reserve=24_000, max_record=50_000,
                final_record_reserve=200, sync_interval_raw=32_000,
            )
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "raw.gz"
                with gzip.open(p, "xb", compresslevel=4) as writer:
                    raw = 0
                    reason = None
                    for _ in range(100):
                        line = rng.randbytes(10_000)
                        reason = guard.decision(writer, raw, line)
                        if reason:
                            break
                        writer.write(line)
                        raw += len(line)
                    self.assertEqual(reason, "COMPRESSED_CAP")
                self.assertLess(p.stat().st_size, guard.max_compressed)

    def test_periodic_sync_preserves_compression_reasonably(self):
        rng = random.Random(20261115)
        rows = []
        for seq in range(5000):
            row = {
                "kind": "SYNTHETIC_ONLY", "seq": seq, "venue": "TEST",
                "levels": [[str(20000 + j + rng.randrange(5)), str(rng.random())]
                           for j in range(5)],
            }
            rows.append((json.dumps(row, separators=(",", ":")) + "\n").encode())
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d) / "baseline.gz"
            guarded = Path(d) / "guarded.gz"
            with gzip.open(baseline, "xb", compresslevel=4) as writer:
                for line in rows:
                    writer.write(line)
            budget = ByteBudget()
            with gzip.open(guarded, "xb", compresslevel=4) as writer:
                raw = 0
                for line in rows:
                    self.assertIsNone(budget.decision(writer, raw, line))
                    writer.write(line)
                    raw += len(line)
            self.assertLess(guarded.stat().st_size, baseline.stat().st_size * 1.15)


if __name__ == "__main__":
    unittest.main()
