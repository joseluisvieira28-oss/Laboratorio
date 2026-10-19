import json
import unittest
from ledger import funding, cost_floor, four_commissions, validate_history, D

class AccountingTests(unittest.TestCase):
    def test_long_pays_positive(self):
        self.assertEqual(funding(1,1,1,1000,".001"),D("-1"))
    def test_short_receives_positive(self):
        self.assertEqual(funding(-1,1,1,1000,".001"),D("1"))
    def test_reversal_is_loss(self):
        self.assertEqual(funding(-1,1,1,1000,"-.001"),D("-1"))
    def test_real_notional_not_constant_entry(self):
        self.assertEqual(funding(1,2,".1",1200,".001"),D("-.24"))
    def test_four_actual_notionals(self):
        self.assertEqual(four_commissions([1000,1100,1000,900]),D("2.21"))
    def test_no_missing_execution(self):
        with self.assertRaises(ValueError): four_commissions([1000]*3)
    def test_cost_capital_denominator(self):
        self.assertEqual(cost_floor(),D(3))
        self.assertEqual(cost_floor(stress=True),D(5))
        self.assertEqual(cost_floor()/2000,D(".0015"))
    def test_synthetic_basis_widening(self):
        # Long A gains 10, short B loses 20; carry of 1 cannot rescue it.
        price_pnl=(110-100)-(122-102)
        self.assertEqual(D(price_pnl)+D(1)-cost_floor(),D(-12))
    def test_asynchronous_settlements(self):
        # 1h short venue vs 8h long venue, sum cashflows rather than raw rates.
        short=sum(funding(-1,1,1,1000,".0001") for _ in range(8))
        long=funding(1,1,1,1000,".0004")
        self.assertEqual(short+long,D(".4"))
    def test_nonfinite(self):
        for bad in ("NaN","Infinity",None,True):
            with self.assertRaises(ValueError): funding(1,1,1,1000,bad)

class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.ts=1735689600000
        self.row={"symbol":"BTCUSDT","fundingTime":self.ts,"fundingRate":".0001","markPrice":"1000"}
    def check(self,raw):
        return validate_history(raw,"BINANCE","BTCUSDT",self.ts,self.ts+86400000)
    def test_schema_only_valid(self):
        self.assertEqual(self.check(json.dumps([self.row])),1)
    def test_empty_html_errors(self):
        for raw in ("[]","<html>403</html>",'{"code":-1}'):
            with self.assertRaises(ValueError): self.check(raw)
    def test_duplicate(self):
        with self.assertRaises(ValueError): self.check(json.dumps([self.row]*2))
    def test_protected_holdout(self):
        self.row["fundingTime"]=1767225600000
        with self.assertRaises(ValueError): self.check(json.dumps([self.row]))
    def test_missing_price(self):
        del self.row["markPrice"]
        with self.assertRaises(ValueError): self.check(json.dumps([self.row]))
    def test_wrong_symbol(self):
        self.row["symbol"]="ETHUSDT"
        with self.assertRaises(ValueError): self.check(json.dumps([self.row]))
    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError): self.check('[{"symbol":"BTCUSDT","symbol":"ETHUSDT"}]')
    def test_mexc_incomplete_pagination(self):
        with self.assertRaises(ValueError):
            validate_history('{"success":true,"code":0,"data":{"resultList":[]}}',"MEXC","BTC_USDT",self.ts,self.ts)
    def test_mexc_requires_cycle(self):
        row={"symbol":"BTC_USDT","settleTime":self.ts,"fundingRate":".0001"}
        raw={"success":True,"code":0,"data":{"pageSize":1,"totalCount":1,"totalPage":1,"currentPage":1,"resultList":[row]}}
        with self.assertRaises(ValueError): validate_history(json.dumps(raw),"MEXC","BTC_USDT",self.ts,self.ts)
    def test_unsupported_interval(self):
        row={"symbol":"BTC_USDT","settleTime":self.ts,"fundingRate":".0001","collectCycle":2}
        raw={"success":True,"code":0,"data":{"pageSize":1,"totalCount":1,"totalPage":1,"currentPage":1,"resultList":[row]}}
        with self.assertRaises(ValueError): validate_history(json.dumps(raw),"MEXC","BTC_USDT",self.ts,self.ts)

if __name__=="__main__":
    unittest.main(verbosity=2)
