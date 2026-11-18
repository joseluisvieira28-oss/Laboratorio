"""Synthetic checks only. They do NOT establish profitability."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from collector import choose_pair,sol_mint,pool_extract,evaluate

MINT="7R3gZePQntJW5nAS3k1qgXswfgbs3SWh9HnPrnQe1qnd"
OTHER="6x9ApsZg7BRW93jtD3Pb9qrEVxeE8R7orRg9pG8ocBfv"
NOW=1810000000000

def pair(mint=MINT,liq=250000,age_days=20,volume=150000,buy=350,sell=350,px=1.,pair_id="PAIR"):
    return {"chainId":"solana","baseToken":{"address":mint},
            "quoteToken":{"address":"So11111111111111111111111111111111111111112"},
            "pairAddress":pair_id,"priceUsd":str(px),
            "pairCreatedAt":NOW-int(age_days*86400000),
            "liquidity":{"usd":liq},"volume":{"h24":volume},
            "txns":{"h24":{"buys":buy,"sells":sell}}}

class TestScreen(unittest.TestCase):
    def test_address_not_ticker_name(self):
        x=[pair(OTHER,900000,pair_id="fake"),pair(MINT,170000,pair_id="real")]
        self.assertEqual(choose_pair(x,MINT)["pairAddress"],"real")
    def test_highest_liquidity_matching_mint(self):
        x=[pair(MINT,200000,pair_id="one"),pair(MINT,310000,pair_id="two")]
        self.assertEqual(choose_pair(x,MINT)["pairAddress"],"two")
    def test_official_mint_provenance_only(self):
        self.assertEqual(sol_mint({"platforms":{"solana":MINT}}),MINT)
        self.assertIsNone(sol_mint({"symbol":"MOON","name":"Moon","platforms":{}}))
    def test_seven_day_reject(self):
        row={"pair":pool_extract(pair(age_days=3)),"gecko_cross_check":"OK"}
        out=evaluate(row,NOW)
        self.assertEqual(out["status"],"REJECT")
        self.assertIn("POOL_AGE_LT_7D",out["reasons"])
    def test_missing_volume_is_unknown(self):
        p=pair()
        p["volume"]={}
        row={"pair":pool_extract(p),"gecko_cross_check":"OK"}
        self.assertEqual(evaluate(row,NOW)["status"],"UNKNOWN")
    def test_stress_screen_is_not_trade_approval(self):
        row={"pair":pool_extract(pair()),"gecko_cross_check":"OK"}
        out=evaluate(row,NOW)
        self.assertEqual(out["status"],"SCREEN_PASS_ONLY")
        self.assertFalse(out["can_execute"])
        self.assertFalse(out["economic_edge"])
    def test_cross_source_missing_is_unknown(self):
        row={"pair":pool_extract(pair()),"gecko_cross_check":"UNVERIFIED"}
        self.assertEqual(evaluate(row,NOW)["status"],"UNKNOWN")
    def test_no_pool_unknown(self):
        self.assertEqual(evaluate({"pair":None},NOW)["status"],"UNKNOWN")

if __name__=="__main__":unittest.main()
