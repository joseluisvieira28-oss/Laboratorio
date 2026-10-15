"""No-network / no-broker / no-live RC33 pre-certification regressions."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from synthetic_stop_contract import (
    reconcile_mock_snapshot, uncertain_post_action, required_external_proofs,
)
from rc33_local_source_preflight import offline_preflight


def model(**kwargs):
    position = {"positionId": 123, "symbol": "ETH_USDT",
                "positionType": 1, "holdVol": 2}
    stop = {"positionId": 123, "symbol": "ETH_USDT",
            "isFinished": 0, "vol": 2, "stopLossPrice": 96, "takeProfitPrice": 0}
    opts = dict(position=position, stops=[stop], symbol="ETH_USDT", position_id=123,
                expected_volume=2, expected_stop_price=96, price_unit=0.01,
                snapshot_age_seconds=1)
    opts.update(kwargs)
    return reconcile_mock_snapshot(**opts)


class SyntheticStopContractTests(unittest.TestCase):
    def test_mock_good_readback_is_never_broker_certification(self):
        result = model()
        self.assertTrue(result.mock_readback_accepted)
        self.assertEqual(result.code, "MOCK_STOP_READBACK_SHAPE_ACCEPTED_ONLY")
        self.assertFalse(result.live_go)
        self.assertFalse(result.brokerage_certified)

    def test_missing_or_multiple_stops_blocks(self):
        self.assertEqual(model(stops=[]).code, "BROKER_STOP_MISSING_OR_MULTIPLE")
        self.assertEqual(model(stops=model_stops_twice()).code, "BROKER_STOP_MISSING_OR_MULTIPLE")

    def test_stop_coverage_under_current_hold_blocks(self):
        result = model(stops=[{"positionId": 123, "symbol": "ETH_USDT",
                              "isFinished": 0, "vol": 1, "stopLossPrice": 96}])
        self.assertEqual(result.code, "STOP_NOT_COVERING_FULL_POSITION")

    def test_partial_fill_is_separate_unproven_gate(self):
        self.assertEqual(model(partial_fill=True).code,
                         "PARTIAL_FILL_REQUIRES_EXPLICIT_COVERAGE_RECONCILIATION")

    def test_wrong_position_id_and_symbol_block(self):
        self.assertEqual(model(position_id=124).code, "BROKER_POSITION_IDENTITY_MISMATCH")
        self.assertEqual(model(symbol="SOL_USDT").code, "BROKER_POSITION_IDENTITY_MISMATCH")

    def test_wrong_position_direction_blocks(self):
        p = {"positionId": 123, "symbol": "ETH_USDT",
             "positionType": 2, "holdVol": 2}
        self.assertEqual(model(position=p).code, "UNSUPPORTED_POSITION_SIDE")

    def test_missing_held_position_blocks(self):
        self.assertEqual(model(position=None).code, "UNVERIFIED_POSITION_OR_GEOMETRY")

    def test_position_volume_difference_blocks(self):
        p = {"positionId": 123, "symbol": "ETH_USDT",
             "positionType": 1, "holdVol": 1}
        self.assertEqual(model(position=p).code, "POSITION_VOLUME_MISMATCH")

    def test_unexpected_take_profit_blocks(self):
        st = {"positionId": 123, "symbol": "ETH_USDT", "isFinished": 0,
              "vol": 2, "stopLossPrice": 96, "takeProfitPrice": 101}
        self.assertEqual(model(stops=[st]).code, "UNEXPECTED_TAKE_PROFIT")

    def test_stop_price_mismatch_blocks(self):
        self.assertEqual(model(expected_stop_price=94).code, "STOP_READBACK_PRICE_MISMATCH")

    def test_stale_broker_readback_blocks(self):
        self.assertEqual(model(snapshot_age_seconds=5.1).code, "BROKER_SNAPSHOT_STALE")
        self.assertEqual(model(snapshot_age_seconds=-0.1).code, "BROKER_SNAPSHOT_STALE")

    def test_pending_stop_write_cannot_be_auto_accepted(self):
        self.assertEqual(model(pending_mutation=True).code,
                         "UNKNOWN_BROKER_OUTCOME_NO_BLIND_RETRY")

    def test_unknown_write_or_restart_halts(self):
        self.assertEqual(model(ambiguous_exchange_response=True).code,
                         "UNKNOWN_BROKER_OUTCOME_NO_BLIND_RETRY")
        self.assertEqual(model(after_restart=True, pending_mutation=True).code,
                         "RESTART_UNRESOLVED_MUTATION_NO_RESEND")

    def test_no_blind_post_replay_even_on_recovery(self):
        for outcome in ("TIMEOUT", "UNKNOWN", "HTTP_503", "RECONCILED_BROKER_RECEIPT"):
            result = uncertain_post_action(outcome, pending_journal=True)
            self.assertEqual(result, "HALT_AND_RECONCILE_NO_RESEND")

    def test_unseen_exit_and_stop_trigger_still_require_real_proof(self):
        req = required_external_proofs()
        self.assertIn("STOP_AMEND_AND_STOP_TRIGGER_SETTLEMENT", req)
        self.assertIn("VENUE_NATIVE_STOP_NOT_ATOMICALLY_CERTIFIED", req)
        self.assertGreaterEqual(len(req), 8)

    def test_no_credentials_network_or_live_gateway_in_reference_module(self):
        source = Path(__file__).with_name("synthetic_stop_contract.py").read_text()
        for forbidden in ("requests.", "urlopen(", "MEXC_API_KEY", "LIVE_AUTHORITY.json",
                          "os.environ", "subprocess.run(", "socket.connect("):
            self.assertNotIn(forbidden, source)

    def test_real_local_code_missing_never_passes(self):
        with tempfile.TemporaryDirectory() as td:
            result = offline_preflight(Path(td))
        self.assertFalse(result["engine"]["exists"])
        self.assertFalse(result["transport"]["exists"])
        self.assertFalse(result["local_disarmed_snapshot"])
        self.assertEqual(result["installation_certification"], "NOT_CERTIFIED")
        self.assertFalse(result["live_go"])
        self.assertEqual(result["broker_account"], "NOT_QUERIED")

    def test_preflight_does_not_execute_target_code(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            app = root / "app"
            app.mkdir()
            source = "raise RuntimeError('IF_YOU_RUN_ME_YOU_MUTATE')\ndef validated_stop(): pass\n"
            (app / "engine.py").write_text(source)
            (app / "mexc_futures.py").write_text("def stops(): pass\n")
            (root / "state").mkdir()
            (root / "state" / "KILL_SWITCH").touch()
            (root / "state" / "status.json").write_text(
                json.dumps({"mode": "OBSERVE_ONLY", "positions": 0, "pending_entries": 0})
            )
            result = offline_preflight(root)
        self.assertTrue(result["engine"]["exists"])
        self.assertEqual(result["engine"]["syntax"], "PARSEABLE_ONLY")
        self.assertFalse(result["engine"]["sha256_matches_user_receipt"])
        self.assertTrue(result["local_disarmed_snapshot"])
        self.assertFalse(result["live_go"])

    def test_observe_only_without_kill_is_not_disarmed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "state").mkdir()
            (root / "state" / "status.json").write_text(
                json.dumps({"mode": "OBSERVE_ONLY", "positions": 0, "pending_entries": 0})
            )
            self.assertFalse(offline_preflight(root)["local_disarmed_snapshot"])

    def test_live_authority_present_denies_disarmed_even_with_kill(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "state").mkdir()
            (root / "state" / "KILL_SWITCH").touch()
            (root / "state" / "LIVE_AUTHORITY.json").write_text("{}")
            (root / "state" / "status.json").write_text(
                json.dumps({"mode": "OBSERVE_ONLY", "positions": 0, "pending_entries": 0})
            )
            self.assertFalse(offline_preflight(root)["local_disarmed_snapshot"])


def model_stops_twice():
    st = {"positionId": 123, "symbol": "ETH_USDT",
          "isFinished": 0, "vol": 2, "stopLossPrice": 96, "takeProfitPrice": 0}
    return [st, dict(st)]


if __name__ == "__main__":
    unittest.main()
