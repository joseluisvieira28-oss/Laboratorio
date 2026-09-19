import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("forward_bbo_collector_v01.py")
spec = importlib.util.spec_from_file_location("collector", MODULE_PATH)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class ForwardBBOCollectorTests(unittest.TestCase):
    def test_select_instruments_is_deterministic_and_respects_envelope(self):
        now_ms = 1_700_000_000_000
        day = 86_400_000
        instruments = [
            {"kind":"option","is_active":True,"expiration_timestamp":now_ms+30*day,"strike":100.0,"option_type":"call","instrument_name":"C100"},
            {"kind":"option","is_active":True,"expiration_timestamp":now_ms+30*day,"strike":100.0,"option_type":"put","instrument_name":"P100"},
            {"kind":"option","is_active":True,"expiration_timestamp":now_ms+30*day,"strike":130.0,"option_type":"call","instrument_name":"TOO_FAR"},
            {"kind":"option","is_active":True,"expiration_timestamp":now_ms+10*day,"strike":100.0,"option_type":"call","instrument_name":"TOO_SHORT"},
            {"kind":"option","is_active":False,"expiration_timestamp":now_ms+30*day,"strike":100.0,"option_type":"call","instrument_name":"INACTIVE"},
        ]
        got = collector.select_instruments(instruments, 100.0, now_ms)
        self.assertEqual([x["instrument_name"] for x in got], ["C100", "P100"])

    def test_first_level(self):
        self.assertEqual(collector.first_level({"bids":[[1.5, 2.0]]}, "bids"), (1.5, 2.0))
        self.assertEqual(collector.first_level({"asks":[]}, "asks"), (None, None))

    def test_append_jsonl_rejects_duplicate_hour(self):
        payload = {"snapshot_hour_utc":"2026-09-19T17:00:00+00:00","x":1}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "data.jsonl"
            collector.append_jsonl(path, payload)
            with self.assertRaises(RuntimeError):
                collector.append_jsonl(path, payload)


if __name__ == "__main__":
    unittest.main()
