from datetime import date
import unittest

from .pmr001_three_books_v02 import (
    parse_token_ids, selection, book_data, analyze_pair, fetch_books, SourceBlocked
)

DAY=date(2026,10,13)
COND="0x"+"9"*64
TOKENS=["101","102"]

def market(i,minsize="50"):
    return {
        "id":str(i), "active":True,"closed":False,"acceptingOrders":True,
        "enableOrderBook":True,"rewardsMinSize":minsize,
        "rewardsMaxSpread":"3","liquidityNum":"10000",
        "clobTokenIds":'["101","102"]',"conditionId":COND,
        "clobRewards":[{"rewardsDailyRate":"100","startDate":"2026-10-01",
                        "endDate":"2026-10-31"}]
    }

def orderbook(tok,mid=COND,bid="0.45",ask="0.55"):
    return {
        "market":mid, "asset_id":tok, "hash":"hash"+tok,
        "timestamp":"1791897600000","tick_size":"0.01",
        "bids":[{"price":bid,"size":"75"},{"price":"0.40","size":"20"}],
        "asks":[{"price":ask,"size":"60"},{"price":"0.60","size":"30"}]
    }

class PMR001V02Tests(unittest.TestCase):
    def test_two_token_ids_string_schema(self):
        self.assertEqual(parse_token_ids('["101","102"]'),["101","102"])
        self.assertIsNone(parse_token_ids('["101","101"]'))
        self.assertIsNone(parse_token_ids('["abc","102"]'))
        self.assertIsNone(parse_token_ids("invalid"))

    def test_select_numeric_id_sort_not_reward_cherry_pick(self):
        picked=selection([[market(12),market(4)],[market(9),market(2,"200")]],DAY)
        self.assertEqual([m["market_id"] for m in picked],["4","9","12"])

    def test_exact_three_no_backfill_if_two_qualified(self):
        selected=selection([[market(12)],[market(2,"200")]],DAY)
        self.assertEqual(len(selected),1)

    def test_book_pair_computes_cost_not_profit(self):
        m=selection([[market(10)],[]],DAY)[0]
        result=analyze_pair(m,orderbook("101"),orderbook("102"))
        self.assertEqual(result["counterfactual_buy_yes_and_no_at_best_bid_usdc"],45.0)
        self.assertTrue(result["cash_proxy_under_100_usdc"])
        self.assertIsNone(result["individual_usdc_payout"])
        self.assertIsNone(result["user_net_pnl"])
        self.assertEqual(result["yes"]["top3_bid_shares"],95.0)

    def test_books_crossed_or_wrong_token_fail_closed(self):
        with self.assertRaises(SourceBlocked):
            book_data(orderbook("101",ask="0.44"),"101",COND)
        with self.assertRaises(SourceBlocked):
            book_data(orderbook("101"),"103",COND)
        with self.assertRaises(SourceBlocked):
            book_data(orderbook("101",mid="0x"+ "8"*64),"101",COND)

    def test_unavailable_side_is_not_zero_competition(self):
        b=orderbook("101");b["asks"]=[]
        with self.assertRaises(SourceBlocked):
            book_data(b,"101",COND)

if __name__=="__main__":
    unittest.main()
