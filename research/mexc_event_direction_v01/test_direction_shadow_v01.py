import hashlib
import unittest
from direction_shadow_v01 import admit, settle

H = lambda s: hashlib.sha256(s.encode()).hexdigest()
BASE = 1_800_000_000_000

def fixture():
    d = {
        "signal_id": "test-1", "signal_source_sha256": H("signal"),
        "rule_hash": H("rule"), "model_hash": H("model"),
        "model_id": "TEST_ONLY", "symbol": "BTC_USDT", "direction": "UP",
        "horizon_minutes": 10, "signal_ts_ms": BASE,
        "signal_received_ms": BASE+20, "feature_cutoff_ms": BASE-50,
        "payout_received_ms": BASE+1000, "index_received_ms": BASE+1100,
        "decision_ts_ms": BASE+1050, "decision_index": 20000,
        "payout_up": .8, "payout_down": .85,
        "payout_source_sha256": H("payout"),
        "decision_index_raw_sha256": H("index"), "product_state": "ONLINE",
        "forecast_prob_up": .59
    }
    a = {"status": "ACTIVE_PROSPECTIVE", "operator_authority": True,
         "activated_at_ms": BASE-1000, "allowed_rule_hashes": [H("rule")],
         "model_hash_by_id": {"TEST_ONLY": H("model")}}
    return d, a

class TestDirectionShadow(unittest.TestCase):
    def test_locked(self):
        d, a = fixture(); a["status"] = "SOURCE_GATE_REQUIRED"
        with self.assertRaises(ValueError): admit([d], a)

    def test_win_payout(self):
        d, a = fixture(); e = admit([d], a)[0]
        self.assertEqual(e["payout"], .8)
        ticks = [{"symbol": "BTC_USDT",
                  "server_ts_ms": e["expiry_target_ts_ms"]+100,
                  "received_ms": e["expiry_target_ts_ms"]+150,
                  "index": 20010, "raw_sha256": H("tick")}]
        rows, blocked = settle([e], ticks)
        self.assertEqual(blocked, [])
        self.assertEqual((rows[0]["outcome"], rows[0]["unit_return"]), ("WIN", .8))

    def test_lookahead(self):
        d, a = fixture(); d["feature_cutoff_ms"] = d["decision_ts_ms"]+1
        with self.assertRaises(ValueError): admit([d], a)

    def test_stale_join(self):
        d, a = fixture(); d["index_received_ms"] += 6000
        with self.assertRaises(ValueError): admit([d], a)

    def test_missing_expiry(self):
        d, a = fixture(); e = admit([d], a)[0]
        ticks = [{"symbol": "BTC_USDT",
                  "server_ts_ms": e["expiry_target_ts_ms"]+5001,
                  "received_ms": e["expiry_target_ts_ms"]+5002,
                  "index": 20010, "raw_sha256": H("tick")}]
        rows, blocked = settle([e], ticks)
        self.assertEqual(rows, [])
        self.assertEqual(blocked[0]["reason"], "BLOCKED_MISSING_EXPIRY_INDEX")

    def test_duplicates(self):
        d, a = fixture()
        with self.assertRaises(ValueError): admit([d, d], a)

    def test_nonfinite(self):
        d, a = fixture(); d["forecast_prob_up"] = float("nan")
        with self.assertRaises(ValueError): admit([d], a)

    def test_unregistered(self):
        d, a = fixture(); d["model_hash"] = H("changed")
        with self.assertRaises(ValueError): admit([d], a)

    def test_negative_ev_abstain(self):
        d, a = fixture(); d["forecast_prob_up"] = .5
        with self.assertRaises(ValueError): admit([d], a)

    def test_bad_receipt_clock(self):
        d, a = fixture(); e = admit([d], a)[0]
        ticks = [{"symbol": "BTC_USDT",
                  "server_ts_ms": e["expiry_target_ts_ms"],
                  "received_ms": e["expiry_target_ts_ms"]+10000,
                  "index": 20010, "raw_sha256": H("tick")}]
        with self.assertRaises(ValueError): settle([e], ticks)

    def test_tie(self):
        d, a = fixture(); e = admit([d], a)[0]
        ticks = [{"symbol": "BTC_USDT",
                  "server_ts_ms": e["expiry_target_ts_ms"],
                  "received_ms": e["expiry_target_ts_ms"]+10,
                  "index": 20000, "raw_sha256": H("tie")}]
        rows, _ = settle([e], ticks)
        self.assertEqual((rows[0]["outcome"], rows[0]["unit_return"]), ("TIE", 0))

if __name__ == "__main__":
    unittest.main()
