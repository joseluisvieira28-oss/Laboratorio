"""Hermetic synthetic equivalence: V03 vs V03C quote parser, never market result."""
import tempfile
import unittest
from pathlib import Path
from research.convex_binance_l1_v03.test_bookticker_gate import fixture,BASE_MS,DAY
from research.convex_binance_l1_v03.bookticker_gate import last_causal_quotes
from research.convex_binance_l1_v03.streaming_v03c import (
    causal_quotes_from_zip_path,root_cause_group,MAX_ZIP_BYTES,MAX_UNZIPPED,MAX_EVENTS
)

class StreamingTechnicalContracts(unittest.TestCase):
    def compare(self,events,ts):
        binary=fixture(events)
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"one.zip"
            path.write_bytes(binary)
            a,ca=last_causal_quotes(binary,DAY,ts)
            b,cb=causal_quotes_from_zip_path(path,DAY,ts)
            self.assertEqual(a,b)
            self.assertEqual(ca,cb)
    def test_one_event_exact_old_parser_parity(self):
        self.compare([(BASE_MS+1000,"100","101","10")],[BASE_MS+1000])
    def test_first_future_event_does_not_leak(self):
        self.compare([(BASE_MS+2000,"100","101","10")],[BASE_MS+1000])
    def test_multi_signal_same_day_parity(self):
        self.compare([(BASE_MS+500,"100","101","5"),(BASE_MS+2000,"100","102","1"),
                      (BASE_MS+4500,"101","103","4")],
                     [BASE_MS+1000,BASE_MS+2500,BASE_MS+5000])
    def test_invalid_crossed_book_fail_closed(self):
        payload=fixture([(BASE_MS+1000,"102","101","1")])
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"one.zip";path.write_bytes(payload)
            with self.assertRaises(ValueError):
                causal_quotes_from_zip_path(path,DAY,[BASE_MS+2000])
    def test_exact_frozen_resource_caps(self):
        self.assertEqual((MAX_ZIP_BYTES,MAX_UNZIPPED,MAX_EVENTS),
                         (320_000_000,2_500_000_000,35_000_000))
    def test_synthetic_original_resource_reason_only(self):
        files=[{"day":f"2023-06-{i:02d}","status":"SOURCE_BLOCKED",
                "reason":"ValueError:PUBLISHER_ARCHIVE_TOO_BIG"} for i in range(1,19)]
        d={"symbol":"SOLUSDT","count":33,"trading_authority":"NONE","source_files":files}
        self.assertEqual(len(root_cause_group(d,"SOLUSDT")),18)
    def test_fail_if_source_block_reason_differs(self):
        files=[{"day":f"2023-06-{i:02d}","status":"SOURCE_BLOCKED",
                "reason":"ValueError:PUBLISHER_ARCHIVE_TOO_BIG"} for i in range(1,18)]
        files.append({"day":"2023-06-18","status":"SOURCE_BLOCKED","reason":"HTTP_451"})
        d={"symbol":"SOLUSDT","count":33,"trading_authority":"NONE","source_files":files}
        with self.assertRaises(ValueError):
            root_cause_group(d,"SOLUSDT")

if __name__=="__main__":
    unittest.main()
