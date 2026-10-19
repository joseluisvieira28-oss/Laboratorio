"""Offline-only Windows/Linux fixture for exact manually supplied OKX archive."""
import io,tarfile,tempfile,json,unittest
from pathlib import Path
from research.convex_okx_l2_v05.catalogue_gate import CASES
from research.convex_okx_l2_v05.local_archive_importer import validate_one

def make_tar(path,ts):
    rows=[
        {"instId":"BNB-USDT-SWAP","ts":ts-500,"action":"snapshot",
         "asks":[["100.1","4"],["101","5"]],"bids":[["100","7"]],
         "seqId":200,"prevSeqId":-1},
        {"instId":"BNB-USDT-SWAP","ts":ts+1000,"action":"update",
         "asks":[["101","6"]],"bids":[],"seqId":201,"prevSeqId":200}
    ]
    raw=("\n".join(json.dumps(x) for x in rows)+"\n").encode()
    with tarfile.open(path,"w:gz") as t:
        info=tarfile.TarInfo("BNB-USDT-SWAP_2023-11-01.ndjson")
        info.size=len(raw)
        t.addfile(info,io.BytesIO(raw))

class LocalImporterSafety(unittest.TestCase):
    def test_exact_offline_book_can_pass_structure_not_account(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"BNB-USDT-SWAP_l2_orderbook_2023-11-01.tar.gz"
            make_tar(p,1698854700000)
            x=validate_one(CASES[1],p)
            self.assertEqual(x["status"],"PRELIMINARY_CAUSAL_BOOK_SOURCE_ONLY")
            self.assertEqual(x["signal_quote_age_ms"],500)
            self.assertFalse(x["actual_broker_fill_verified"])
            self.assertFalse(x["historical_contract_multiplier_verified"])
    def test_wrong_symbol_filename_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"SOL-USDT-SWAP_l2_orderbook_2023-11-01.tar.gz"
            p.write_bytes(b"not archive")
            x=validate_one(CASES[1],p)
            self.assertEqual(x["status"],"SOURCE_BLOCKED")
            self.assertIn("WRONG_INSTRUMENT",x["reason"])
    def test_missing_archive_reported_not_invented(self):
        x=validate_one(CASES[0],None)
        self.assertEqual(x["status"],"SOURCE_BLOCKED")
    def test_corrupt_transport_bytes_do_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"BNB-USDT-SWAP_l2_orderbook_2023-11-01.tar.gz"
            p.write_bytes(b"not gzip at all")
            x=validate_one(CASES[1],p)
            self.assertEqual(x["status"],"SOURCE_BLOCKED")
if __name__=="__main__":
    unittest.main()
