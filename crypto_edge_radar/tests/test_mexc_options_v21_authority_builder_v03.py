from __future__ import annotations
import unittest
from scripts.mexc_options_v21_authority_builder_v03 import build_long,build_short,AuthorityBuildError

class BuilderTests(unittest.TestCase):
    def _signal(self,direction):
        return {"strategy_id":"OPTIONS-SPOTPERP-001-V2.1","canonical":True,"source_healthy":True,"radar_motor_healthy":True,
                "information_safe_time_passed":True,"materialization_latency_seconds":10.0,"signal_direction":direction,
                "immutable_signal_key":"OPTIONS-SPOTPERP-001:V2.1:2026-09-24","entry_target_utc":"2026-09-25T00:00:00Z","exit_target_utc":"2026-09-26T00:00:00Z"}
    def _long_template(self):
        return {"status":"TEMPLATE_NOT_AUTHORITY","policy_id":"TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24","direction":"LONG"}
    def _short_template(self):
        return {"status":"TEMPLATE_NOT_AUTHORITY","policy_id":"TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24","direction":"SHORT"}
    def test_long_builder_activates_only_matching_signal(self):
        pf={"pass":True,"candidate_feasibility":{"OPTIONS-SPOTPERP-001-V2.1-LONG":{"pass":True}}}
        out=build_long(template=self._long_template(),signal=self._signal("LONG"),spot_preflight=pf)
        self.assertEqual(out["status"],"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY")
        self.assertTrue(out["client_order_id"].startswith("optl-"))
        self.assertTrue(out["authority_instance_sha256"])
        with self.assertRaises(AuthorityBuildError):
            build_long(template=self._long_template(),signal=self._signal("SHORT"),spot_preflight=pf)
    def test_short_builder_uses_venue_minimum_and_stress20(self):
        pf={"pass":True,"checks":{
            "contract":{"min_contract_volume":1.0,"contract_volume_step":1.0,"contract_size_base":0.0001,"reference_price":85000.0},
            "fees":{"effective_taker_fee_bps_for_execution_model":8.0},
            "funding":{"funding_rate":0.00001,"collect_cycle_hours":8}
        }}
        out=build_short(template=self._short_template(),signal=self._signal("SHORT"),futures_preflight=pf)
        self.assertEqual(out["volume_contracts"],1)
        self.assertAlmostEqual(out["projected_round_trip_bps"],16.3)
        self.assertEqual(out["implementation_mapping_review_status"],"ACCEPTED_PRE_ORDER")
    def test_short_builder_blocks_above_10_usdt(self):
        pf={"pass":True,"checks":{
            "contract":{"min_contract_volume":1.0,"contract_volume_step":1.0,"contract_size_base":0.0002,"reference_price":85000.0},
            "fees":{"effective_taker_fee_bps_for_execution_model":8.0},
            "funding":{"funding_rate":0.0,"collect_cycle_hours":8}
        }}
        with self.assertRaises(AuthorityBuildError):
            build_short(template=self._short_template(),signal=self._signal("SHORT"),futures_preflight=pf)

if __name__=="__main__": unittest.main()
