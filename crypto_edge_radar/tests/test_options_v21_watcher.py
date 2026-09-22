import math
import os
import tempfile
import unittest
from datetime import date, datetime, timezone

from radar.evidence import EvidenceStore
from radar.options_v21_live import DAY_MS, DailyBar, OptionTrade
from radar.options_v21_watcher import OptionsV21ForwardShadowWatcher


class StubOptions:
    provider="DERIBIT_STUB"
    last_invalid_iv_index_rows=0
    def trades(self, *, start_ms, end_ms):
        day=datetime.fromtimestamp(start_ms/1000,tz=timezone.utc).date()
        ts=start_ms+1000
        rows=[]
        for i,iv in enumerate([50,52,54,56,58]):
            rows.append(OptionTrade(f"c-{day}-{i}",ts+i,f"BTC-30OCT26-{95000+i*1000}-C",iv,90000.0))
        for i,iv in enumerate([40,42,44,46,48]):
            rows.append(OptionTrade(f"p-{day}-{i}",ts+100+i,f"BTC-30OCT26-{75000+i*1500}-P",iv,90000.0))
        return rows


class StubBTC:
    provider="BINANCE_STUB"
    def __init__(self):
        self.start_ms=int(datetime(2021,4,1,tzinfo=timezone.utc).timestamp()*1000)
        self.bars=[]
        price=100.0
        for i in range(2200):
            op=price
            r=0.002+((i%7)-3)*0.0003
            price*=math.exp(r)
            self.bars.append(DailyBar(self.start_ms+i*DAY_MS,op,price))

    def daily(self, *, start_day, end_day_exclusive):
        s=int(datetime(start_day.year,start_day.month,start_day.day,tzinfo=timezone.utc).timestamp()*1000)
        e=int(datetime(end_day_exclusive.year,end_day_exclusive.month,end_day_exclusive.day,tzinfo=timezone.utc).timestamp()*1000)
        return [b for b in self.bars if s<=b.open_time<e]

    def _get_json(self, query):
        target=int(query["startTime"])
        row=next((b for b in self.bars if b.open_time==target),None)
        if row is None:
            return []
        return [[row.open_time,str(row.open),"0","0",str(row.close),"0",row.open_time+DAY_MS-1]]


class OptionsV21WatcherTests(unittest.TestCase):
    def test_source_quality_counter_is_persisted_without_changing_signal(self):
        class QualityStubOptions(StubOptions):
            def trades(self, *, start_ms, end_ms):
                rows=super().trades(start_ms=start_ms,end_ms=end_ms)
                self.last_invalid_iv_index_rows=2
                return rows

        with tempfile.TemporaryDirectory() as tmp:
            store=EvidenceStore(os.path.join(tmp,"e.sqlite3"))
            w=OptionsV21ForwardShadowWatcher(store=store,options_feed=QualityStubOptions(),btc_feed=StubBTC())
            now=int(datetime(2026,9,20,1,tzinfo=timezone.utc).timestamp()*1000)
            result=w.run_once(now_ms=now)
            self.assertEqual(result["invalid_iv_index_rows_rejected_this_run"],2)
            days=store.read_payloads("OPTIONS_V21_FORWARD_SIGNAL_DAY")
            self.assertEqual(len(days),1)
            self.assertEqual(days[0]["source_quality"]["invalid_iv_index_rows_rejected"],2)
            self.assertTrue(days[0]["signal"]["valid"])

    def test_waits_before_first_full_postfreeze_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=EvidenceStore(os.path.join(tmp,"e.sqlite3"))
            w=OptionsV21ForwardShadowWatcher(store=store,options_feed=StubOptions(),btc_feed=StubBTC())
            now=int(datetime(2026,9,19,12,tzinfo=timezone.utc).timestamp()*1000)
            r=w.run_once(now_ms=now)
            self.assertEqual(r["status"],"WAITING_FIRST_FULL_POST_FREEZE_SIGNAL_DAY")

    def test_signal_entry_resolution_and_replay_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=EvidenceStore(os.path.join(tmp,"e.sqlite3"))
            w=OptionsV21ForwardShadowWatcher(store=store,options_feed=StubOptions(),btc_feed=StubBTC())
            now=int(datetime(2026,9,21,1,tzinfo=timezone.utc).timestamp()*1000)
            first=w.run_once(now_ms=now)
            self.assertEqual(first["status"],"OK")
            self.assertGreaterEqual(first["inserted_signal_days"],1)
            self.assertGreaterEqual(first["inserted_entries"],1)
            self.assertGreaterEqual(first["inserted_resolutions"],1)
            resolutions=store.read_payloads("OPTIONS_V21_FORWARD_RESOLUTION")
            self.assertGreaterEqual(len(resolutions),1)
            x=resolutions[0]
            self.assertIn("base_net_bps",x)
            self.assertIn("stress_net_bps",x)
            self.assertGreater(x["weight"],0)
            second=w.run_once(now_ms=now)
            self.assertEqual(second["inserted_signal_days"],0)
            self.assertEqual(second["inserted_entries"],0)
            self.assertEqual(second["inserted_resolutions"],0)
            self.assertEqual(
                len(store.read_payloads("OPTIONS_V21_FORWARD_RESOLUTION")),
                len(resolutions),
            )


if __name__=="__main__":
    unittest.main()
