import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import source_probe as p

class Tests(unittest.TestCase):
    def test_rejects_modified_seed(self):
        with tempfile.TemporaryDirectory() as folder:
            f=pathlib.Path(folder)/"seed.json"
            f.write_text("{}")
            with self.assertRaisesRegex(RuntimeError,"SOURCE_INTEGRITY_BLOCKED"):
                p.cohort(f)
    def test_300_trade_truncation_cannot_prove_one_hour(self):
        d={"data":[{"attributes":{"block_timestamp":"2026-11-19T00:00:00Z",
                         "kind":"buy","tx_from_address":"ABC"}} for _ in range(300)]}
        result=p.trades_schema(d)
        self.assertEqual(result["count"],300)
        self.assertFalse(result["full_2026_october_history_available"])
        self.assertEqual(result["detected_attribute_fields"]["tx_from_address"],300)
    def test_absent_trades_blocked(self):
        self.assertFalse(p.trades_schema(None)["is_trade_array"])
    def test_index_never_deems_empty_valid_trade(self):
        self.assertEqual(p.index_schema({"files":[1,2]})["list_files_count"],2)
        self.assertFalse(p.index_schema(None)["valid_json"])

if __name__=="__main__":unittest.main()
