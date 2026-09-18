import unittest

from radar.canary_wake_check import CanaryWakeError, validate_public_shadow_state


class CanaryWakeCheckTests(unittest.TestCase):
    def _state(self, **changes):
        state={
            "health":"OK",
            "mode":"PUBLIC_SHADOW_ONLY",
            "evidence_backend":"postgres",
            "evidence_chain_ok":True,
            "authenticated_exchange_api_used":False,
            "orders_created":False,
            "exchange_mutation_performed":False,
            "live_capital_enabled":False,
            "tfg":{"status":"IDLE_NO_NEW_CERTIFIABLE_12H_BOUNDARY"},
            "options_v21":{"status":"WAITING_FIRST_FULL_POST_FREEZE_SIGNAL_DAY"},
        }
        state.update(changes)
        return state

    def test_valid_public_shadow_state_passes(self):
        receipt=validate_public_shadow_state(self._state())
        self.assertEqual(receipt["status"],"PASS_PUBLIC_BOUNDARY_WAKE")
        self.assertFalse(receipt["orders_created"])

    def test_any_order_or_capital_flag_fails_closed(self):
        with self.assertRaises(CanaryWakeError):
            validate_public_shadow_state(self._state(orders_created=True))
        with self.assertRaises(CanaryWakeError):
            validate_public_shadow_state(self._state(live_capital_enabled=True))

    def test_missing_forward_engine_state_fails_closed(self):
        state=self._state()
        del state["tfg"]
        with self.assertRaises(CanaryWakeError):
            validate_public_shadow_state(state)

    def test_unhealthy_canary_fails_closed(self):
        with self.assertRaises(CanaryWakeError):
            validate_public_shadow_state(self._state(health="FAIL_CLOSED"))


if __name__=="__main__":
    unittest.main()
