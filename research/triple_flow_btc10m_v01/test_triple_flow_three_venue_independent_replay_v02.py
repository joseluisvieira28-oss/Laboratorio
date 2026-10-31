import pathlib,sys,unittest,io,json,zipfile,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from triple_flow_three_venue_independent_replay_v02 import check_zip,digest
class Integrity(unittest.TestCase):
 def test_wrong_zip_digest_rejected(self):
  with self.assertRaisesRegex(ValueError,"EXACT_SERVER_ZIP_HASH_MISMATCH"):
    check_zip(b"notzip","f"*64)
 def test_missing_all_four_files_rejected(self):
  b=io.BytesIO()
  with zipfile.ZipFile(b,"w") as z:z.writestr("source_receipt.json","{}")
  with self.assertRaisesRegex(ValueError,"WRONG_WS_ARCHIVE_FILES"):
    check_zip(b.getvalue(),digest(b.getvalue()))
if __name__=="__main__":unittest.main()
