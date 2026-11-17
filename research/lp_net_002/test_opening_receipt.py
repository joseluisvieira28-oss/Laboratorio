"""Offline canonical Uniswap v3 pool Mint signature regression check."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import opening_receipt_proof as p

class TestCanonicalPoolMint(unittest.TestCase):
    def test_topic_frozen_from_actual_pool_receipts(self):
        self.assertEqual(p.POOL_MINT,
          "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde")
    def test_pool_address_frozen(self):
        self.assertEqual(p.POOL,"0x6c6bc977e13df9b0de53b251522280bb72383700")
    def test_four_word_pool_mint_matches_three_word_manager_increase(self):
        manager=[123456,12*10**18,17*10**6]
        pool=[int("c36442b4a4522e871399cd717abdd847ab11fe88",16)]+manager
        blob="0x"+"".join(format(x,"064x") for x in pool)
        self.assertEqual(p.abi(blob)[1:],manager)

if __name__=="__main__":unittest.main()
