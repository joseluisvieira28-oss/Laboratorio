#!/usr/bin/env python3
"""Offline-only fail-closed protocol tests. No market connections."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import replay_artifact as v

class FrozenArtifactAuditTests(unittest.TestCase):
 def test_pins_original_code_unchanged(self):
  self.assertTrue(v.pins())
  self.assertEqual(v.RUN,45337495640)
  self.assertEqual(v.ARTIFACT_ID,14895554598)
 def test_original_sha_and_chain_frozen(self):
  self.assertEqual(len(v.RAW_SHA),64)
  self.assertEqual(v.RAW_SHA,"83ff8d37e2fcf9477cd7e8e125f243063167ffa702cd5c6ae9b12292c8760cac")
  self.assertEqual(v.LAST_CHAIN,"2291d3e97e2ed98762bdd5376e7a150d24daed36eb4d57c04e095672b9390c6a")
 def test_known_previous_observations_are_NOT_new_heldout(self):
  self.assertEqual(v.KNOWN["PRIMARY"],(21,-31.17594879113982,0))
  self.assertEqual(v.KNOWN["FLOW_ONLY_CONTROL"][0],18)
  self.assertEqual(v.KNOWN["UNCONDITIONAL_BASELINE"][0],42)
 def test_hash_original_git_blob(self):
  self.assertEqual(v.blob(b"test\n"),"9daeafb9864cf43055ae93beb0afd6c7d144bfa4")
 def test_missing_archive_fail_closed_no_substitute(self):
  with tempfile.TemporaryDirectory() as d:
   with patch.object(v,"INPUT",Path(d)):
    with self.assertRaises(v.Stop):
     v.validate_metadata()
 def test_missing_gzip_chunk_cannot_be_skipped(self):
  with tempfile.TemporaryDirectory() as d:
   with patch.object(v,"INPUT",Path(d)):
    p=Path(d)/"recovered.jsonl"
    with self.assertRaises(v.Stop):
     v.decompress_exact({"chunks":[{"file":"journal-part-0001.jsonl.gz"}]},p)
 def test_004_correct_verifier_exists_with_check(self):
  spec=importlib.util.spec_from_file_location("binance011r_test_pinned_004",
   v.ROOT/"research/binance_diamante004/verify_offline.py")
  self.assertEqual(spec.origin,
    str(v.ROOT/"research/binance_diamante004/verify_offline.py"))
  self.assertIn("def check():",(v.ROOT/"research/binance_diamante004/verify_offline.py").read_text())
  self.assertIn("def main():",(v.ROOT/"research/binance_diamante003/verify_offline.py").read_text())
 def test_offline_script_has_no_executable_market_connector(self):
  script=(v.ROOT/"research/binance_diamante011r/replay_artifact.py").read_text()
  self.assertNotIn("wss://",script)
  self.assertNotIn("api.binance",script)
  self.assertNotIn("asyncio.run(",script)
  self.assertNotIn("collect()",script)

if __name__=="__main__":unittest.main()
