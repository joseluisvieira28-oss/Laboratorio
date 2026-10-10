"""G2 strictly synthetic source only test suite."""
import copy,json,unittest
from pathlib import Path
from rw_hl_g2_source_variation_census_v01 import census,verify_freeze,SourceError,ROOT

def frozen():
    return json.loads((ROOT/"RW_HL_EXITFLOW_001_G2_SOURCE_VARIATION_FREEZE_2026-10-09.json").read_text())

def make_snapshots():
    f=frozen()
    rows=[]
    for i in range(3):
        markets=[]
        for n in range(120):
            oi=100+(i*5 if n<35 else 0)
            funding="-0.0005" if n<20 else "0.0002"
            markets.append({"coin":f"TEST{n:03d}","openInterest":str(oi),
                            "funding":funding,"markPx":"10.0"})
        rows.append({"lab_id":"RW-HL-EXITFLOW-001","ordinal":i+1,"trading_authority":"NONE",
           "historical_outcome":False,"read_utc":f["source_timestamp_order"][i],
           "context":{"valid_public_markets":120,"market_context":markets}})
    return rows

class VariationSourceTests(unittest.TestCase):
    def test_freeze_valid(self):
        self.assertEqual(verify_freeze(frozen())["min_assets_negative_funding_last"],5)
    def test_source_census_pass(self):
        x=census(frozen(),make_snapshots())
        self.assertEqual(x["state"],"PROSPECTIVE_SOURCE_VARIATION_PASS_NOT_EDGE")
        self.assertEqual(x["OI_rising_and_funding_negative_common_markets"],20)
        self.assertFalse(x["economic_edge_assessed"])
    def test_no_rise_and_negative_is_insufficient(self):
        rows=make_snapshots()
        for x in rows[2]["context"]["market_context"]:
            if x["coin"]<"TEST020":x["openInterest"]="100"
        result=census(frozen(),rows)
        self.assertEqual(result["state"],"PROSPECTIVE_SOURCE_VARIATION_INSUFFICIENT")
    def test_duplicated_market_rejected(self):
        rows=make_snapshots()
        rows[1]["context"]["market_context"][1]["coin"]="TEST000"
        with self.assertRaises(SourceError):census(frozen(),rows)
    def test_context_count_rejected(self):
        rows=make_snapshots();rows[0]["context"]["valid_public_markets"]=119
        with self.assertRaises(SourceError):census(frozen(),rows)
    def test_authority_rejected(self):
        rows=make_snapshots();rows[0]["trading_authority"]="LIVE"
        with self.assertRaises(SourceError):census(frozen(),rows)
    def test_protected_outcomes_rejected(self):
        rows=make_snapshots();rows[0]["historical_outcome"]=True
        with self.assertRaises(SourceError):census(frozen(),rows)
    def test_timestamp_binding_rejected(self):
        rows=make_snapshots();rows[0]["read_utc"]="2000-01-01T00:00:00Z"
        with self.assertRaises(SourceError):census(frozen(),rows)
    def test_nonfinite_OI_rejected(self):
        rows=make_snapshots();rows[0]["context"]["market_context"][0]["openInterest"]="nan"
        with self.assertRaises(SourceError):census(frozen(),rows)
    def test_thin_market_rejected(self):
        rows=make_snapshots()
        for row in rows:
            row["context"]["market_context"]=row["context"]["market_context"][:80]
            row["context"]["valid_public_markets"]=80
        self.assertEqual(census(frozen(),rows)["state"],"PROSPECTIVE_SOURCE_VARIATION_INSUFFICIENT")
    def test_universe_overlap(self):
        rows=make_snapshots()
        for x in rows[2]["context"]["market_context"][:20]:
            x["coin"]="REPLACED"+x["coin"]
        self.assertFalse(census(frozen(),rows)["gates"]["UNIVERSE_INTERSECTION"])
    def test_freeze_gate_tampering(self):
        f=frozen();f["source_gate_preregistered"]["min_assets_negative_funding_last"]=0
        with self.assertRaises(SourceError):census(f,make_snapshots())
    def test_no_future_price_or_funding_payoff(self):
        import inspect,rw_hl_g2_source_variation_census_v01 as s
        txt=inspect.getsource(s)
        self.assertNotIn("price_exit",txt)
        self.assertNotIn("realizedPnl",txt)
        self.assertNotIn("place_order(",txt)
if __name__=="__main__":unittest.main()
