"""Synthetic-only, no credentials/network/exchange. Tests the actual engine."""
import copy
from decimal import Decimal
from pathlib import Path
import unittest
from unittest.mock import patch

from engine.three_convex_v05.signals import (
    Bar, Halt, MS5, PARENT_PATH, PARENT_GIT_BLOB, git_blob_sha,
    aggregate_complete, parent_signal_function, closed_signal_decisions,
)
from engine.three_convex_v05.shadow import (
    raw_market_bars, build_signal_schedule, model_one_contract,
    ShadowMotor, DisabledBroker,
)


def bars(count=12, price=100.0, symbol="SOL_USDT", *, start=0):
    return [dict(symbol=symbol, source="BINANCE_USDM_CANONICAL_5M",
                 t=start+i*MS5,open=price,high=price+1,
                 low=price-1,close=price,volume=100.0)
            for i in range(count)]


def both(count=12):
    return raw_market_bars(bars(count)+bars(count,symbol="BNB_USDT",price=730.0))


def signal(lane, symbol, close, tf=5):
    return dict(lane=lane,symbol=symbol, signal_id=f"{lane}:{close}",
                signal_close_ms=close,entry_open_ms=close+MS5,
                tf_minutes=tf,score=3)


class PinnedSource(unittest.TestCase):
    def test_parent_blob_identity_exact(self):
        self.assertEqual(git_blob_sha(PARENT_PATH.read_bytes().replace(b"\r\n",b"\n")),PARENT_GIT_BLOB)

    def test_parent_is_callable_and_requires_200_history(self):
        fn=parent_signal_function()
        raw=[dict(t=i*MS5,open=100,high=101,low=99,close=100,
                  volume=100) for i in range(210)]
        flags,details=fn(raw)
        self.assertEqual(len(flags),len(raw))
        self.assertFalse(any(flags))
        self.assertIsNone(details[0])

    def test_parent_cannot_be_swapped(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"parent.py"
            p.write_text("def build_signals(x): return [True]*len(x), []")
            with self.assertRaisesRegex(Halt,"BLOB_IDENTITY"):
                parent_signal_function(p)

    def test_open_bar_future_not_admitted(self):
        sample=[Bar(i*MS5,100,101,99,100,100) for i in range(260)]
        with self.assertRaisesRegex(Halt,"INCOMPLETE_OR_NONCAUSAL_BAR"):
            closed_signal_decisions("SOL_USDT",sample,sample[-1].t+MS5)
        self.assertEqual(closed_signal_decisions("SOL_USDT",sample,sample[-1].t+MS5+1000),[])

    def test_gap_rejected(self):
        b=[Bar(i*MS5,100,101,99,100,100) for i in (0,1,3)]
        with self.assertRaisesRegex(Halt,"GAP"):
            aggregate_complete(b,12)

    def test_4h_from_canonical_5m(self):
        b=[Bar(i*MS5,100+i%3,101+i%3,99+i%3,100+i%3,1)
           for i in range(96)]
        a=aggregate_complete(b,48)
        self.assertEqual(len(a),2)
        self.assertEqual(a[0]["t"],0)
        self.assertEqual(a[0]["volume"],48)
        self.assertEqual(a[1]["t"],48*MS5)

    def test_incomplete_4h_excluded(self):
        b=[Bar(i*MS5,100,101,99,100,1) for i in range(60)]
        self.assertEqual(len(aggregate_complete(b,48)),1)

    def test_mid_tf_initial_chunk_discarded(self):
        b=[Bar(i*MS5,100,101,99,100,1) for i in range(1,25)]
        a=aggregate_complete(b,12)
        self.assertEqual(len(a),1)
        self.assertEqual(a[0]["t"],12*MS5)


class MarketGates(unittest.TestCase):
    def test_source_must_claim_canonical(self):
        a=bars(); a[0]["source"]="MEXC_5M"
        with self.assertRaisesRegex(Halt,"CANONICAL_SOURCE"):
            raw_market_bars(a+bars(symbol="BNB_USDT"))

    def test_wrong_volume(self):
        a=bars(); a[0]["volume"]=-10
        with self.assertRaisesRegex(Halt,"NONPOSITIVE_CANDLE"):
            raw_market_bars(a+bars(symbol="BNB_USDT"))

    def test_nonfinite(self):
        a=bars(); a[0]["high"]=float("nan")
        with self.assertRaisesRegex(Halt,"NONFINITE_CANDLE"):
            raw_market_bars(a+bars(symbol="BNB_USDT"))

    def test_reorder_and_duplicate(self):
        a=bars()
        a[1],a[2]=a[2],a[1]
        with self.assertRaisesRegex(Halt,"GAP_REORDER"):
            raw_market_bars(a+bars(symbol="BNB_USDT"))
        c=bars();c.append(c[-1])
        with self.assertRaisesRegex(Halt,"GAP_REORDER"):
            raw_market_bars(c+bars(symbol="BNB_USDT"))

    def test_both_symbols_required(self):
        with self.assertRaisesRegex(Halt,"BOTH_SYMBOLS_REQUIRED"):
            raw_market_bars(bars())

    def test_no_warmup_gives_no_real_signal(self):
        motor=ShadowMotor(both(60))
        self.assertFalse(motor.schedule)
        self.assertEqual(motor.run()["opened_proxy_positions"],0)

    def test_1h_and_4h_bars_not_assumed_after_short_history(self):
        events,evidence=build_signal_schedule(both(200))
        self.assertFalse(events)
        self.assertEqual(len(evidence),3)

    def test_risk_one_contract_sol_bnb(self):
        sol=model_one_contract("SOL_USDT",104.31)
        bnb=model_one_contract("BNB_USDT",730.8)
        self.assertLess(sol["cash_risk"],Decimal("0.50"))
        self.assertLess(bnb["cash_risk"],Decimal("0.50"))
        self.assertEqual(sol["qty"],Decimal("0.1"))
        self.assertEqual(bnb["qty"],Decimal("0.01"))

    def test_risk_2x_one_contract_exceeds_budget(self):
        sol=model_one_contract("SOL_USDT",104.31)
        self.assertGreater(2*sol["cash_risk"],Decimal("0.50"))
        with self.assertRaisesRegex(Halt,"EXCEEDS_BUDGET"):
            model_one_contract("SOL_USDT",160)


class ShadowSafety(unittest.TestCase):
    def setUp(self):
        self.motor=ShadowMotor(both(10))

    def test_signal_entry_delayed_exactly_full_five_minute(self):
        s=signal("SOL_CONVEX_NATIVE_5M","SOL_USDT",MS5)
        self.motor.schedule={MS5:[s]}
        r=self.motor.run()
        entries=[e for e in self.motor.ledger if e["event"]=="PAPER_ENTRY_MODEL_NOT_ORDER"]
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0]["entry_bar_t"],2*MS5)
        self.assertEqual(r["execution_authority"],"NONE")
        self.assertFalse(r["broker_stop_ack"])

    def test_unsafe_simultaneous_sol_signals_blocked(self):
        self.motor.schedule={MS5:[
            signal("SOL_CONVEX_NATIVE_5M","SOL_USDT",MS5),
            signal("SOL_CONVEX_1H","SOL_USDT",MS5,60)]}
        r=self.motor.run()
        self.assertEqual(r["opened_proxy_positions"],0)
        self.assertEqual(r["blocked_counts"]["SAME_SYMBOL_SIMULTANEOUS_SIGNALS"],2)

    def test_one_sol_plus_bnb_allowed_in_model(self):
        self.motor.schedule={MS5:[
            signal("SOL_CONVEX_NATIVE_5M","SOL_USDT",MS5),
            signal("BNB_CONVEX_4H","BNB_USDT",MS5,240)]}
        r=self.motor.run()
        self.assertEqual(r["opened_proxy_positions"],2)
        self.assertEqual(len(r["modeled_active_positions"]),2)

    def test_second_sol_signal_blocked_while_first_active(self):
        self.motor.schedule={
            MS5:[signal("SOL_CONVEX_NATIVE_5M","SOL_USDT",MS5)],
            3*MS5:[signal("SOL_CONVEX_1H","SOL_USDT",3*MS5,60)]}
        r=self.motor.run()
        self.assertEqual(r["opened_proxy_positions"],1)
        self.assertEqual(r["blocked_counts"]["PHYSICAL_SYMBOL_ALREADY_RESERVED"],1)

    def test_stop_gap_pnl_contains_adverse_gap(self):
        data=both(10)
        # Force fourth bar to gap below the initial stop.
        a=data["SOL_USDT"]
        a[3]=Bar(3*MS5,90,91,89,90,100)
        for i in range(4,10):
            a[i]=Bar(i*MS5,90,91,89,90,100)
        self.motor=ShadowMotor(data)
        self.motor.schedule={MS5:[signal("SOL_CONVEX_NATIVE_5M","SOL_USDT",MS5)]}
        r=self.motor.run()
        self.assertEqual(r["opened_proxy_positions"],1)
        self.assertEqual(r["closed_proxy_positions"],1)
        exits=[e for e in self.motor.ledger if e["event"]=="PAPER_EXIT_MODEL"]
        self.assertEqual(exits[0]["cause"],"GAP_AT_5M_OPEN")
        self.assertLess(Decimal(exits[0]["pnl_after_model_costs"]),Decimal("-.50"))

    def test_original_nonlatched_trailing_danger_reported(self):
        from engine.three_convex_v05.shadow import PaperPosition
        p=PaperPosition(lane="SOL_CONVEX_NATIVE_5M",signal_id="s",
             symbol="SOL_USDT",contracts=1,qty=Decimal(".1"),entry_t=0,
             entry=Decimal("100"),initial_stop=Decimal("96"),
             stop=Decimal("104"),peak=Decimal("120"),
             modeled_cash_risk=Decimal(".44"),entry_fee=Decimal(".008"),
             funding_reserve=Decimal(".005"))
        self.motor.positions["SOL_USDT"]=p
        self.motor._active_symbol="SOL_USDT"
        self.motor._exit_if_hit(Bar(0,110,112,105,100,10))
        self.assertEqual(self.motor.loosen_warnings,1)
        self.assertEqual(p.stop,Decimal("96"))
        self.assertTrue(any(x["event"]=="ORIGINAL_V5_NONLATCHED_STOP_WEAKENS"
                            for x in self.motor.ledger))

    def test_no_exchange_broker_methods(self):
        with self.assertRaisesRegex(Halt,"NO_LIVE_GO"):
            DisabledBroker().submit_order("SOL_USDT")
        with self.assertRaisesRegex(Halt,"NO_LIVE_GO"):
            DisabledBroker().cancel_order("test")

    def test_receipt_hash_chain(self):
        self.motor.schedule={MS5:[signal("SOL_CONVEX_NATIVE_5M","SOL_USDT",MS5)]}
        self.motor.run()
        import hashlib,json
        parent="0"*64
        for i,receipt in enumerate(self.motor.ledger):
            self.assertEqual(receipt["seq"],i+1)
            self.assertEqual(receipt["previous_hash"],parent)
            blob={k:v for k,v in receipt.items() if k!="receipt_sha256"}
            raw=json.dumps(blob,sort_keys=True,separators=(",",":"),default=str)
            parent=hashlib.sha256(raw.encode()).hexdigest()
            self.assertEqual(receipt["receipt_sha256"],parent)

    def test_live_go_never_claimed(self):
        self.motor.schedule={}
        r=self.motor.run()
        self.assertFalse(r["trading_enabled"])
        self.assertEqual(r["status"],"OFFLINE_SHADOW_ENGINE_COMPLETE_NO_LIVE_GO")
        self.assertTrue(r["readiness"])


if __name__=="__main__":
    unittest.main()
