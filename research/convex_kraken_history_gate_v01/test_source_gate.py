import json
import unittest
from research.convex_kraken_history_gate_v01.source_gate import classify,unix_utc

class SourceGateSynthetic(unittest.TestCase):
    def test_prelisting_always_ineligible(self):
        v=classify("PF_BNBUSD","spreads","2023-01-03",status=200,
            raw=json.dumps({"result":{"timestamp":[unix_utc("2023-01-03")]}}).encode())
        self.assertEqual(v["status"],"PRE_LISTING_INELIGIBLE")

    def test_valid_postlisting_source_candidate(self):
        v=classify("PF_SOLUSD","spreads","2023-01-03",status=200,
            raw=json.dumps({"result":{"timestamp":[unix_utc("2023-01-03")]}}).encode())
        self.assertEqual(v["status"],"SOURCE_DATE_COVERAGE_CANDIDATE")

    def test_future_stamp_rejected(self):
        v=classify("PF_SOLUSD","funding","2023-01-03",status=200,
            raw=json.dumps({"result":{"timestamp":[unix_utc("2025-06-03")]}}).encode())
        self.assertEqual(v["status"],"SOURCE_BLOCKED_OR_EMPTY")

    def test_empty_rejected(self):
        v=classify("PF_SOLUSD","funding","2023-01-03",status=200,
            raw=b'{"result":{"timestamp":[]}}')
        self.assertEqual(v["status"],"SOURCE_BLOCKED_OR_EMPTY")

    def test_unregistered_symbol_no_probe(self):
        with self.assertRaises(ValueError):
            classify("PF_BTCUSD","funding","2023-01-03",status=200,raw=b"{}")

    def test_http_error_failclosed(self):
        v=classify("PF_SOLUSD","spreads","2023-01-03",status=451,error="HTTP_451")
        self.assertEqual(v["status"],"SOURCE_BLOCKED_OR_EMPTY")



    def test_epoch_millis_normalizes_only_whole_seconds(self):
        v=classify("PF_SOLUSD","spreads","2023-01-03",status=200,
            raw=json.dumps({"result":{"timestamp":[unix_utc("2023-01-03")*1000]}}).encode())
        self.assertEqual(v["status"],"SOURCE_DATE_COVERAGE_CANDIDATE")

    def test_epoch_mixed_units_rejected(self):
        u=unix_utc("2023-01-03")
        v=classify("PF_SOLUSD","spreads","2023-01-03",status=200,
            raw=json.dumps({"result":{"timestamp":[u,u*1000]}}).encode())
        self.assertEqual(v["status"],"SOURCE_BLOCKED_OR_EMPTY")

    def test_noninteger_string_rejected(self):
        v=classify("PF_SOLUSD","spreads","2023-01-03",status=200,
            raw=json.dumps({"result":{"timestamp":[str(unix_utc("2023-01-03"))]}}).encode())
        self.assertEqual(v["status"],"SOURCE_BLOCKED_OR_EMPTY")

if __name__=="__main__":
    unittest.main()
