"""RW-HL first durable-source intake synthetic correctness checks."""
import hashlib,unittest
import rw_hl_forward_source_capture_v01 as capture

def market():
    names=["BTC","ETH","SOL","XRP","DOGE"]
    return [{"universe":[{"name":n} for n in names]},
      [{"openInterest":"123","markPx":"8500.50","funding":"0.00001",
        "dayNtlVlm":"50000"} for n in names]]

class TestSourceCapture(unittest.TestCase):
    def test_sha_chain_genesis(self):
        payload=b"source\n"
        self.assertEqual(capture.chain("0"*64,payload),
          hashlib.sha256(bytes.fromhex("0"*64)+payload).hexdigest())
    def test_sha_chain_order_changes(self):
        z="0"*64
        self.assertNotEqual(capture.chain(capture.chain(z,b"a"),b"b"),
            capture.chain(capture.chain(z,b"b"),b"a"))
    def test_only_public_query(self):
        items=[]
        def fake(x):
            items.append(x);return market()
        r=capture.capture_once(fake)
        self.assertEqual(items,[{"type":"metaAndAssetCtxs"}])
        self.assertEqual(r["valid_public_markets"],5)
    def test_three_snapshots_exact(self):
        self.assertEqual(capture.SAMPLE_N,3)
    def test_delay_minute(self):
        self.assertEqual(capture.DELAY_SECONDS,60)
    def test_source_freeze_exists(self):
        self.assertTrue(capture.SOURCE_PROOF.exists())
        self.assertIn("FIRST PROSPECTIVE SOURCE CAPTURE AUTHORITY",
          capture.SOURCE_PROOF.read_text())
    def test_no_private_account_calls(self):
        import inspect
        src=inspect.getsource(capture)
        self.assertNotIn('type":"user',src)
        self.assertNotIn('type":"exchange',src)
    def test_no_outcome_classifier(self):
        import inspect
        src=inspect.getsource(capture)
        self.assertNotIn("calculate_pnl",src)
        self.assertNotIn("signal_score",src)
    def test_current_timestamp_has_utc_z(self):
        self.assertTrue(capture.stamp().endswith("Z"))
if __name__=="__main__":unittest.main()
