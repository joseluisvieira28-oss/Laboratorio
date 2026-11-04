"""Local fixture smoke checks for settlement audit. No market access."""
import unittest
from decimal import Decimal as D
import audit_settlement

class SettlementMathTests(unittest.TestCase):
    def test_no_friday_fee_on_thursday(self):
        import datetime as dt
        leg={"meta":{"strike":76500,"option_type":"call"}}
        self.assertEqual(audit_settlement.payoff([leg],D(80000),dt.datetime(2026,11,5,8,tzinfo=dt.timezone.utc)),(D(35),D(0)))
    def test_friday_fee_is_charged_once(self):
        import datetime as dt
        leg={"meta":{"strike":76500,"option_type":"call"}}
        gross,fee=audit_settlement.payoff([leg],D(80000),dt.datetime(2026,11,6,8,tzinfo=dt.timezone.utc))
        self.assertEqual(gross,D(35))
        self.assertEqual(fee,D(".12"))
    def test_cost_takes_one_adverse_tick(self):
        leg={"ask":D(1000),"index":D(76500),"meta":{"tick_size":5,"tick_size_steps":[]}}
        self.assertEqual(audit_settlement.entry_cost([leg],1,D(1)),D("10.2795"))
if __name__=="__main__":unittest.main()
