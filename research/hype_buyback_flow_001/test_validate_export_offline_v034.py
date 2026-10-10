import csv
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SOURCE=Path(__file__).with_name("validate_export_offline_v034.py")
spec=importlib.util.spec_from_file_location("validate_export_offline_v034", SOURCE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ImportIntegrity(unittest.TestCase):
    def test_csv_no_strong_trade_id_never_claims_source_pass(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"AF.csv"
            p.write_text(
                "time,coin,dir,px,sz,hash\n"
                "2026-09-20T12:00:00Z,@107,Buy,80,5,0xabc\n", encoding="utf-8")
            r=m.audit_file(p)
            self.assertEqual(r["missing_tid"],1)
            self.assertEqual(r["eligible_af_hype_buy_rows"],0)
            self.assertFalse(r["SOURCE_PASS"])

    def test_duplicate_same_trade_is_quarantined_and_wallet_checked(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"AF.csv"
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["time","coin","side","px","sz","tid","hash","wallet"])
                w.writeheader()
                row={"time":"2026-09-20T12:00:00Z","coin":"@107","side":"B",
                     "px":"80","sz":"5","tid":"123","hash":"0xabc","wallet":m.AF}
                w.writerow(row)
                w.writerow(row)
                w.writerow(dict(row,coin="@108"))
            r=m.audit_file(p)
            self.assertEqual(r["eligible_af_hype_buy_rows"],1)
            self.assertEqual(r["duplicate_strong_id"],1)
            self.assertEqual(r["wrong_coin"],1)
            self.assertTrue(r["source_wallet_proven_from_file"])
            self.assertEqual(r["total_usdc"],"400")
            self.assertFalse(r["SOURCE_PASS"])

    def test_no_trading_metrics_or_future_price_reads(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"AF.csv"
            p.write_text("time,coin,side,px,sz,tid,hash\n",encoding="utf-8")
            r=m.audit_file(p)
            self.assertEqual(r["record_count"],0)
            self.assertFalse(r["SOURCE_PASS"])
            self.assertEqual(r["active_days_in_range"],0)
            self.assertNotIn("return",r)
            self.assertNotIn("pnl",r)

if __name__=="__main__":
    unittest.main()
