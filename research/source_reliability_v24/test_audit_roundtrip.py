#!/usr/bin/env python3
"""End-to-end independent auditor smoke with synthetic 2h receipt, no market data."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from audit_v24 import audit,AuditFail

def h(b):return hashlib.sha256(b).hexdigest()

class SyntheticRawReplay(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.folder=self.root/"v24_evidence";self.folder.mkdir()
        captured=self.root/"research"
        own=Path(__file__).resolve().parent
        for short,original in (
            ("source_reliability_v24/PROTOCOL_FROZEN.md",own/"PROTOCOL_FROZEN.md"),
            ("source_reliability_v22/compare.py",own.parent/"source_reliability_v22"/"compare.py")
        ):
            target=captured/short;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(original.read_bytes())
        self.rawrows=[
            {"seq":1,"mono_ns":1_000_000_000,
             "utc_ms":1_800_000_000_000,"elapsed":0.0,
             "venue":"system","kind":"start","segment":0,"raw":"{}"},
            {"seq":2,"mono_ns":7_201_100_000_000,
             "utc_ms":1_800_007_200_100,"elapsed":7200.1,
             "venue":"system","kind":"end","segment":0,"raw":"WALL_LIMIT"}
        ]
        self.write()

    def write(self):
        raw=("\n".join(json.dumps(r,separators=(",",":")) for r in self.rawrows)+"\n").encode()
        with gzip.open(self.folder/"raw.jsonl.gz","wb") as f:f.write(raw)
        m={"protocol_sha256":h((self.root/"research/source_reliability_v24/PROTOCOL_FROZEN.md").read_bytes()),
           "source_sha256":h((self.root/"research/source_reliability_v22/compare.py").read_bytes()),
           "gzip_sha256":h((self.folder/"raw.jsonl.gz").read_bytes()),
           "raw_sha256":h(raw),"rows":len(self.rawrows),"end_reason":"WALL_LIMIT"}
        (self.folder/"manifest.json").write_text(json.dumps(m))
        (self.folder/"report.json").write_text(json.dumps({
           "elapsed_seconds":7200.1,"grid_seconds":7200,
           "comparison":{k:{"good":0} for k in "ABC"},
           "l50_delta_count":0,"l50_snapshot_count":0,"mexc_books":0,
           "source_verdict":"SOURCE_COMPARE_NO_GAIN","reason":"WALL_LIMIT"}))

    def test_synthetic_two_hour_empty_source_must_be_blocked(self):
        v=audit(self.folder)
        self.assertEqual(v["source_verdict"],"SOURCE_STRESS_BLOCKED")
        self.assertEqual(v["joint_good_seconds"]["C"],0)
        self.assertEqual(len(v["ten_minute_windows"]),12)
        self.assertEqual(v["bad_ten_minute_windows"],list(range(12)))
        self.assertEqual(v["economic_verdict"],"ECONOMIC_INSUFFICIENT")

    def test_tampered_original_raw_fails_sha(self):
        manifest=json.loads((self.folder/"manifest.json").read_text())
        manifest["raw_sha256"]="0"*64
        (self.folder/"manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(AuditFail,"UNCOMPRESSED_RAW_HASH_MISMATCH"):
            audit(self.folder)

    def test_fake_good_seconds_not_accepted_without_raw(self):
        report=json.loads((self.folder/"report.json").read_text())
        report["comparison"]["C"]["good"]=6840
        (self.folder/"report.json").write_text(json.dumps(report))
        with self.assertRaisesRegex(AuditFail,"ASOF_COVERAGE_MISMATCH_C"):
            audit(self.folder)

if __name__=="__main__":
    unittest.main(verbosity=2)
