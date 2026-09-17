import json
from pathlib import Path
import tempfile
import unittest

from radar.dashboard import HTML, build_control_room_state


class DashboardTests(unittest.TestCase):
    def _paths(self, root: Path):
        registry = root / "registry.json"
        status = root / "status.json"
        events = root / "events.jsonl"
        status.write_text(
            json.dumps({
                "health": "OK",
                "provider": "MEXC_FUTURES_PUBLIC",
                "cycle": 7,
                "universe": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"],
            }),
            encoding="utf-8",
        )
        events.write_text(json.dumps({"ts_utc": "2026-09-17T00:00:00Z", "event_type": "TEST", "payload": {}}) + "\n", encoding="utf-8")
        return registry, status, events

    def test_v3_focus_comes_from_registry_and_closed_shadow_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            focus = [
                "ETF-CME-INSTFLOW-001",
                "BNB-LAUNCHPOOL-DEMAND-001",
                "OPTIONS-SPOTPERP-001-V2.1",
                "HTF-DONCHIAN-DH02-6H",
            ]
            registry.write_text(
                json.dumps({
                    "registry_version": "2.0-test",
                    "governance": "V3_TEST",
                    "focus_strategy_ids": focus,
                    "candidates": [
                        {"strategy_id": focus[0], "scientific_tier": 2, "deployment_state": "SHADOW_EXECUTION_RESEARCH", "shadow_allowed": True, "micro_live_allowed_now": False},
                        {"strategy_id": focus[1], "scientific_tier": 2, "deployment_state": "PROSPECTIVE_WATCHER", "shadow_allowed": True, "micro_live_allowed_now": False},
                        {"strategy_id": focus[2], "scientific_tier": 2, "deployment_state": "SHADOW_PREFLIGHT", "shadow_allowed": True, "micro_live_allowed_now": False},
                        {"strategy_id": focus[3], "scientific_tier": 2, "deployment_state": "BLOCKED_CLOSED_SHADOW_READINESS_FAIL_2026", "shadow_allowed": False, "micro_live_allowed_now": False},
                        {"strategy_id": "BTC-OPTIONS-EXPIRY-REVERSAL-001", "scientific_tier": 4, "deployment_state": "BLOCKED", "shadow_allowed": False, "micro_live_allowed_now": False},
                    ],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["system"]["health"], "OK")
            self.assertEqual(state["registry_version"], "2.0-test")
            self.assertEqual(state["registry"]["focus_loaded"], 4)
            self.assertTrue(state["registry"]["ok"])
            self.assertEqual([b["strategy_id"] for b in state["bots"]], focus)
            self.assertEqual(state["focus_counts"]["SHADOW"], 3)
            self.assertEqual(state["focus_counts"]["BLOCKED"], 1)
            self.assertEqual(state["focus_counts"]["ARMED"], 0)
            donchian = next(b for b in state["bots"] if b["strategy_id"] == "HTF-DONCHIAN-DH02-6H")
            self.assertEqual(donchian["operating_state"], "BLOCKED")

    def test_missing_registry_fails_closed_instead_of_showing_empty_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _registry, status, events = self._paths(root)
            missing = root / "missing.json"
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(missing))
            self.assertEqual(state["system"]["market_health"], "OK")
            self.assertEqual(state["system"]["health"], "REGISTRY_DESYNC")
            self.assertFalse(state["registry"]["ok"])
            self.assertEqual(state["bots"], [])

    def test_dashboard_html_has_live_state_endpoint(self):
        self.assertIn("/api/state", HTML)
        self.assertIn("Crypto Edge Radar", HTML)
        self.assertIn("RISK FIREWALL", HTML)
        self.assertIn("REGISTRY DESYNC", HTML)


if __name__ == "__main__":
    unittest.main()
