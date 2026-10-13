"""No-market tests for new prospective 2026-10-15 gate."""
import unittest
from research.convex_sol_bnb_gates_v01 import forward_custody_gate as f

def event(sym="SOLUSDT",bar=f.BOUNDARY_MS,lag=1000):
    tf=f.TF_MS[sym]
    return {"symbol":sym,"timeframe_ms":tf,"bar_open_ms":bar,
            "witness_ms":bar+tf+lag,"side":"LONG",
            "source_raw_sha256":"a"*64,"signal_proof_sha256":"b"*64,
            "warmup_completed_bar_count":200,
            "source_observed_before_outcome":True,
            "signed_or_append_only_receipt":True}

class ProspectiveOnly(unittest.TestCase):
    def test_frozen_boundary_and_source_witness(self):
        self.assertEqual(f.BOUNDARY_MS,1792022400000)
        self.assertTrue(f.validate_future_signal(event()).startswith("FUTURE_SOURCE"))
        self.assertTrue(f.validate_future_signal(event("BNBUSDT")).startswith("FUTURE_SOURCE"))
        self.assertEqual(f.validate_future_signal(event(bar=f.BOUNDARY_MS-f.TF_MS["SOLUSDT"])),
                         "PREBOUNDARY_OR_UNALIGNED_BAR")
        self.assertEqual(f.validate_future_signal(event(lag=121000)),
                         "NOT_CONTEMPORANEOUS_TO_COMPLETED_BAR")

    def test_reject_retroactive_backfill(self):
        q=event()
        q["source_observed_before_outcome"]=False
        self.assertEqual(f.validate_future_signal(q),"HINDSIGHT_OR_UNSEALED_EVENT")
        q=event()
        q["signed_or_append_only_receipt"]=False
        self.assertEqual(f.validate_future_signal(q),"NO_IMMUTABLE_WITNESS")
        q=event()
        q["warmup_completed_bar_count"]=199
        self.assertEqual(f.validate_future_signal(q),"INSUFFICIENT_CONTEMPORANEOUS_WARMUP")

    def test_unbacked_quote_is_not_forward_fill(self):
        e=event()
        t=e["witness_ms"]+200
        quote={"venue":"MEXC_FUTURES_PUBLIC","market_timestamp_ms":t,
               "locally_received_ms":t+50,"bid":100,"ask":100.02,
               "visible_contract_qty":1000,"raw_response_sha256":"c"*64}
        self.assertEqual(f.validate_quote_after_signal(e,quote),
                         "SOURCE_ONLY_ELIGIBLE_NOT_AN_EXECUTABLE_FILL")
        quote["locally_received_ms"]=t+5000
        self.assertEqual(f.validate_quote_after_signal(e,quote),
                         "PUBLIC_QUOTE_STALE_OR_MISSING_TIME")
        quote["locally_received_ms"]=t+50;quote["market_timestamp_ms"]=e["witness_ms"]-10
        self.assertEqual(f.validate_quote_after_signal(e,quote),
                         "QUOTE_PRECEDES_SIGNAL_DECISION")

    def test_sample_counter_not_revenue_go(self):
        x=f.checkpoint([event()])
        self.assertEqual(x["pair_gate"]["SOLUSDT"]["valid_sealed_signals"],1)
        self.assertFalse(x["pair_gate"]["SOLUSDT"]["minimum_source_volume_met"])
        self.assertFalse(x["economic_profitability_proven"])
        self.assertEqual(x["trading_authority"],"NONE")

if __name__=="__main__":unittest.main()
