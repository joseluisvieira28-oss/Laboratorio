"""Deterministic offline tests: rejects corrupt source; validates hypothetical book math."""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_cost_gate as g

def fixture():
    return {
        "lastUpdateId": 100,
        "bids": [["100.0", "100"], ["99.0", "100"]],
        "asks": [["101.0", "100"], ["102.0", "100"]]
    }
def trades(ms=1795000000000):
    return [
        {"a": 100,"p":"100","q":"0.1","f":100,"l":100,"T":ms-500,"m":True},
        {"a": 101,"p":"101","q":"0.2","f":101,"l":102,"T":ms-300,"m":False}
    ]

class BookTests(unittest.TestCase):
    def test_depth_source_pass(self):
        v=g.parse_depth(fixture())
        self.assertEqual(v["best_bid"],D("100"))
        self.assertEqual(v["best_ask"],D("101"))
        self.assertGreater(v["spread_bps"],D(0))
    def test_depth_missing_sequence(self):
        obj=fixture();obj.pop("lastUpdateId")
        with self.assertRaisesRegex(ValueError,"lastUpdateId"):g.parse_depth(obj)
    def test_crossed_book(self):
        obj=fixture();obj["bids"][0][0]="101"
        with self.assertRaisesRegex(ValueError,"crossed"):g.parse_depth(obj)
    def test_duplicate_bids(self):
        obj=fixture();obj["bids"][1][0]="100"
        with self.assertRaisesRegex(ValueError,"descending"):g.parse_depth(obj)
    def test_reversed_asks(self):
        obj=fixture();obj["asks"][1][0]="99"
        with self.assertRaisesRegex(ValueError,"ascending"):g.parse_depth(obj)
    def test_nonfinite_quote(self):
        obj=fixture();obj["asks"][0][1]="NaN"
        with self.assertRaisesRegex(ValueError,"non-positive"):g.parse_depth(obj)
    def test_nonpositive_volume(self):
        obj=fixture();obj["bids"][0][1]="0"
        with self.assertRaisesRegex(ValueError,"non-positive"):g.parse_depth(obj)
    def test_100_1000_hypothetical_stress(self):
        matrix=g.friction_matrix(g.parse_depth(fixture()))
        self.assertEqual(len(matrix),4)
        for n in ("100","1000"):
            rows={x["fee_bps_each_leg"]:x for x in matrix if x["quote_entry_usdt"]==n}
            self.assertTrue(all(r["status"]=="HYPOTHETICAL_SAME_BOOK_ONLY" for r in rows.values()))
            self.assertGreater(D(rows["10"]["cost_bps"]),D(rows["0"]["cost_bps"]))
            self.assertFalse(rows["10"]["actual_fills"])
    def test_depth_insufficient_no_fake_fill(self):
        obj=fixture()
        obj["asks"]=[["101", "0.001"]]
        x=g.friction_matrix(g.parse_depth(obj))
        self.assertTrue(all(r["status"]=="INSUFFICIENT_DEPTH" for r in x))
    def test_sell_depth_insufficient(self):
        obj=fixture()
        obj["bids"]=[["100","0.001"]]
        x=g.friction_matrix(g.parse_depth(obj))
        self.assertTrue(all(r["status"]=="INSUFFICIENT_DEPTH" for r in x))

class TradeTests(unittest.TestCase):
    def test_agg_trade_side_semantics(self):
        r=g.parse_trades(trades(),1795000000000)
        self.assertEqual(r["aggressive_sell_aggregates"],1)
        self.assertEqual(r["aggressive_buy_aggregates"],1)
    def test_duplicate_id(self):
        q=trades();q[1]["a"]=100
        with self.assertRaisesRegex(ValueError,"duplicate"):g.parse_trades(q,1795000000000)
    def test_future_timestamp(self):
        q=trades();q[-1]["T"]=1795000101000
        with self.assertRaisesRegex(ValueError,"future"):g.parse_trades(q,1795000000000)
    def test_stale_trade(self):
        with self.assertRaisesRegex(ValueError,"older"):g.parse_trades(trades(1794000000000),1795000000000)
    def test_flag_nonboolean(self):
        q=trades();q[0]["m"]=1
        with self.assertRaisesRegex(ValueError,"side flag"):g.parse_trades(q,1795000000000)
    def test_bad_url_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError,"whitelisted"):
            g.public_get("https://api.binance.com/api/v3/order?symbol=BTCUSDT")

if __name__=="__main__":
    unittest.main()
