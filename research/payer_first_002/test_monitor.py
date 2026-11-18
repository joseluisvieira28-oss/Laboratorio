import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from monitor import decode_liquidation, monitor

F = json.loads(Path(__file__).with_name('fixture_aave_base_liquidation.json').read_text())

class Tests(unittest.TestCase):
    def test_decode_real_historical_event(self):
        r=decode_liquidation(F)
        self.assertEqual(r['debt_repaid_usdc'], '42061.674725')
        self.assertEqual(r['collateral_liquidated_weth'], '19.415285763088108751')
        self.assertEqual(r['borrower_address'], '0xc936a10fa85231bd1d5d859865c3f1749d4e7f17')
    def test_threshold_pass(self):
        self.assertEqual(len(monitor([F], Decimal('40000'))),1)
    def test_threshold_fail(self):
        self.assertEqual(len(monitor([F], Decimal('45000'))),0)
    def test_duplicate_event(self):
        self.assertEqual(len(monitor([F,F], Decimal('1'))),1)
    def test_reject_wrong_chain(self):
        e=copy.deepcopy(F);e['chain_id']=1
        with self.assertRaises(ValueError):decode_liquidation(e)
    def test_reject_wrong_emitter(self):
        e=copy.deepcopy(F);e['address']='0x'+'0'*40
        with self.assertRaises(ValueError):decode_liquidation(e)
    def test_reject_wrong_topic(self):
        e=copy.deepcopy(F);e['topics'][0]='0x'+'0'*64
        with self.assertRaises(ValueError):decode_liquidation(e)
    def test_reject_wrong_decimal_asset(self):
        e=copy.deepcopy(F);e['topics'][2]='0x'+'0'*64
        with self.assertRaises(ValueError):decode_liquidation(e)
    def test_reject_malformed_data(self):
        e=copy.deepcopy(F);e['data']='0x0'
        with self.assertRaises(ValueError):decode_liquidation(e)
    def test_reject_failed_transaction(self):
        e=copy.deepcopy(F);e['transaction_status']='failed'
        with self.assertRaises(ValueError):decode_liquidation(e)
    def test_reject_bad_boolean(self):
        e=copy.deepcopy(F);e['data']=e['data'][:-64] + '0'*63+'2'
        with self.assertRaises(ValueError):decode_liquidation(e)
    def test_negative_threshold(self):
        with self.assertRaises(ValueError):monitor([F],Decimal('-1'))

if __name__=='__main__':unittest.main()
