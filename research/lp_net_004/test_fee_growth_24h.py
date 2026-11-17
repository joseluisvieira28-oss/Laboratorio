"""Read-only global fee growth block diagnostics offline invariants."""
import unittest,sys,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fee_growth_24h_block_pinned as f
class FeeGrowthGuard(unittest.TestCase):
 def test_raw_selectors_and_known_uniswap_signature(self):
  self.assertEqual(f.SEL["global0"],"0xf3058399")
  self.assertEqual(f.SEL["global1"],"0x46141319")
 def test_u256_rejects_out_of_range(self):
  with self.assertRaises(ValueError):f.u256("0x"+("f"*65))
 def test_wrapping_arithmetic(self):
  big=(1<<256)-3;small=5
  self.assertEqual((small-big)%f.UINT256,8)
 def test_no_transactions_in_module(self):
  source=inspect.getsource(f)
  for term in ("eth_sendRawTransaction","eth_sendTransaction","PRIVATE_KEY","signTransaction"):
   self.assertNotIn(term,source)
 def test_fee_growth_is_not_inside(self):
  self.assertIn("NOT_RECONSTRUCTED",inspect.getsource(f))
if __name__=="__main__":unittest.main()
