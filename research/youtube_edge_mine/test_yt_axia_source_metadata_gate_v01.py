"""Synthetic regressions for metadata-only source probe. NO market data."""
import unittest
from yt_axia_source_metadata_gate_v01 import head_probe,parse_checksum,GateError,DATES

class SourceGateTests(unittest.TestCase):
    def test_sha_single_token(self):
        self.assertEqual(parse_checksum(b"a"*64,"x.zip"),"a"*64)
    def test_sha_filename(self):
        self.assertEqual(parse_checksum((("f"*64)+"  *x.zip").encode(),"x.zip"),"f"*64)
    def test_wrong_name_rejected(self):
        with self.assertRaises(GateError):parse_checksum((("f"*64)+"  y.zip").encode(),"x.zip")
    def test_bad_sha_rejected(self):
        with self.assertRaises(GateError):parse_checksum(b"not_a_sha","x.zip")
    def test_missing_day_rejected(self):
        with self.assertRaises(ValueError):head_probe("2024-99-99",None)
    def test_probe_no_zip_get(self):
        calls=[]
        def fake(url,method):
            calls.append((url,method))
            return ((1048576,b"") if method=="HEAD" else (65,(("f"*64)+"  BTCUSDT-aggTrades-2024-01-18.zip").encode()))
        r=head_probe("2024-01-18",fake)
        self.assertEqual(len(calls),2)
        self.assertTrue(calls[0][0].endswith(".zip"))
        self.assertEqual(calls[0][1],"HEAD")
        self.assertTrue(calls[1][0].endswith(".CHECKSUM"))
        self.assertEqual(calls[1][1],"GET")
        self.assertEqual(r["compressed_bytes"],1048576)
        self.assertFalse(r["zip_content_opened"])
    def test_empty_content_length_fails(self):
        def fake(url,method):return (0,b"f"*64)
        with self.assertRaises(GateError):head_probe("2024-01-18",fake)
    def test_time_period_spans_years(self):
        self.assertEqual({x[:4] for x in DATES},{"2022","2023","2024"})
    def test_no_outcome_import(self):
        import inspect,yt_axia_source_metadata_gate_v01 as m
        source=inspect.getsource(m)
        self.assertNotIn("return_bps",source)
        self.assertNotIn("trade_pnl",source)
        self.assertNotIn("POST",source)
    def test_same_file_checksum_cannot_change(self):
        sha="123"*21+"1"
        self.assertEqual(parse_checksum((sha+"  BTCUSDT-aggTrades-2024-11-25.zip").encode(),"BTCUSDT-aggTrades-2024-11-25.zip"),sha)

if __name__=="__main__": unittest.main()
