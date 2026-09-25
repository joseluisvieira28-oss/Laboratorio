from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.mexc_universal_dispatcher_v01 import build_dispatch_plan


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "execution" / "CANDIDATE_EXECUTION_MANIFESTS_V1.json"


class UniversalDispatcherTests(unittest.TestCase):
    def _signal(self, candidate_id: str, direction: str, include_key: bool = True) -> Path:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "signal.json"
        payload = {"strategy_id": candidate_id, "direction": direction}
        if include_key:
            payload["immutable_signal_key"] = f"{candidate_id}:{direction}:TEST"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_options_long_delegates_to_existing_spot_executor(self) -> None:
        plan = build_dispatch_plan(
            MANIFESTS,
            self._signal("OPTIONS-SPOTPERP-001-V2.1", "LONG"),
        )
        self.assertTrue(plan["pass"])
        self.assertEqual(plan["venue"], "MEXC_SPOT")
        self.assertEqual(plan["symbol"], "BTCUSDT")
        self.assertEqual(
            plan["executor_script"],
            "crypto_edge_radar/scripts/mexc_tier2_spot_executor.py",
        )
        self.assertEqual(plan["max_notional_usdt"], 10)

    def test_options_short_remains_locked(self) -> None:
        plan = build_dispatch_plan(
            MANIFESTS,
            self._signal("OPTIONS-SPOTPERP-001-V2.1", "SHORT"),
        )
        self.assertFalse(plan["pass"])
        self.assertEqual(plan["status"], "EXECUTION_LOCKED")
        self.assertIn(
            "UNATTENDED_ACCOUNT_IDENTITY_BINDING_NOT_YET_PRESERVED",
            plan["blockers"],
        )

    def test_bnb_prebuilt_manifest_cannot_create_order_path(self) -> None:
        plan = build_dispatch_plan(
            MANIFESTS,
            self._signal("BNB-LAUNCHPOOL-DEMAND-001", "LONG"),
        )
        self.assertFalse(plan["pass"])
        self.assertEqual(plan["status"], "EXECUTION_LOCKED")
        self.assertEqual(plan["execution_state"], "PREPARED_LOCKED")

    def test_ced1d_prebuilt_manifest_remains_locked_while_source_retries(self) -> None:
        plan = build_dispatch_plan(
            MANIFESTS,
            self._signal("CED1D-0031", "CONTINUATION"),
        )
        self.assertFalse(plan["pass"])
        self.assertEqual(plan["status"], "EXECUTION_LOCKED")
        self.assertEqual(plan["execution_state"], "PREPARED_LOCKED")

    def test_forward_gate_candidates_cannot_delegate(self) -> None:
        for candidate in (
            "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
            "HTF-DH03-12H-STANDALONE-FORWARD-V1",
            "EMA6H-50X200-REGIME-DEPENDENCY-001",
        ):
            with self.subTest(candidate=candidate):
                plan = build_dispatch_plan(MANIFESTS, self._signal(candidate, "LONG"))
                self.assertFalse(plan["pass"])
                self.assertEqual(plan["status"], "EXECUTION_LOCKED")

    def test_etf_no_peek_cannot_delegate(self) -> None:
        plan = build_dispatch_plan(
            MANIFESTS,
            self._signal("ETF-CME-INSTFLOW-001", "LONG"),
        )
        self.assertFalse(plan["pass"])
        self.assertEqual(plan["execution_state"], "SCIENCE_PROTECTED")

    def test_cirv_has_no_order_path(self) -> None:
        plan = build_dispatch_plan(
            MANIFESTS,
            self._signal(
                "CRYPTO-INTRAWEEK-RV-001 / CIRV-HAR-DOW-BTCETH-001",
                "NONE",
            ),
        )
        self.assertFalse(plan["pass"])
        self.assertEqual(plan["execution_state"], "FORECAST_ONLY")

    def test_unknown_candidate_fails_closed(self) -> None:
        plan = build_dispatch_plan(MANIFESTS, self._signal("NOT-REAL", "LONG"))
        self.assertFalse(plan["pass"])
        self.assertIn("CANDIDATE_MANIFEST_NOT_UNIQUE_OR_MISSING", plan["blockers"])

    def test_missing_signal_key_fails_closed_even_for_ready_lane(self) -> None:
        plan = build_dispatch_plan(
            MANIFESTS,
            self._signal("OPTIONS-SPOTPERP-001-V2.1", "LONG", include_key=False),
        )
        self.assertFalse(plan["pass"])
        self.assertIn("IMMUTABLE_SIGNAL_KEY_MISSING", plan["blockers"])

    def test_registry_is_deny_by_default_and_only_one_route_ready(self) -> None:
        registry = json.loads(MANIFESTS.read_text(encoding="utf-8"))
        self.assertIs(registry["deny_by_default"], True)
        ready = []
        for candidate in registry["candidates"]:
            for direction, route in candidate["routes"].items():
                if route.get("adapter_status") == "READY":
                    ready.append((candidate["candidate_id"], direction))
        self.assertEqual(ready, [("OPTIONS-SPOTPERP-001-V2.1", "LONG")])


if __name__ == "__main__":
    unittest.main()
