"""Independent raw auditor tests using explicitly synthetic fixtures, never market data."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit_receipts import audit,AuditFail

def digest(x):return hashlib.sha256(x).hexdigest()

class AuditFaults(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.p=Path(self.folder.name)
        def row(seq,t,kind="start"):
            return {"seq":seq,"elapsed":t,"utc_ms":1793850000000+int(t*1000),
                    "mono_ns":1111000000000+int(t*1e9),
                    "venue":"system","kind":kind,"segment":0,"raw":"fixture"}
        data=(json.dumps(row(1,0))+"\n"+json.dumps(row(2,5,"end"))+"\n").encode()
        with gzip.open(self.p/"raw.jsonl.gz","wb") as f:f.write(data)
        source_dir=Path(__file__).resolve().parent
        (self.p/"manifest.json").write_text(json.dumps({
            "raw_sha256":digest(data),"gzip_sha256":digest((self.p/"raw.jsonl.gz").read_bytes()),
            "protocol_sha256":digest((source_dir/"PROTOCOL_FROZEN.md").read_bytes()),
            "source_sha256":digest((source_dir/"compare.py").read_bytes()),
            "rows":2}))
        (self.p/"report.json").write_text(json.dumps({
            "comparison":{k:{"good":0,"stale_resets":0} for k in "ABC"},
            "l50_snapshot_count":0,"l50_delta_count":0,"mexc_books":0,
            "l1_duplicate_no_refresh":0,"source_verdict":"SOURCE_COMPARE_BLOCKED"}))
    def test_synthetic_empty_evidence_never_claims_edge(self):
        a=audit(self.p)
        self.assertEqual(a["audit"],"INDEPENDENT_RECEIVE_ORDER_RECONSTRUCTION_PASS")
        self.assertEqual(a["paired_good_seconds"],{"A":0,"B":0,"C":0})
        self.assertEqual(a["live_verdict"],"NO_LIVE_GO")
    def test_raw_mutation_fails_hash(self):
        m=json.loads((self.p/"manifest.json").read_text())
        m["raw_sha256"]="bad"
        (self.p/"manifest.json").write_text(json.dumps(m))
        with self.assertRaisesRegex(AuditFail,"RAW_SHA256_MISMATCH"):audit(self.p)
    def test_gzip_mutation_fails_hash(self):
        m=json.loads((self.p/"manifest.json").read_text())
        m["gzip_sha256"]="bad"
        (self.p/"manifest.json").write_text(json.dumps(m))
        with self.assertRaisesRegex(AuditFail,"GZIP_SHA256_MISMATCH"):audit(self.p)
    def test_false_good_seconds_rejected(self):
        r=json.loads((self.p/"report.json").read_text())
        r["comparison"]["C"]["good"]=1
        (self.p/"report.json").write_text(json.dumps(r))
        with self.assertRaisesRegex(AuditFail,"CAUSAL_GRID_MISMATCH_C"):audit(self.p)
    def test_missing_sequence_number_rejected(self):
        m=json.loads((self.p/"manifest.json").read_text())
        with gzip.open(self.p/"raw.jsonl.gz","rb") as f:rows=[json.loads(x) for x in f]
        rows[1]["seq"]=5
        data=("\n".join(json.dumps(x) for x in rows)+"\n").encode()
        with gzip.open(self.p/"raw.jsonl.gz","wb") as f:f.write(data)
        m["raw_sha256"]=digest(data)
        m["gzip_sha256"]=digest((self.p/"raw.jsonl.gz").read_bytes())
        (self.p/"manifest.json").write_text(json.dumps(m))
        with self.assertRaisesRegex(AuditFail,"SEQ_BAD"):audit(self.p)

if __name__=="__main__":unittest.main()
