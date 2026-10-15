import unittest
from tempfile import TemporaryDirectory
from engine.three_convex_v08.order_ledger import DurableLedger,SignalIntent,LedgerHalt
from engine.three_convex_v08.synthetic_execution import FakeMEXC,simulate_protected_open,SimHalt

def sig(lane="SOL_CONVEX_NATIVE_5M",t=1000000):
    return SignalIntent(lane,lane+":"+str(t),t,t+5000)

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.t=TemporaryDirectory();self.db=DurableLedger(self.t.name)
    def tearDown(self):
        self.db.close();self.t.cleanup()
    def test_same_signal_rejected(self):
        self.db.reserve(sig())
        with self.assertRaisesRegex(LedgerHalt,"DUPLICATE"):
            self.db.reserve(sig())
    def test_sol_5m_1h_physical_slot_conflict(self):
        self.db.reserve(sig())
        with self.assertRaisesRegex(LedgerHalt,"PHYSICAL_SYMBOL"):
            self.db.reserve(sig("SOL_CONVEX_1H"))
    def test_bnb_parallel_possible(self):
        self.db.reserve(sig());self.db.reserve(sig("BNB_CONVEX_4H"))
        self.assertEqual(len(self.db.summary()["active"]),2)
    def test_freshness_guard(self):
        with self.assertRaisesRegex(LedgerHalt,"STALE"):
            SignalIntent("BNB_CONVEX_4H","BNB_CONVEX_4H:123",100,200000)
    def test_no_short_authority(self):
        with self.assertRaisesRegex(LedgerHalt,"UNAUTHORIZED"):
            SignalIntent("SOL_CONVEX_1H","SOL_CONVEX_1H:123",100,100,"SHORT")
    def test_invalid_transition_blocked(self):
        oid=self.db.reserve(sig())
        with self.assertRaisesRegex(LedgerHalt,"ILLEGAL_TRANSITION"):
            self.db.advance(oid,"PROTECTED",1010000)
    def test_restart_unknown_no_retry(self):
        oid=self.db.reserve(sig())
        self.db.advance(oid,"ENTRY_SUBMIT_UNKNOWN",1010000)
        self.db.close();self.db=DurableLedger(self.t.name)
        self.assertTrue(self.db.summary()["restart_requires_broker_reconciliation"])
        with self.assertRaisesRegex(LedgerHalt,"PHYSICAL_SYMBOL"):
            self.db.reserve(sig("SOL_CONVEX_1H"))
    def test_no_protected_without_stop_readback(self):
        oid=self.db.reserve(sig())
        self.db.advance(oid,"ENTRY_SUBMIT_UNKNOWN",1010000)
        self.db.advance(oid,"ENTRY_ACK",1010001,order_id="9001")
        self.db.advance(oid,"FILLED_UNPROTECTED",1010002,position_id="1234")
        self.db.advance(oid,"STOP_SUBMIT_UNKNOWN",1010003)
        self.db.advance(oid,"STOP_ACK",1010004,stop_id="7777")
        with self.assertRaisesRegex(LedgerHalt,"NATIVE_STOP_READBACK"):
            self.db.advance(oid,"PROTECTED",1010005,evidence={})
    def test_close_needs_broker_flat_reads(self):
        oid=self.db.reserve(sig())
        self.db.advance(oid,"HALTED",1010000)
        with self.assertRaisesRegex(LedgerHalt,"TWO_BROKER"):
            self.db.advance(oid,"CLOSED",1010001,evidence={})
        self.db.advance(oid,"CLOSED",1010002,evidence={"independent_broker_flat_reads":2})
        self.assertFalse(self.db.summary()["restart_requires_broker_reconciliation"])
    def test_synthetic_protected_sol(self):
        result=simulate_protected_open(broker=FakeMEXC(),ledger=self.db,signal=sig())
        self.assertEqual(result["status"],"SYNTHETIC_NATIVE_STOP_RECONCILIATION_PASS")
        self.assertEqual(self.db.summary()["active"][0]["state"],"PROTECTED")
    def test_synthetic_protected_bnb(self):
        result=simulate_protected_open(broker=FakeMEXC(),ledger=self.db,signal=sig("BNB_CONVEX_4H"))
        self.assertEqual(result["status"],"SYNTHETIC_NATIVE_STOP_RECONCILIATION_PASS")
    def test_stop_qty_lag_blocks(self):
        result=simulate_protected_open(broker=FakeMEXC(quantity_lag=True),ledger=self.db,signal=sig())
        self.assertEqual(result["status"],"SYNTHETIC_FLOW_HARD_HALT")
    def test_unknown_submit_blocks(self):
        result=simulate_protected_open(broker=FakeMEXC(fail_at="entry"),ledger=self.db,signal=sig())
        self.assertEqual(result["status"],"SYNTHETIC_FLOW_HARD_HALT")
        self.assertFalse(result["blind_resend"])
    def test_unknown_stop_blocks(self):
        result=simulate_protected_open(broker=FakeMEXC(fail_at="stop"),ledger=self.db,signal=sig())
        self.assertEqual(result["status"],"SYNTHETIC_FLOW_HARD_HALT")
    def test_real_transport_cannot_inject(self):
        class No:
            pass
        with self.assertRaisesRegex(SimHalt,"REAL_BROKER"):
            simulate_protected_open(broker=No(),ledger=self.db,signal=sig())
if __name__=="__main__":unittest.main()
