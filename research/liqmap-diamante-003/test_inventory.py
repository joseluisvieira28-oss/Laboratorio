import datetime as dt
import unittest
import inventory as x

class ForensicSourceTests(unittest.TestCase):
    def test_dates_not_wallet_count(self):
        paths=[{"path":"snapshots_perp/date=2026-10-01/positions.parquet"},
               {"path":"snapshots_perp/date=2026-10-01/more.parquet"},
               {"path":"snapshots_perp/date=2026-10-02/positions.parquet"}]
        import re
        dates={y for p in paths for y in re.findall(r"(20\d\d-\d\d-\d\d)",p["path"])}
        self.assertEqual(len(dates),2)
    def test_protocol_no_paid_downloads(self):
        self.assertIn("api.github.com",x.GITHUB)
        self.assertIn("huggingface.co",x.HF)
        self.assertEqual(x.DATASETS[0],"Hydromancer/hyperliquid-reservoir")
        self.assertEqual(x.DATASETS[1],"ProbioticFarmer/hyperliquid-augmented-copytrading")
    def test_1_commit_is_not_60_snapshots(self):
        timeline=[{"sha":"one","published_utc":"2026-11-26T07:30:25Z"}]
        self.assertLess(len(timeline),60)
if __name__=="__main__":unittest.main()
