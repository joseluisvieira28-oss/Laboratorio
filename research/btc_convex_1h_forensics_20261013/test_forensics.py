"""Synthetic offline tests: frozen accounting provenance, no market outcomes."""
import copy
import unittest
from research.btc_convex_1h_forensics_20261013 import forensics as f

def fixture(*,gap=0):
    opened=1609632000000
    closed=opened+2*86400000
    qty=2.
    ep,xp=100.,110.
    entryfee=ep*qty*.0008
    exitfee=xp*qty*.0008
    price=(xp-ep)*qty
    funding=-.5
    net=price-entryfee-exitfee+funding
    row={"open_t":str(opened),"close_t":str(closed),
         "entry_price":str(ep),"exit_price":str(xp),"qty":str(qty),
         "entry_fees":str(entryfee),"exit_fee":str(exitfee),
         "funding":str(funding),"net_pnl":str(net),
         "price_pnl":str(price),"exit_reason":"STOP_INTRABAR",
         "exit_year":"2021","notional_return_pct":str(100*net/(qty*ep))}
    m={"fees_usdt":entryfee+exitfee+.17,
       "funding_usdt":funding+.1,
       "initial_equity":10000.,
       "cash_equity_usdt":10000+net+.1-.17+gap,
       "terminal_marked_equity_usdt":10000+net+.1-.17+2.+gap,
       "marked_return_pct":(net+.1-.17+2.+gap)/100.,
       "end_position_open":True}
    return m,[row]

class ForensicsSyntheticTests(unittest.TestCase):
    def test_closed_trade_reconciles_open_position(self):
        m,rows=fixture()
        x=f.analyze_arm(m,rows)
        self.assertAlmostEqual(x["closed_net_usdt"],19.164)
        self.assertAlmostEqual(x["open_position_residual"]["total_fees_minus_closed_fees_usdt"],.17)
        self.assertAlmostEqual(x["open_position_residual"]["total_funding_minus_closed_funding_usdt"],.1)
        self.assertTrue(x["open_position_residual"]["verified_cashflow_identity"])

    def test_zero_fee_and_funding_are_not_tradable_returns(self):
        m,rows=fixture()
        x=f.analyze_arm(m,rows)["cost_sensitivity_on_fixed_closed_trades"]
        self.assertGreater(x["FEE_ZERO_ACCOUNTING_ONLY"]["closed_unchanged_ledger_pnl_usdt"],
                           x["AS_RECORDED"]["closed_unchanged_ledger_pnl_usdt"])
        self.assertGreater(x["FUNDING_ZERO_ACCOUNTING_ONLY"]["closed_unchanged_ledger_pnl_usdt"],
                           x["AS_RECORDED"]["closed_unchanged_ledger_pnl_usdt"])
        self.assertLess(x["EXTRA_10BPS_SIDE_ACCOUNTING_ONLY"]["closed_unchanged_ledger_pnl_usdt"],
                        x["AS_RECORDED"]["closed_unchanged_ledger_pnl_usdt"])

    def test_reject_falsified_net_accounting(self):
        m,rows=fixture()
        rows[0]["net_pnl"]="900"
        with self.assertRaisesRegex(ValueError,"LEDGER_ARITHMETIC_FAILED"):
            f.analyze_arm(m,rows)

    def test_reject_missing_open_account_reconciliation(self):
        m,rows=fixture(gap=10)
        with self.assertRaisesRegex(ValueError,"ACCOUNT_LEDGER"):
            f.analyze_arm(m,rows)

    def test_reject_fake_closed_year_and_date(self):
        m,rows=fixture()
        rows[0]["exit_year"]="2025"
        with self.assertRaisesRegex(ValueError,"YEAR_ATTRIBUTION_BAD"):
            f.analyze_arm(m,rows)

    def test_reject_fake_entry_fee_or_trade_qty(self):
        m,rows=fixture()
        rows[0]["entry_fees"]="0.0"
        rows[0]["net_pnl"]=str(float(rows[0]["net_pnl"])+.16)
        rows[0]["notional_return_pct"]=str(float(rows[0]["net_pnl"])/200*100)
        with self.assertRaisesRegex(ValueError,"ENTRY_FEE_ASSUMPTION_MISMATCH"):
            f.analyze_arm(m,rows)

if __name__=="__main__":
    unittest.main()
