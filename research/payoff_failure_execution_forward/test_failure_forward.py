"""Synthetic-only fail-closed tests: cost identity, forward boundary, leakage."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_failure_modes as audit
import forward_boundary_gate as forward
H=forward.H

class AuditAndForwardTests(unittest.TestCase):
    def example_trade(self):
        return {"entry_t":1583020800000,"exit_t":1583024400000,
                "fill":100.,"exit_fill":98.,"qty":1.,"entry_fee":.08,
                "funding_cash":-.01,"net_pnl":-2.1684,
                "reason":"STOP","margin_net_return":-.10}
    def sample_forward(self,n=202):
        b=[{"t":forward.BOUNDARY+i*H,"open":100.,"high":101.,"low":99.,"close":100.,"volume":1000.} for i in range(n)]
        last=b[-1]["t"]+H
        return {"status":"SOURCE_OK","authority":"PUBLIC_READ_ONLY_SHADOW",
                "forward_boundary_utc":"2026-10-14T00:00:00Z",
                "bars":b,"marks":{str(x["t"]):{"open":100.,"high":101.,"low":99.,"close":100.} for x in b},
                "funding":{},"verified_complete_through_ms":last,
                "funding_verified_through_ms":last}

    def test_trade_accounting(self):
        r=audit.partition([self.example_trade()],.0008)
        self.assertEqual(r["trades"],1)
        self.assertAlmostEqual(r["net_usdt"],-2.1684)
        self.assertEqual(r["maximum_consecutive_losses"],1)
    def test_accounting_tamper_fails(self):
        x=self.example_trade();x["net_pnl"]=100
        with self.assertRaisesRegex(ValueError,"CASH_IDENTITY_MISMATCH"):
            audit.partition([x],.0008)
    def test_strict_future_warmup(self):
        with self.assertRaisesRegex(ValueError,"WARMUP_INSUFFICIENT"):
            forward.validate(self.sample_forward(201))
    def test_future_boundary(self):
        data=self.sample_forward()
        b,marks,funds,end=forward.validate(data)
        self.assertEqual(end,data["bars"][-1]["t"])
        self.assertEqual(len(b),202)
    def test_future_preboundary_rejection(self):
        x=self.sample_forward()
        x["bars"][0]["t"]-=H
        with self.assertRaisesRegex(ValueError,"SEALED_PREBOUNDARY"):
            forward.validate(x)
    def test_future_funding_attestation(self):
        x=self.sample_forward()
        x["funding_verified_through_ms"]=0
        with self.assertRaisesRegex(ValueError,"FUNDING_COVERAGE"):
            forward.validate(x)
    def test_future_mark_coverage(self):
        x=self.sample_forward()
        del x["marks"][str(x["bars"][4]["t"])]
        with self.assertRaisesRegex(ValueError,"MARK_COVERAGE"):
            forward.validate(x)
    def test_future_unclosed_bar(self):
        x=self.sample_forward()
        x["verified_complete_through_ms"]=0
        with self.assertRaisesRegex(ValueError,"LAST_BAR_NOT_CONFIRMED"):
            forward.validate(x)
    def test_future_authority_required(self):
        x=self.sample_forward();x["authority"]="TRADE"
        with self.assertRaisesRegex(ValueError,"SOURCE_AUTHORITY"):
            forward.validate(x)
    def test_future_no_ordertype(self):
        x=self.sample_forward()
        o=forward.run(x)
        self.assertEqual(o["trading_authority"],"NONE")
        self.assertIn("PARENT",o["results"]["BASE"])
        self.assertIn("PAYOFF",o["results"]["STRESS"])

if __name__=="__main__":unittest.main()
