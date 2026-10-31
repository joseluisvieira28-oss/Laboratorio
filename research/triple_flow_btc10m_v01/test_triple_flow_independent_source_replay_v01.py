import io,json,pathlib,sys,tempfile,unittest,zipfile,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from triple_flow_independent_source_replay_v01 import read_rows,sha
class Integrity(unittest.TestCase):
 def test_raw_row_bytes_sha_valid(self):
  raw='{"data":1}'
  row={"received_ms":1800000000000,"source_sha256":sha(raw.encode()),"raw_utf8":raw}
  data=(json.dumps(row)+"\n").encode()
  self.assertEqual(list(read_rows(data))[0][1],{"data":1})
 def test_tampered_payload_is_rejected(self):
  raw='{"data":1}'
  row={"received_ms":1800000000000,"source_sha256":sha(raw.encode()),"raw_utf8":'{"data":2}'}
  with self.assertRaisesRegex(ValueError,"RAW_SOURCE_ROW_HASH_MISMATCH"):
   list(read_rows((json.dumps(row)+"\n").encode()))
 def test_partial_trailing_ndjson_block(self):
  with self.assertRaisesRegex(ValueError,"BAD_NDJSON_TERMINATION"):
   list(read_rows(b'{"x":1}'))
if __name__=="__main__":unittest.main()
