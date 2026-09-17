import json
from pathlib import Path
import tempfile
import unittest

from radar.dashboard import HTML, build_control_room_state


class DashboardTests(unittest.TestCase):
    def test_control_room_focus_and_fail_closed_states(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = root / "registry.json"
            status = root / "status.json"
            events = root / "events.jsonl"
            registry.write_text(
                json.dumps(
                    {
                        "registry_version": "test",
                        "governance": "TEST",
                        "candidates": [
                            {
                                "strategy_id": "ETF-CME-INSTFLOW-001",
                                "scientific_tier": 2,
                                "deployment_state": "MICRO_LIVE_CANDIDATE_PENDING_EXECUTION_AND_RISK_CONTRACT",
                                "shadow_allowed": True,
                                "micro_live_allowed_now": False,
                                "blocking_gates": ["risk model not frozen"],
                            },
                            {
                                "strategy_id": "BNB-LAUNCHPOOL-DEMAND-001",
                                "scientific_tier": 3,
                                "deployment_state": "SHADOW_ONLY",
                                "shadow_allowed": True,
                                "micro_live_allowed_now": False,
                            },
                            {
                                "strategy_id": "BTC-OPTIONS-EXPIRY-REVERSAL-001",
                                "scientific_tier": 3,
                                "deployment_state": "SHADOW_ONLY",
                                "shadow_allowed": True,
                                "micro_live_allowed_now": False,
                            },
                            {
                                "strategy_id": "HTF-DH03-12H",
                                "scientific_tier": None,
                                "deployment_state": "DIAGNOSTIC_SHADOW_ONLY",
                                "shadow_allowed": True,
                                "micro_live_allowed_now": False,
                            },
                            {
                                "strategy_id": "REJECTED-X",
                                "scientific_tier": 4,
                                "deployment_state": "BLOCKED",
                                "shadow_allowed": False,
                                "micro_live_allowed_now": False,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            status.write_text(
                json.dumps(
                    {
                        "health": "OK",
                        "provider": "MEXC_FUTURES_PUBLIC",
                        "cycle": 7,
                        "universe": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"],
                    }
                ),
                encoding="utf-8",
            )
            events.write_text(
                json.dumps({"ts_utc": "2026-09-17T00:00:00Z", "event_type": "TEST", "payload": {}}) + "\n",
                encoding="utf-8",
            )

            state = build_control_room_state(
                status_path=str(status),
                notification_path=str(events),
                registry_path=str(registry),
            )
            self.assertEqual(state["system"]["health"], "OK")
            self.assertEqual(state["system"]["market_provider"], "MEXC_FUTURES_PUBLIC")
            self.assertFalse(state["system"]["live_order_transport_enabled"])
            self.assertEqual(len(state["bots"]), 4)
            self.assertEqual(state["focus_counts"]["SHADOW"], 4)
            self.assertEqual(state["focus_counts"]["ARMED"], 0)
            self.assertEqual(len(state["recent_events"]), 1)

    def test_dashboard_html_has_live_state_endpoint(self):
        self.assertIn("/api/state", HTML)
        self.assertIn("Crypto Edge Radar", HTML)
        self.assertIn("Risk firewall", HTML)


if __name__ == "__main__":
    unittest.main()
