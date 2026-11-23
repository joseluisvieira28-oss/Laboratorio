import datetime as dt
import unittest
import weekly_snapshot as f

class TestForward(unittest.TestCase):
    def test_prospective_window(self):
        f.verify_target("2026-11-30",dt.datetime(2026,11,30,0,30,tzinfo=dt.timezone.utc))
        for day in [dt.datetime(2026,11,30,6,0,tzinfo=dt.timezone.utc),dt.datetime(2026,12,1,0,30,tzinfo=dt.timezone.utc)]:
            with self.assertRaises(ValueError):f.verify_target("2026-11-30",day)
        with self.assertRaises(ValueError):f.verify_target("2026-11-23",dt.datetime(2026,11,23,0,30,tzinfo=dt.timezone.utc))
    def test_closed_week_gate(self):
        day=dt.date(2026,11,30)
        start=day-dt.timedelta(weeks=53)
        rows=[]
        for i in range(54):
            d=start+dt.timedelta(weeks=i)
            ms=int(dt.datetime.combine(d,dt.time(),dt.timezone.utc).timestamp()*1000)
            rows.append([ms,"0.04","0.05","0.03","0.045","100",ms+7*86400000-1])
        got=f.weekly_closed(rows,day)
        self.assertEqual(len(got),53)
        self.assertEqual(got[-1]["date"],"2026-11-23")
        rows.pop(-2)
        with self.assertRaises(ValueError):f.weekly_closed(rows,day)
    def test_empty(self):
        with self.assertRaises(ValueError):f.weekly_closed([],dt.date(2026,11,30))
if __name__=="__main__":unittest.main()
