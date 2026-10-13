import unittest
from decimal import Decimal
from .pmr001_real_cash_truth import SOURCES, MARKETS, external_account_truth, market_necessary_share, report

class MarketMakerCashTruthTests(unittest.TestCase):
    def test_live_realized_net_loss(self):
        o=external_account_truth(SOURCES[0])
        self.assertEqual(o["gross_rewards_paid_usd"],"349.45")
        self.assertEqual(o["inventory_pnl_usd"],"-479.35")
        self.assertEqual(o["net_reward_plus_inventory_usd"],"-129.90")
        self.assertFalse(o["is_profit_proof_for_our_lab"])

    def test_live_marked_net_loss_not_confused_with_realized(self):
        o=external_account_truth(SOURCES[1])
        self.assertEqual(o["net_reward_plus_inventory_usd"],"-10.81")
        self.assertIn("marked",o["pnl_basis"])

    def test_no_measured_pnl_or_rewards_claimed(self):
        o=report()
        self.assertIsNone(o["claimed_profit_usd"])
        self.assertEqual(o["operator_cases_independently_audited"],0)
        self.assertEqual(o["trading_authority"],"NONE")
        self.assertFalse(o["orders_created"])
        self.assertEqual(o["verdict"],"NO_VERIFIED_PROFIT_EVIDENCE_FOR_PMR001_OR_OUR_ACCOUNT")

    def test_reward_single_market_daily_floor_is_not_guarantee(self):
        r=market_necessary_share(MARKETS[2],Decimal("0.00"))
        self.assertEqual(r["required_market_reward_share_pct_to_cover_loss_and_reach_1usd_floor"],"11.1111")
        self.assertIsNone(r["actual_individual_reward_share_pct"])

    def test_one_adverse_fill_five_cents_on_fifty_shares(self):
        r=market_necessary_share(MARKETS[2],Decimal("0.05"))
        self.assertEqual(r["scenario_one_leg_loss_usd"],"2.50")
        self.assertEqual(r["required_market_reward_share_pct_to_cover_loss_and_reach_1usd_floor"],"27.7778")
        self.assertTrue(r["is_assumed_not_measured"])

    def test_large_market_not_proven_either(self):
        r=market_necessary_share(MARKETS[0],Decimal("0.05"))
        self.assertEqual(r["required_market_reward_share_pct_to_cover_loss_and_reach_1usd_floor"],"1.1261")

    def test_scenarios_have_no_fill_prob_or_user_profit(self):
        o=report()
        for rows in o["one_adverse_fill_break_even_sensitivity"].values():
            for x in rows:
                self.assertIsNone(x["actual_fill_likelihood"])
                self.assertIsNone(x["actual_net_profit"])

if __name__=="__main__":unittest.main()
