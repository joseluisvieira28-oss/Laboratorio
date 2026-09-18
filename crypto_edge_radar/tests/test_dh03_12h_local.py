import os
import tempfile
import unittest

from radar.dh03_12h_core import FREEZE_MS, FIFTEEN_MIN_MS, TWELVE_H_MS
from radar.dh03_12h_local import (
    DH03CollectorError,
    DH03MarketStore,
    DH03ShadowEngine,
    dh03_clock_preflight,
    require_dh03_clock_preflight,
)
from radar.evidence import EvidenceStore


def build_15m_history(base:int):
    rows=[]
    # 41 complete 12h buckets. First 40 capped at high=100; final closes above.
    for bucket_i in range(41):
        bucket=base+bucket_i*TWELVE_H_MS
        for j in range(48):
            t=bucket+j*FIFTEEN_MIN_MS
            if bucket_i<40:
                o=95.0; h=100.0; l=90.0; c=95.0
            else:
                o=95.0; h=102.0; l=90.0; c=95.0 if j<47 else 101.0
            rows.append((t,o,h,l,c,1.0))
    return rows


class _FakeClockFeed:
    provider="BINANCE_USDM_PUBLIC_REST"

    def __init__(self,server_ms):
        self.server_ms=server_ms

    def server_time_ms(self):
        return self.server_ms


