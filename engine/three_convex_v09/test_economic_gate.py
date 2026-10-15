import unittest
from engine.three_convex_v09.economic_gate import economic_verdict,EconomicHalt

SHA="a"*40

class EconomyTests(unittest.TestCase):
    def check(self,rs=None,verified=False,now="2026-12-25T00:00:00+00:00"):
        return economic_verdict(rs if rs is not None else [],now_iso=now,
            freeze_git_sha=SHA,independent_venue_validation=verified)
    def test_zero_real_verified_trades_is_no_go(self):
        x=self.check()
        self.assertEqual(x["verdict"],"NO_GO")
        self.assertEqual(x["reason"],"INDEPENDENT_EXCHANGE_COST_AND_FILL_RECEIPTS_NOT_VERIFIED")
    def test_manual_fake_ninety_trade_rows_do_not_enable_go(self):
        self.assertEqual(self.check([{}]*90)["verdict"],"NO_GO")
    def test_ninety_trades_after_one_day_still_not_sixty_days(self):
        self.assertEqual(self.check([{}]*90,True,now="2026-10-17T00:00:00+00:00")["reason"],
                         "MINIMUM_60_DAYS_FORWARD_NOT_ELAPSED")
    def test_unverified_source_rejected_before_any_profit_calcs(self):
        self.assertEqual(self.check([{"realized_net_usdt":999999}]*100)["verdict"],"NO_GO")
    def test_incomplete_evidence_fails_closed(self):
        with self.assertRaisesRegex(EconomicHalt,"MISSING_TRADE_RECEIPT_EVIDENCE"):
            self.check([{}]*90,True)
    def test_forged_date_before_freeze_rejected(self):
        lanes=["SOL_CONVEX_NATIVE_5M","SOL_CONVEX_1H","BNB_CONVEX_4H"]
        rs=[]
        for i in range(90):
            rs.append({
                "lane":lanes[i%3],"entry_utc":"2026-10-14T00:00:00+00:00",
                "exit_utc":"2026-10-15T00:00:00+00:00",
                "external_oid":str(i),"realized_net_usdt":"0.1",
                "fee_receipt_independently_confirmed":True,
                "funding_independently_confirmed":True,
                "fill_and_close_independently_confirmed":True,
                "frozen_strategy_id":"CONVEX_V5_MICRO_1LOT_10X_V09",
            })
        with self.assertRaisesRegex(EconomicHalt,"PRE_FREEZE"):
            self.check(rs,True)
if __name__=="__main__":unittest.main()
