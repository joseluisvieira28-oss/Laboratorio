import tempfile
import unittest
from unittest.mock import patch
from engine.three_convex_v05.signals import Bar,MS5,Halt
from engine.three_convex_v07.feed import FeedHalt
from engine.three_convex_v12.lanes import LANES,EXPECTED_V07,EXPECTED_V11,MAX_TOTAL_LANES,decide,message_for_signal
from engine.three_convex_v12.public_feed import fetch
from engine.three_convex_v12.watcher import Outbox,cycle,SingleInstance,AlreadyRunning

def fake_parent(rows):
    return [False]*(len(rows)-1)+[True],[{"score":3} for _ in rows]

class V12Tests(unittest.TestCase):
    def bars(self,n=48*260+96):
        return [Bar(i*MS5,100.,101.,99.,100.,20.) for i in range(n)]
    def signal(self,lane,close=300000):
        return {"lane":lane,"symbol":LANES[lane][0],
                "signal_close_ms":close,"signal_id":f"{lane}:{close}",
                "category":"V12_HISTORICAL_ONLY_EXPERIMENTAL"}
    def test_final_inventory_ten_no_growth(self):
        self.assertEqual(len(LANES),4)
        self.assertEqual(len(set(LANES)|EXPECTED_V07|EXPECTED_V11),MAX_TOTAL_LANES)
        self.assertEqual(set(LANES),{
            "BNB_CONVEX_NATIVE_5M_EXPERIMENTAL",
            "SOL_CONVEX_30M_EXPERIMENTAL",
            "BNB_CONVEX_15M_EXPERIMENTAL",
            "DOGE_CONVEX_4H_EXPERIMENTAL"})
    def test_all_four_signal_causal_parent_function(self):
        bars=self.bars()
        end=len(bars)*MS5
        with patch("engine.three_convex_v12.lanes.parent_signal_function",return_value=fake_parent):
            observed=[]
            for asset in ("BNB_USDT","SOL_USDT","DOGE_USDT"):
                observed.extend(decide(asset,bars,end+2000,end-10000))
        self.assertEqual(set(s["lane"] for s in observed),set(LANES))
        self.assertTrue(all(s["not_order"] and s["economic_edge_proven"] is False for s in observed))
    def test_no_replay_and_no_partial_tf(self):
        bars=self.bars()
        end=len(bars)*MS5
        with patch("engine.three_convex_v12.lanes.parent_signal_function",return_value=fake_parent):
            self.assertEqual(decide("SOL_USDT",bars,end+2000,end+3000),[])
            self.assertEqual(decide("DOGE_USDT",bars,end+2000,end+3000),[])
            self.assertEqual(decide("SOL_USDT",bars[:-1],end+2000,0),[])
    def test_bad_bar_rejected(self):
        bars=self.bars()
        end=len(bars)*MS5
        with self.assertRaises(Halt):decide("BNB_USDT",bars,end,0)
        bars[6]=Bar(bars[6].t+MS5,100,101,99,100,20)
        with self.assertRaises(Halt):decide("BNB_USDT",bars,end+2000,0)
    def test_message_identity_and_warning(self):
        with self.assertRaises(Halt):message_for_signal({"lane":"SOL_CONVEX_30M_EXPERIMENTAL","symbol":"DOGE_USDT"})
        s=self.signal("DOGE_CONVEX_4H_EXPERIMENTAL")
        message=message_for_signal(s)
        self.assertIn("NÃO É ORDEM",message)
        self.assertIn("NÃO CONTAR COMO TRADES INDEPENDENTES",message)
        self.assertIn("OOS/forward/edge líquido NÃO COMPROVADOS",message)
    def test_sqlite_duplicates_persistence_and_expired(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            s=self.signal("BNB_CONVEX_15M_EXPERIMENTAL",300000)
            q.enqueue(s);q.enqueue(s)
            self.assertEqual(q.pending(),1)
            q.close()
            q=Outbox(d)
            delivered=[]
            self.assertEqual(q.drain(delivered.append,301000),(1,0))
            self.assertEqual(q.drain(delivered.append,301000),(0,0))
            self.assertEqual(len(delivered),1)
            old=self.signal("BNB_CONVEX_NATIVE_5M_EXPERIMENTAL",300000)
            q.enqueue(old)
            self.assertEqual(q.drain(delivered.append,700000),(0,1))
            self.assertEqual(q.pending(),0)
            q.close()
    def test_failed_send_does_not_ack_and_expires(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            q.enqueue(self.signal("SOL_CONVEX_30M_EXPERIMENTAL"))
            def fail(_):raise RuntimeError("fake telegram outage")
            with self.assertRaises(RuntimeError):q.drain(fail,301000)
            self.assertEqual(q.pending(),1)
            self.assertEqual(q.drain(lambda _:None,700000),(0,1))
            q.close()
    def test_unexpected_lane_never_queued(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            with self.assertRaises(Halt):q.enqueue({"lane":"EXTRA_11TH_LANE","category":"V12_HISTORICAL_ONLY_EXPERIMENTAL"})
            q.close()
    def test_partial_source_outage_keeps_good_signals_and_pending(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            q.enqueue(self.signal("BNB_CONVEX_15M_EXPERIMENTAL",300000))
            sent=[]
            def f(asset,_,__):
                if asset=="DOGE_USDT":raise FeedHalt("simulated DOGE downtime")
                return []
            def decide_mock(symbol,bars,now,activation):
                if symbol=="SOL_USDT":
                    return [self.signal("SOL_CONVEX_30M_EXPERIMENTAL",300000)]
                return []
            with patch("engine.three_convex_v12.watcher.decide",side_effect=decide_mock):
                report=cycle(q,sent.append,now_ms=302000,server_ms=302000,market_fetch=f)
            self.assertEqual(report["status"],"V12_DEGRADED_READONLY")
            self.assertFalse(report["sources_ok"])
            self.assertEqual(report["source_status"]["DOGE_USDT"],"BLOCKED:FeedHalt")
            self.assertEqual(report["telegram_sent_this_cycle"],2)
            self.assertEqual(q.pending(),0)
            self.assertEqual(len(sent),2)
            q.close()
    def test_slow_collection_rechecked_clock_expires_stale_signal(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            sent=[]
            with patch("engine.three_convex_v12.watcher.decide",return_value=[
                self.signal("BNB_CONVEX_15M_EXPERIMENTAL",300000)
            ]):
                report=cycle(q,sent.append,now_ms=302000,server_ms=302000,
                    market_fetch=lambda *a: [],fresh_clock=lambda:700000)
            self.assertEqual(report["telegram_sent_this_cycle"],0)
            self.assertGreater(report["stale_signals_suppressed_this_cycle"],0)
            self.assertEqual(sent,[])
            q.close()
    def test_clock_offset_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            with self.assertRaises(FeedHalt):
                cycle(q,lambda _:None,now_ms=300000,server_ms=400000)
            q.close()
    def test_single_instance_lock(self):
        with tempfile.TemporaryDirectory() as d:
            path=d+"/v12.lock"
            with SingleInstance(path):
                with self.assertRaises(AlreadyRunning):
                    with SingleInstance(path):pass
            with SingleInstance(path):pass
    def test_public_doge_pages_and_cached_result(self):
        with tempfile.TemporaryDirectory() as d:
            import engine.three_convex_v12.public_feed as feed
            calls=[]
            def fake_public(path,params):
                calls.append((path,params["symbol"]))
                first=params["startTime"]
                return [[first+i*MS5,"100","101","99","100","20",first+(i+1)*MS5-1] for i in range(params["limit"])]
            now=20*MS5+10000
            with patch.object(feed,"LOOKBACK",3):
                bars=fetch("DOGE_USDT",now,d,public=fake_public)
                self.assertEqual(len(bars),3)
                self.assertEqual(calls[0][1],"DOGEUSDT")
                calls.clear()
                again=fetch("DOGE_USDT",now,d,public=fake_public)
                self.assertEqual(len(again),3)
                self.assertEqual(calls,[])
    def test_source_truncated_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            import engine.three_convex_v12.public_feed as feed
            with patch.object(feed,"LOOKBACK",3):
                with self.assertRaises(FeedHalt):
                    fetch("DOGE_USDT",20*MS5+10000,d,public=lambda *a,**k:[])

if __name__=="__main__":unittest.main()
