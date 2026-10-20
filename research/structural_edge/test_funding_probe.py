"""Hermetic tests: market packets synthetic, no exchange endpoints or outcomes."""
import unittest
from funding_probe import bbo, screen_pair, FEE_BPS, EIGHT_HOURS_MS
T=1800000000000
S=T+3600000

def fixtures(okx_rate="0.0003", bybit_rate="0.0001"):
    okx = {"okx_funding":{"data":[{"instId":"BTC-USDT-SWAP","fundingTime":str(S),
                                    "prevFundingTime":str(S-EIGHT_HOURS_MS),"fundingRate":okx_rate}]},
           "okx_book":{"data":[{"ts":str(T-1000),"bids":[["100","5"]],"asks":[["100.01","5"]]}]},
           "bybit_ticker":{"result":{"list":[{"symbol":"BTCUSDT","nextFundingTime":str(S),"fundingRate":bybit_rate}]}},
           "bybit_book":{"result":{"s":"BTCUSDT","ts":T-1000,"b":[["100","5"]],"a":[["100.01","5"]]}},
           "bybit_instrument":{"result":{"list":[{"symbol":"BTCUSDT","fundingInterval":480}]}}}
    return okx

class TestFalsifier(unittest.TestCase):
    def test_four_fill_benchmark(self):self.assertEqual(FEE_BPS,24)
    def test_low_diff_below_hurdle(self):
        r=screen_pair("BTC",fixtures(),T)
        self.assertEqual(r["verdict"],"SINGLE_INTERVAL_ESTIMATE_BELOW_FROZEN_HURDLE")
        self.assertEqual(r["predicted_single_settlement_gross_bps"],2)
    def test_high_diff_only_source_screen(self):
        r=screen_pair("BTC",fixtures("0.01","0.0001"),T)
        self.assertEqual(r["verdict"],"SOURCE_SCREEN_POSITIVE_NOT_EDGE")
        self.assertIn("net_profit",r["not_proven"])
    def test_bad_bbo(self):
        with self.assertRaisesRegex(ValueError,"CROSSED"):bbo("100","100","1","1")
    def test_zero_liquidity(self):
        with self.assertRaisesRegex(ValueError,"INVALID"):bbo("100","101","0","1")
    def test_nonnumeric_funding(self):
        with self.assertRaisesRegex(ValueError,"NONFINITE"):screen_pair("BTC",fixtures("NaN","0"),T)
    def test_settlement_mismatch(self):
        x=fixtures();x["bybit_ticker"]["result"]["list"][0]["nextFundingTime"]=str(S+3600000)
        with self.assertRaisesRegex(ValueError,"FUNDING_TIME"):screen_pair("BTC",x,T)
    def test_interval_mismatch(self):
        x=fixtures();x["bybit_instrument"]["result"]["list"][0]["fundingInterval"]=240
        with self.assertRaisesRegex(ValueError,"BYBIT_NOT_8H"):screen_pair("BTC",x,T)
    def test_stale_book(self):
        x=fixtures();x["okx_book"]["data"][0]["ts"]=str(T-60000)
        with self.assertRaisesRegex(ValueError,"STALE"):screen_pair("BTC",x,T)
    def test_wrong_symbol(self):
        x=fixtures();x["okx_funding"]["data"][0]["instId"]="ETH-USDT-SWAP"
        with self.assertRaisesRegex(ValueError,"INSTRUMENT_MISMATCH"):screen_pair("BTC",x,T)
    def test_negative_rate_is_not_error(self):
        r=screen_pair("BTC",fixtures("-0.0001","0.0001"),T)
        self.assertEqual(r["higher_predicted_funding_venue"],"BYBIT")
    def test_future_book_fails(self):
        x=fixtures();x["bybit_book"]["result"]["ts"]=T+5000
        with self.assertRaisesRegex(ValueError,"STALE"):screen_pair("BTC",x,T)

if __name__=="__main__":unittest.main()
