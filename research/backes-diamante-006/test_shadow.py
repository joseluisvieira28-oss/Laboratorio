import datetime as dt
import unittest
import shadow as sh

class FrozenFutureGates(unittest.TestCase):
    def test_cannot_backfill_prospective(self):
        utc=dt.timezone.utc
        sh.validate_mode("preflight","2026-11-23",dt.datetime(2026,11,24,9,30,tzinfo=utc))
        sh.validate_mode("prospective","2026-11-30",dt.datetime(2026,11,30,0,30,tzinfo=utc))
        for date,clock in [
            ("2026-11-23",dt.datetime(2026,11,23,0,30,tzinfo=utc)),
            ("2026-11-30",dt.datetime(2026,11,29,23,59,tzinfo=utc)),
            ("2026-11-30",dt.datetime(2026,11,30,6,0,tzinfo=utc)),
            ("2026-11-30",dt.datetime(2026,12,1,0,30,tzinfo=utc)),
            ("2026-12-01",dt.datetime(2026,12,1,0,30,tzinfo=utc))]:
            with self.assertRaises(ValueError):
                sh.validate_mode("prospective",date,clock)
    def test_004_archive_bytes_and_completed_week(self):
        d=sh.load_history()
        self.assertEqual(set(d),{"Coinbase","Binance"})
        for v in d:
            self.assertEqual(len(d[v]["BTC"]),464)
            self.assertEqual(d[v]["BTC"][-1]["date"],"2026-11-16")
            calc=sh.calculate(d[v],dt.date(2026,11,23))
            self.assertEqual(calc["last_complete_week"],"2026-11-16")
            self.assertEqual(calc["n_completed_weeks"],464)
    def test_backward_parity_with_frozen_005_for_many_weeks(self):
        data=sh.load_history()
        for venue,full in data.items():
            policies=sh.p.b004.positions(full)
            for i in (41,55,101,250,320,463):
                past={k:v[:i] for k,v in full.items()}
                date=dt.date.fromisoformat(full["BTC"][i]["date"])
                decision=sh.calculate(past,date)
                self.assertEqual(decision["BTC_TREND40"],sh.p.trend40(full,i))
                for model in sh.MODELS:
                    expected=sh.p.alloc(full,policies,model,i)
                    actual=(decision["models"][model]["target_weight_BTC"],
                            decision["models"][model]["target_weight_ETH"])
                    for a,b in zip(actual,expected):
                        self.assertAlmostEqual(a,b,places=12)
                    self.assertAlmostEqual(sum(actual)+decision["models"][model]["target_weight_CASH"],1.,12)
    def test_bad_data_cannot_hide_bad_candles(self):
        sh.validate_daily(1,2,0.5,1.5)
        for row in ((1,0.99,.5,1.2),(1,2,1.1,1.5),(-1,2,.5,1)):
            with self.assertRaises(ValueError):sh.validate_daily(*row)
    def test_no_relabelled_old_source_as_new_prospective(self):
        data=sh.load_history()
        receipts=[]
        x=sh.extend("Binance",data["Binance"],dt.date(2026,11,23),receipts)
        self.assertEqual(x,data["Binance"])
        self.assertEqual(len(receipts),0)
        with self.assertRaises(ValueError):
            sh.extend("Binance",data["Binance"],dt.date(2026,11,24),receipts)
if __name__=="__main__":unittest.main()
