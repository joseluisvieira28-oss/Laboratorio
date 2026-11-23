#!/usr/bin/env python3
"""No-network verified official redirect scope tests, BINANCE009."""
import unittest
from official_hf_source import official_hf_redirect,OFFICIAL_HOSTS,SOURCE,RUN_DIR

class OfficialRedirect(unittest.TestCase):
    def test_exact_preverified_host(self):
        self.assertTrue(official_hf_redirect("https://us.aws.cdn.hf.co/xet-bridge-us/foo?X-Amz-Signature=redacted"))
    def test_all_official_hosts_https(self):
        for host in OFFICIAL_HOSTS:
            self.assertTrue(official_hf_redirect("https://"+host+"/xet-bridge-us/abc"))
    def test_third_party_suffix_spoof(self):
        for url in ("https://us.aws.cdn.hf.co.bad.example/path",
                    "https://another.hf.co/path",
                    "https://evil.org/file",
                    "http://us.aws.cdn.hf.co/file",
                    "https://us.aws.cdn.hf.co:8080/file",
                    "https://tester@us.aws.cdn.hf.co/file"):
            self.assertFalse(official_hf_redirect(url))
    def test_no_root_domain_wildcard(self):
        self.assertNotIn("*.hf.co",OFFICIAL_HOSTS)
        self.assertNotIn("hf.co",OFFICIAL_HOSTS)
    def test_scope_unchanged(self):
        self.assertEqual(SOURCE.DATASET,"Goooddy/crypto-lob-stream")
        self.assertEqual(SOURCE.SYMBOL,"SOLUSDT")
        self.assertEqual(SOURCE.MONTH,"2026-08")
        self.assertEqual(len(SOURCE.PARTS),3)
        self.assertEqual(SOURCE.MAX_DEPTH_ROWS,200000)
    def test_caps_unchanged(self):
        self.assertEqual(SOURCE.MAX_FILE_BYTES,90_000_000)
        self.assertEqual(SOURCE.MAX_ALL_BYTES,160_000_000)
    def test_source_not_alphas(self):
        self.assertEqual(str(RUN_DIR),"binance009-evidence")

if __name__=="__main__":unittest.main()
