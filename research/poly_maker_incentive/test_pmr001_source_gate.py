import unittest
from datetime import date
from decimal import Decimal
from .pmr001_source_gate import adjudicate, valid_reward_rate, SourceBlocked


TODAY=date(2026,10,13)


def market(mid, minsize="50", rate="10", *,
           active=True, expires="2026-10-31", accepting=True, maxspread="0.03"):
    return {
        "id":str(mid),"slug":"fixture-"+str(mid),"active":active,"closed":False,
        "acceptingOrders":accepting,"enableOrderBook":True,
        "rewardsMinSize":minsize,"rewardsMaxSpread":maxspread,
        "liquidityNum":"9000",
        "clobRewards":[{
            "rewardsDailyRate":rate,"startDate":"2026-10-01","endDate":expires
        }]
    }


class PmrSourceTests(unittest.TestCase):
    def test_positive_market_does_not_become_profitable(self):
        z=adjudicate([[market(1)],[market(2,minsize="120",rate="20")]],TODAY)
        self.assertEqual(z["source_verdict"],"SOURCE_PASS_REWARDS_EXIST_BUT_EDGE_UNPROVEN")
        self.assertEqual(z["qualified_active_reward_markets"],2)
        self.assertEqual(z["eligible_reward_market_count_by_min_shares"]["50"],1)
        self.assertEqual(z["eligible_reward_market_count_by_min_shares"]["100"],1)
        self.assertEqual(z["eligible_reward_market_count_by_min_shares"]["200"],2)
        self.assertEqual(z["sum_market_daily_pools_usdc_sample"],30.0)
        self.assertEqual(z["user_net_income_usdc"],None)
        self.assertFalse(z["orders_created"])
        self.assertEqual(z["trading_authority"],"NONE")

    def test_expired_program_not_eligible(self):
        z=adjudicate([[market(1,expires="2026-10-12")],[]],TODAY)
        self.assertEqual(z["source_verdict"],"SAMPLE_ZERO_ACTIVE_REWARDS")

    def test_zero_size_and_no_book_not_eligible(self):
        z=adjudicate([[market(1,minsize="0")],
                      [dict(market(2),enableOrderBook=False)]],TODAY)
        self.assertEqual(z["qualified_active_reward_markets"],0)

    def test_unknown_reward_date_fails_closed(self):
        p=market(1);p["clobRewards"][0]["startDate"]="not-a-date"
        with self.assertRaises(SourceBlocked):adjudicate([[p],[]],TODAY)

    def test_duplicates_not_doubled(self):
        with self.assertRaises(SourceBlocked):
            adjudicate([[market(1)], [market(1)]],TODAY)

    def test_tiny_reward_only_shared_market_pool(self):
        z=adjudicate([[market(1,minsize="300",rate="2")],[]],TODAY)
        self.assertTrue(z["microcap_100shares_sample_not_eligible"])
        self.assertEqual(z["eligible_reward_market_count_by_min_shares"]["100"],0)
        self.assertEqual(z["sum_market_daily_pools_usdc_sample"],2.0)
        self.assertIsNone(z["user_net_income_usdc"])

    def test_crypto_maker_rebate_ceiling_not_a_profit_claim(self):
        # Fee-equivalent = C*0.07*p*(1-p); crypto rebate share max 0.20
        p=Decimal("0.5")
        fee=Decimal("100")*Decimal("0.07")*p*(1-p)
        rebate=Decimal("0.20")*fee
        self.assertEqual(rebate,Decimal("0.35"))
        # $50 maker fill notional => 0.7% gross rebate, subject to rule/competition.
        self.assertEqual(rebate/(Decimal("100")*p),Decimal("0.007"))

if __name__=="__main__":
    unittest.main()
