import unittest

from radar.options_v21_exec_mapping import evaluate_public_mapping


class OptionsV21ExecMappingTests(unittest.TestCase):
    def _spot(self,spread=0.1):
        return {
            "long_mapping_candidate":{
                "spread_bps":spread,
            }
        }

    def test_long_generic_mexc_taker_proxy_exceeds_base10_with_positive_spread(self):
        r=evaluate_public_mapping(
            spot_receipt=self._spot(0.1),
            futures_spread_bps=0.1,
            short_funding_burden_bps=0.0,
        )
        self.assertGreater(r["long_spot"]["public_proxy_round_trip_bps"],10.0)
        self.assertFalse(r["long_spot"]["base10_compatible_public_proxy"])
        self.assertTrue(r["long_spot"]["stress20_compatible_public_proxy"])

    def test_short_reference_taker_proxy_can_pass_stress20_but_not_base10(self):
        r=evaluate_public_mapping(
            spot_receipt=self._spot(0.1),
            futures_spread_bps=0.1,
            short_funding_burden_bps=1.0,
        )
        self.assertGreater(r["short_perp"]["public_proxy_round_trip_bps"],10.0)
        self.assertLessEqual(r["short_perp"]["public_proxy_round_trip_bps"],20.0)
        self.assertFalse(r["short_perp"]["base10_compatible_public_proxy"])
        self.assertTrue(r["short_perp"]["stress20_compatible_public_proxy"])

    def test_high_funding_burden_blocks_stress20(self):
        r=evaluate_public_mapping(
            spot_receipt=self._spot(0.1),
            futures_spread_bps=0.1,
            short_funding_burden_bps=5.0,
        )
        self.assertGreater(r["short_perp"]["public_proxy_round_trip_bps"],20.0)
        self.assertFalse(r["short_perp"]["stress20_compatible_public_proxy"])

    def test_public_evaluator_never_claims_account_or_execution_authority(self):
        r=evaluate_public_mapping(
            spot_receipt=self._spot(0.1),
            futures_spread_bps=0.1,
            short_funding_burden_bps=0.0,
        )
        self.assertFalse(r["account_specific_fee_verified"])
        self.assertFalse(r["authenticated_transport_verified"])
        self.assertFalse(r["execution_authority_present"])
        self.assertFalse(r["orders_created"])
        self.assertFalse(r["capital_enabled"])


if __name__=="__main__":
    unittest.main()
