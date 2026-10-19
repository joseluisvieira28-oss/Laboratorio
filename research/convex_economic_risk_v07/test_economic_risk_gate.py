"""Hermetic synthetic tests; these observations are not trading evidence."""
import unittest
from research.convex_economic_risk_v07.economic_risk_gate import (
    SCENARIOS_BPS,SIZE_FACTORS,audit_ledger,evaluate,gate
)

def t(t0,year,net=100,entry=100,qty=10):
    # Synthetic net = price pnl minus fees with 0 funding.
    ts={"2023":1680000000000,"2024":1710000000000,"2025":1740000000000}[year]+t0
    fee=1.0
    price=net+2.0
    return {"open_t":ts,"close_t":ts+300000,
            "entry_price":entry,"exit_price":entry+price/qty,"qty":qty,
            "price_pnl":price,"entry_fees":fee,"exit_fee":fee,
            "funding":0.0,"net_pnl":net,"exit_reason":"STOP_INTRABAR"}

def fixture():
    rows=[t(0,"2023",100),t(300000,"2024",-20),t(600000,"2025",80)]
    model={"closed_trades":3,"annual_closed_trade_pnl_usdt":
        {"2023":100,"2024":-20,"2025":80},
        "max_loss_streak":1,"profit_factor":9.0,
        "max_5m_low_stress_dd_pct":-8}
    return rows,model

class AuditContracts(unittest.TestCase):
    def test_frozen_five_extra_costs(self):
        self.assertEqual(SCENARIOS_BPS,(0,6,12,20,40))
    def test_exact_static_position_sizes(self):
        self.assertEqual(SIZE_FACTORS,("0.25","0.50","1.00"))
    def test_decomposition_and_year_census(self):
        rows,model=fixture()
        # Gross gains 180, gross loss 20 = PF 9
        a=evaluate(audit_ledger(rows,"BASE",3,"SOLUSDT"),model,"SOLUSDT","BASE")
        self.assertEqual(a["original_closed_net_USDT"],160)
        self.assertEqual(a["cashflow_year_USDT"]["2024"],-20)
        self.assertEqual(a["trade_year_counts"],{"2023":1,"2024":1,"2025":1})
    def test_costs_original_fees_not_double_charged(self):
        rows,model=fixture()
        a=evaluate(audit_ledger(rows,"BASE",3,"SOLUSDT"),model,"SOLUSDT","BASE")
        self.assertAlmostEqual(a["extra_friction_scenarios"][-1]["adjusted_closed_total_USDT"],148)
    def test_risk_quarter_scales_not_computed_backtest(self):
        rows,model=fixture()
        a=evaluate(audit_ledger(rows,"BASE",3,"SOLUSDT"),model,"SOLUSDT","BASE")
        self.assertAlmostEqual(a["three_static_risk_size_tiers"][0]["static_scaled_original_closed_net_USDT"],40)
        self.assertTrue(a["three_static_risk_size_tiers"][0]["not_a_recalculated_account_or_execution"])
    def test_negative_year_and_tiny_sample_rejected(self):
        rows,model=fixture()
        a=evaluate(audit_ledger(rows,"BASE",3,"SOLUSDT"),model,"SOLUSDT","BASE")
        reasons=gate(a,a)["reasons"]
        self.assertIn("LESS_THAN_60_CLOSED_TRADES",reasons)
        self.assertIn("NEGATIVE_CALENDAR_YEAR_2024",reasons)
    def test_duplicate_entry_fail_closed(self):
        rows,_=fixture()
        rows[1]["open_t"]=rows[0]["open_t"]
        with self.assertRaisesRegex(ValueError,"TRADE_TIME"):
            audit_ledger(rows,"BASE",3,"SOLUSDT")
    def test_missing_ledger_trade_fail_closed(self):
        rows,_=fixture()
        with self.assertRaisesRegex(ValueError,"COUNT"):
            audit_ledger(rows[:2],"BASE",3,"SOLUSDT")
    def test_fee_funding_pnl_mismatch_rejected(self):
        rows,_=fixture()
        rows[0]["entry_fees"]=4
        with self.assertRaisesRegex(ValueError,"DECOMPOSITION"):
            audit_ledger(rows,"BASE",3,"SOLUSDT")
    def test_annual_declared_model_mismatch_rejected(self):
        rows,model=fixture()
        model["annual_closed_trade_pnl_usdt"]["2023"]=101
        with self.assertRaisesRegex(ValueError,"ANNUAL"):
            evaluate(audit_ledger(rows,"BASE",3,"SOLUSDT"),model,"SOLUSDT","BASE")
    def test_future_trade_excluded(self):
        rows,_=fixture()
        rows[2]=t(0,"2025",70);rows[2]["close_t"]=1767225600000+300000
        with self.assertRaisesRegex(ValueError,"SOURCE_2023_25"):
            audit_ledger(rows,"BASE",3,"SOLUSDT")
    def test_nonfinite_rejected(self):
        rows,_=fixture()
        rows[0]["entry_price"]="nan"
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            audit_ledger(rows,"BASE",3,"SOLUSDT")

if __name__=="__main__":
    unittest.main()
