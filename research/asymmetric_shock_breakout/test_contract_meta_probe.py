#!/usr/bin/env python3
import unittest
from contract_meta_probe import normalize_contract, check_server_time
def base():
    return {
        "symbol":"BTC_USDT","quoteCoin":"USDT","futureType":1,"state":0,
        "type":1,"apiAllowed":True,"contractSize":0.0001,"minVol":1,
        "volUnit":1,"priceUnit":0.1,"takerFeeRate":0.0008,
        "feeRateMode":"NORMAL"
    }
class TestContractMetadata(unittest.TestCase):
    def test_valid(self):
        v=normalize_contract(base(),"BTC_USDT")
        self.assertTrue(v["enabled_in_public_contract_metadata"])
        self.assertTrue(v["fee_sources_match"])
        self.assertEqual(v["contract_size"],0.0001)
    def test_list_schema(self):
        self.assertEqual(normalize_contract([base()],"BTC_USDT")["symbol"],"BTC_USDT")
    def test_nested_schema(self):
        self.assertEqual(normalize_contract({"list":[base()]},"BTC_USDT")["symbol"],"BTC_USDT")
    def test_disabled(self):
        x=base();x["apiAllowed"]=False
        self.assertFalse(normalize_contract(x,"BTC_USDT")["enabled_in_public_contract_metadata"])
    def test_fee_discrepancy_visible(self):
        x=base();x["takerFeeRate"]=0.0001
        self.assertFalse(normalize_contract(x,"BTC_USDT")["fee_sources_match"])
    def test_invalid_size(self):
        x=base();x["contractSize"]=0
        with self.assertRaisesRegex(ValueError,"CONTRACT_SIZE"): normalize_contract(x,"BTC_USDT")
    def test_symbol_mismatch(self):
        with self.assertRaisesRegex(ValueError,"CONTRACT_IDENTITY"):normalize_contract(base(),"SOL_USDT")
    def test_clock_valid(self):
        self.assertEqual(check_server_time(1800000000000,1800000000500)["server_clock_offset_ms_observed_minus_exchange"],500)
    def test_clock_out_of_range(self):
        with self.assertRaisesRegex(ValueError,"SERVER_CLOCK"):check_server_time(1800000000000,1800000030000)
if __name__=="__main__": unittest.main()
