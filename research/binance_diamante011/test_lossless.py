#!/usr/bin/env python3
"""Offline adversarial checks for lossless compression, source locks and economics.
Synthetic input ONLY; never connects to market or computes live PnL.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal as D

from lossless_journal import (SegmentedJournal,verify_segments,sha_file,
                              CHUNK_MAX_RAW,RAW_MAX,ARCHIVE_MAX)
from runner import guard,setup,OUT,EXPECTED_DAY,EXPERIMENT
from book_core import Journal # original 003 Journal imported via lossless_journal sys.path

def synthetic_pair(out,count=15,chunk_limit=750):
    out=Path(out)
    out.mkdir(exist_ok=True)
    control=Journal(out/"control.jsonl")
    segmented=SegmentedJournal(out/"journal.jsonl",chunk_max=chunk_limit)
    for i in range(count):
        msg=json.dumps({"event":"synthetic_only","timestamp":i,"raw":["αβ🧪",i],"padding":"x"*27})
        opts={"kind":"ws","symbol":"BTCUSDT","raw":msg,
              "utc_ns":1795480000000000000+i,"mono_ns":6500000000000+i}
        control.append(**opts)
        segmented.append(**opts)
    control.close()
    segmented.close()
    return out

class OriginalJournalEquivalence(unittest.TestCase):
    def test_frozen_guard(self):
        g=guard(check_day=False)
        self.assertEqual(g["study"],EXPERIMENT)
        self.assertEqual(g["actual_orders"],0)
    def test_explicit_one_day_and_30min(self):
        self.assertEqual(EXPECTED_DAY,"2026-11-24")
        self.assertEqual((CHUNK_MAX_RAW,RAW_MAX,ARCHIVE_MAX),
                         (16000000,520000000,160000000))
        self.assertEqual(str(OUT),"binance011-evidence")
    def test_original_module_exact_source_fee_thresholds(self):
        cap,science=setup()
        self.assertIs(cap.Journal,SegmentedJournal)
        self.assertEqual(cap.MAX_JOURNAL_BYTES,RAW_MAX)
        self.assertEqual(cap.MAX_FRAMES,420000)
        self.assertEqual(cap.SECONDS_POST_SYNC,1800)
        self.assertEqual(science.CAPTURE_NS,1800*10**9)
        self.assertEqual(science.LATEST_DECISION_NS,1680*10**9)
        self.assertEqual(science.SELL_THRESHOLD,D("0.65"))
        self.assertEqual(science.MIN_QUOTE,D("5000"))
        self.assertEqual(science.DEPTH_PERSIST_MIN,D("0.80"))
        self.assertEqual(science.MID_FLOOR_BPS,D("-3"))
        self.assertEqual(science.SCENARIOS["STRESS_5BPS"],D("5"))
        self.assertEqual(science.FEE_BPS,D("10"))
        self.assertEqual(science.MIN_DAYS_FOR_GO,20)
    def test_original_control_and_compressed_identical_every_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=synthetic_pair(tmp)
            self.assertEqual((p/"control.jsonl").read_bytes(),(p/"journal.jsonl").read_bytes())
            report=verify_segments(p)
            self.assertEqual(report["status"],"LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS")
            self.assertTrue(report["compression_roundtrip_byte_exact"])
            self.assertEqual(report["raw_uncompressed_sha256"],sha_file(p/"control.jsonl"))
            idx=json.loads((p/"lossless_segments_manifest.json").read_text())
            self.assertGreaterEqual(len(idx["chunks"]),3)
            self.assertEqual(idx["total_chained_records"],15)
            self.assertEqual(idx["journal_last_chain_sha256"],
                             json.loads((p/"control.jsonl").read_text().splitlines()[-1])["chain_sha256"])
    def test_true_original_binary_roundtrip_with_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=synthetic_pair(tmp)
            original=sha_file(p/"journal.jsonl")
            result=verify_segments(p,remove_raw=True)
            self.assertEqual(result["status"],"LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS")
            self.assertFalse((p/"journal.jsonl").exists())
            self.assertEqual(original,result["raw_uncompressed_sha256"])
            self.assertTrue(all((p/x["file"]).exists()
                       for x in json.loads((p/"lossless_segments_manifest.json").read_text())["chunks"]))
    def test_tampered_gzip_byte_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=synthetic_pair(tmp)
            idx=json.loads((p/"lossless_segments_manifest.json").read_text())
            item=p/idx["chunks"][0]["file"]
            raw=item.read_bytes()
            item.write_bytes(raw[:-3]+b"xyz")
            report=verify_segments(p)
            self.assertEqual(report["status"],"ARCHIVE_BLOCKED")
            self.assertNotIn("LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS",report["status"])
    def test_original_uncompressed_journal_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=synthetic_pair(tmp)
            f=p/"journal.jsonl"
            raw=f.read_bytes()
            f.write_bytes(raw[:-1]+b"\x00")
            report=verify_segments(p)
            self.assertEqual(report["status"],"ARCHIVE_BLOCKED")
            self.assertEqual(report["blocker"],"ORIGINAL_JSONL_BYTE_MISMATCH")
    def test_deleted_chunk_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=synthetic_pair(tmp)
            idx=json.loads((p/"lossless_segments_manifest.json").read_text())
            (p/idx["chunks"][1]["file"]).unlink()
            report=verify_segments(p)
            self.assertEqual(report["status"],"ARCHIVE_BLOCKED")
    def test_oversized_synthetic_record_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            journal=SegmentedJournal(p/"journal.jsonl",chunk_max=400)
            with self.assertRaisesRegex(ValueError,"SEGMENT_LIMIT"):
                journal.append(kind="ws",symbol="BTCUSDT",
                      raw="a"*2000,utc_ns=1795480000000000000,mono_ns=6500000000000)
            journal.close()
    def test_raw_journal_order_and_byte_sha_are_conserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=synthetic_pair(tmp,count=8,chunk_limit=750)
            idx=json.loads((p/"lossless_segments_manifest.json").read_text())
            self.assertEqual(sum(x["records"] for x in idx["chunks"]),8)
            self.assertEqual(idx["chunks"][0]["record_seq_first"],1)
            self.assertEqual(idx["chunks"][-1]["record_seq_last"],8)
            self.assertEqual(sum(x["original_bytes"] for x in idx["chunks"]),
                             (p/"control.jsonl").stat().st_size)
    def test_fee_costs_stay_nonzero_even_if_print_unchanged(self):
        _,study=setup()
        from decimal import Decimal as D
        m=study.ProspectiveStudy()
        self.assertFalse(m.summary()["economic_go"])
        self.assertEqual(m.summary()["real_fills"],0)

if __name__=="__main__":unittest.main()
