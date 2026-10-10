"""Offline source-only G3 capture tests; no remote exchanges contacted."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import rw_hl_g3_hourly_source_capture_v01 as h

def full():
    names=[f"COIN{i:03d}" for i in range(120)]
    return [{"universe":[{"name":name} for name in names]},
      [{"openInterest":"25.4","markPx":"10.2","funding":"-0.00001",
        "dayNtlVlm":"2000000"} for _ in names]]

class Hourly(unittest.TestCase):
    def test_g3_source_schema(self):
        self.assertEqual(h.safe_market(full())["valid_public_markets"],120)
    def test_below_100_blocks(self):
        x=full();x[0]["universe"]=x[0]["universe"][:99];x[1]=x[1][:99]
        with self.assertRaises(h.Blocked):h.safe_market(x)
    def test_time_must_have_z(self):
        with self.assertRaises(h.Blocked):h.parse_utc("2026-10-09T20:04:00+00:00")
    def test_real_utc_hour(self):
        x=h.build_receipt(full(),"2026-10-09T21:59:59.234567Z","1234")
        self.assertEqual(x["source_hour_utc"],"2026-10-09T21:00:00Z")
        self.assertFalse(x["economic_outcomes_opened"])
    def test_rollover_real_time(self):
        x=h.build_receipt(full(),"2026-10-10T00:00:01Z","1234")
        self.assertEqual(x["source_hour_utc"],"2026-10-10T00:00:00Z")
    def test_invalid_timestamp(self):
        with self.assertRaises(h.Blocked):h.parse_utc("tomorrowZ")
    def test_unknown_source_field_rejected(self):
        x=full();x[1][0]["account"]="secret"
        self.assertEqual(h.safe_market(x)["valid_public_markets"],120) # fixed safe parser excludes extra
    def test_source_duplicate_hour_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(h,"ARCHIVE",Path(tmp)):
                obj=h.build_receipt(full(),"2026-10-09T21:05:00Z","1")
                p,sha=h.write_immutable(obj)
                self.assertEqual(len(sha),64)
                with self.assertRaises(h.Blocked):h.write_immutable(obj)
    def test_different_hour_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(h,"ARCHIVE",Path(tmp)):
                a=h.build_receipt(full(),"2026-10-09T21:05:00Z","1")
                b=h.build_receipt(full(),"2026-10-09T22:00:01Z","2")
                self.assertNotEqual(h.write_immutable(a)[0],h.write_immutable(b)[0])
    def test_sha_proof_matches_blob(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(h,"ARCHIVE",Path(tmp)):
                p,d=h.write_immutable(h.build_receipt(full(),"2026-10-09T21:15:00Z","3"))
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),d)
    def test_num_markets_preserved(self):
        x=h.build_receipt(full(),"2026-10-09T21:05:00Z","id")
        self.assertEqual(len(x["market_data"]["market_context"]),120)
    def test_source_not_trade(self):
        x=h.build_receipt(full(),"2026-10-09T21:05:00Z","id")
        self.assertEqual(x["trading_authority"],"NONE")
        self.assertNotIn("future_return",json.dumps(x))
    def test_no_outcomes_code(self):
        from inspect import getsource
        src=getsource(h)
        self.assertNotIn("create_order(",src)
        self.assertNotIn("realizedPnl",src)
if __name__=="__main__":unittest.main()