class DH0312HLocalTests(unittest.TestCase):
    def test_dh03_clock_preflight_passes_inside_budget(self):
        ticks=iter([1000.0,1100.0])
        result=dh03_clock_preflight(
            feed=_FakeClockFeed(1050.0),
            clock_ms=lambda:next(ticks),
        )
        self.assertTrue(result["pass"])
        self.assertEqual(result["blockers"],[])
        self.assertAlmostEqual(result["server_minus_local_midpoint_ms"],0.0)
        self.assertAlmostEqual(result["request_rtt_ms"],100.0)

    def test_dh03_clock_preflight_fails_offset_and_does_not_arm(self):
        ticks=iter([1000.0,1100.0])
        result=dh03_clock_preflight(
            feed=_FakeClockFeed(2000.0),
            clock_ms=lambda:next(ticks),
        )
        self.assertFalse(result["pass"])
        self.assertIn("CLOCK_OFFSET_OUTSIDE_DH03_BUDGET",result["blockers"])
        ticks=iter([1000.0,1100.0])
        with self.assertRaises(DH03CollectorError):
            require_dh03_clock_preflight(
                feed=_FakeClockFeed(2000.0),
                clock_ms=lambda:next(ticks),
            )

    def test_dh03_clock_preflight_fails_high_rtt(self):
        ticks=iter([1000.0,2500.0])
        result=dh03_clock_preflight(
            feed=_FakeClockFeed(1750.0),
            clock_ms=lambda:next(ticks),
        )
        self.assertFalse(result["pass"])
        self.assertIn("PUBLIC_RTT_OUTSIDE_DH03_BUDGET",result["blockers"])

    def test_market_store_writes_survive_new_connection(self):
        with tempfile.TemporaryDirectory() as td:
            path=os.path.join(td,"market.sqlite3")
            first=DH03MarketStore(path)
            first.set_meta("x",{"value":1})
            first.put_15m("BTCUSDT",(0,100.0,101.0,99.0,100.5,1.0),"TEST")
            first.put_minute("BTCUSDT",(0,100.0,101.0,99.0,100.5),"TEST")
            first.put_funding("BTCUSDT",8*60*60*1000,0.0001,"TEST")
            second=DH03MarketStore(path)
            self.assertEqual(second.get_meta("x"),{"value":1})
            self.assertEqual(len(second.bars15m("BTCUSDT")),1)
            self.assertEqual(len(second.minutes_since("BTCUSDT",0)),1)
            self.assertEqual(len(second.funding_between("BTCUSDT",-1,9*60*60*1000)),1)

    def _make(self,td,activation):
        market=DH03MarketStore(os.path.join(td,"market.sqlite3"))
        evidence=EvidenceStore(os.path.join(td,"evidence.sqlite3"))
        engine=DH03ShadowEngine(market=market,evidence=evidence,activation_ms=activation)
        return market,evidence,engine

    def test_signal_entry_resolution_and_restart_are_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            base=FREEZE_MS-(FREEZE_MS%TWELVE_H_MS)+TWELVE_H_MS
            activation=base+39*TWELVE_H_MS
            market,evidence,engine=self._make(td,activation)
            history=build_15m_history(base)
            for row in history[:-1]:
                market.put_15m("BTCUSDT",row,"TEST")
            result=engine.on_closed_15m("BTCUSDT",history[-1],"TEST")
            self.assertEqual(result["status"],"SIGNAL_RECORDED")
            self.assertEqual(len(evidence.read_payloads("DH03_LOCAL_SIGNAL")),1)

            sig=evidence.read_payloads("DH03_LOCAL_SIGNAL")[0]
            entry_time=int(sig["candidate"]["signal_close_time"])
            changes=engine.on_open_1m("BTCUSDT",entry_time,100.0,"TEST")
            self.assertEqual(changes[0]["status"],"ENTRY_BOUND")
            self.assertEqual(len(evidence.read_payloads("DH03_LOCAL_ENTRY")),1)

            # Restart from the same persistent stores.
            market2,evidence2,engine2=self._make(td,activation)
            self.assertEqual(len(evidence2.read_payloads("DH03_LOCAL_SIGNAL")),1)
            self.assertEqual(len(evidence2.read_payloads("DH03_LOCAL_ENTRY")),1)

            # First closed minute holds; second hits target.
            engine2.on_closed_1m("BTCUSDT",(entry_time,100.0,101.0,99.0,100.0),"TEST")
            entry=evidence2.read_payloads("DH03_LOCAL_ENTRY")[0]["signal"]
            target=float(entry["target"])
            out=engine2.on_closed_1m(
                "BTCUSDT",
                (entry_time+60_000,100.0,target+1.0,99.0,target),
                "TEST",
            )
            self.assertTrue(any(x.get("status")=="RESOLVED" for x in out))
            self.assertEqual(len(evidence2.read_payloads("DH03_LOCAL_RESOLUTION")),1)

            # Replay cannot create a second resolution.
            engine2.on_closed_1m(
                "BTCUSDT",
                (entry_time+60_000,100.0,target+1.0,99.0,target),
                "TEST",
            )
            self.assertEqual(len(evidence2.read_payloads("DH03_LOCAL_RESOLUTION")),1)

    def test_missed_exact_entry_is_deviation_not_late_reconstruction(self):
        with tempfile.TemporaryDirectory() as td:
            base=FREEZE_MS-(FREEZE_MS%TWELVE_H_MS)+TWELVE_H_MS
            activation=base+39*TWELVE_H_MS
            market,evidence,engine=self._make(td,activation)
            history=build_15m_history(base)
            for row in history[:-1]:
                market.put_15m("ETHUSDT",row,"TEST")
            engine.on_closed_15m("ETHUSDT",history[-1],"TEST")
            sig=evidence.read_payloads("DH03_LOCAL_SIGNAL")[0]
            entry_time=int(sig["candidate"]["signal_close_time"])
            changes=engine.on_open_1m("ETHUSDT",entry_time+60_000,100.0,"TEST")
            self.assertEqual(changes[0]["reason"],"MISSED_EXACT_ENTRY_MINUTE_NO_RECONSTRUCTION")
            self.assertEqual(len(evidence.read_payloads("DH03_LOCAL_ENTRY")),0)
            self.assertEqual(len(evidence.read_payloads("DH03_LOCAL_DEVIATION")),1)

    def test_minute_gap_becomes_terminal_deviation(self):
        with tempfile.TemporaryDirectory() as td:
            base=FREEZE_MS-(FREEZE_MS%TWELVE_H_MS)+TWELVE_H_MS
            activation=base+39*TWELVE_H_MS
            market,evidence,engine=self._make(td,activation)
            history=build_15m_history(base)
            for row in history[:-1]:
                market.put_15m("SOLUSDT",row,"TEST")
            engine.on_closed_15m("SOLUSDT",history[-1],"TEST")
            sig=evidence.read_payloads("DH03_LOCAL_SIGNAL")[0]
            entry_time=int(sig["candidate"]["signal_close_time"])
            engine.on_open_1m("SOLUSDT",entry_time,100.0,"TEST")
            engine.on_closed_1m("SOLUSDT",(entry_time,100,101,99,100),"TEST")
            changes=engine.on_closed_1m("SOLUSDT",(entry_time+120_000,100,101,99,100),"TEST")
            self.assertTrue(any(x.get("reason")=="EXECUTION_PATH_UNRESOLVED_GAP" for x in changes))
            self.assertEqual(len(evidence.read_payloads("DH03_LOCAL_RESOLUTION")),0)
            self.assertEqual(len(evidence.read_payloads("DH03_LOCAL_DEVIATION")),1)

    def test_funding_settlement_is_recorded_only_when_next_timestamp_rolls(self):
        with tempfile.TemporaryDirectory() as td:
            base=FREEZE_MS-(FREEZE_MS%TWELVE_H_MS)+TWELVE_H_MS
            market,evidence,engine=self._make(td,base)
            t=base+8*60*60*1000
            self.assertIsNone(engine.on_mark_price("BTCUSDT",t-1000,t,0.0001))
            self.assertIsNone(engine.on_mark_price("BTCUSDT",t-100,t,0.00012))
            receipt=engine.on_mark_price("BTCUSDT",t+1000,t+8*60*60*1000,0.00011)
            self.assertIsNotNone(receipt)
            self.assertEqual(receipt["funding_time"],t)
            self.assertAlmostEqual(receipt["funding_rate"],0.00012)
            self.assertEqual(len(evidence.read_payloads("DH03_LOCAL_FUNDING_SETTLEMENT")),1)


if __name__=="__main__":
    unittest.main()
