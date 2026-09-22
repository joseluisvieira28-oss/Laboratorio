import json
from pathlib import Path
import tempfile
import unittest

from radar.dashboard import HTML, build_control_room_state


class DashboardTests(unittest.TestCase):
    @staticmethod
    def _healthy_forward_state(errors=None):
        return {
            "health": "OK" if not errors else "DEGRADED_FAIL_CLOSED",
            "checked_at_utc": "2026-09-22T08:00:00Z",
            "errors": errors or {},
            "bnb_launchpool": {"status": "NO_NEW_EVENT"},
            "tfg": {"status": "IDLE_NO_NEW_CERTIFIABLE_12H_BOUNDARY"},
            "options_v21": {"status": "NO_SIGNAL"},
            "etf_cme_signal": {"status": "NO_SIGNAL"},
            "ema6h_regime": {"status": "IDLE_NO_NEW_BOUNDARY"},
        }

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
        (root / "forward_local_supervisor_status.json").write_text(
            json.dumps({"status": "RUNNING", "build_id": "TEST"}),
            encoding="utf-8",
        )
        (root / "forward_local_status.json").write_text(
            json.dumps(self._healthy_forward_state()),
            encoding="utf-8",
        )
        return registry, status, events

    def test_active_registry_focus_excludes_archived_stones_and_keeps_gated_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            focus = [
                "ETF-CME-INSTFLOW-001",
                "BNB-LAUNCHPOOL-DEMAND-001",
                "OPTIONS-SPOTPERP-001-V2.1",
                "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
                "HTF-DH03-12H-STANDALONE-FORWARD-V1",
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
                        {"strategy_id": focus[3], "scientific_tier": 3, "deployment_state": "PROSPECTIVE_FORWARD_SHADOW_OPERATIONAL", "shadow_allowed": True, "micro_live_allowed_now": False},
                        {"strategy_id": focus[4], "scientific_tier": None, "deployment_state": "GATED_SOURCE_PASS__LOCAL_COLLECTOR_BUILDING", "shadow_allowed": False, "micro_live_allowed_now": False},
                    ],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["system"]["health"], "OK")
            self.assertEqual(state["registry_version"], "2.0-test")
            self.assertEqual(state["registry"]["focus_loaded"], 5)
            self.assertTrue(state["registry"]["ok"])
            self.assertEqual([b["strategy_id"] for b in state["bots"]], focus)
            self.assertEqual(state["focus_counts"]["SHADOW"], 4)
            self.assertEqual(state["focus_counts"]["GATED"], 1)
            self.assertEqual(state["focus_counts"]["BLOCKED"], 0)
            self.assertEqual(state["focus_counts"]["ARMED"], 0)
            self.assertIn("mexc_execution", state)
            self.assertEqual(state["mexc_execution"]["exchange_authenticated_preflight"]["status"], "FAIL_CLOSED")
            dh03 = next(b for b in state["bots"] if b["strategy_id"] == "HTF-DH03-12H-STANDALONE-FORWARD-V1")
            self.assertEqual(dh03["operating_state"], "GATED")

    def test_local_forward_registry_shadow_stays_gated_when_supervisor_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            (root / "forward_local_supervisor_status.json").unlink()
            (root / "forward_local_status.json").unlink()
            strategy = "EMA6H-50X200-REGIME-DEPENDENCY-001"
            registry.write_text(
                json.dumps({
                    "registry_version": "3.6-test",
                    "focus_strategy_ids": [strategy],
                    "candidates": [{
                        "strategy_id": strategy,
                        "scientific_tier": 3,
                        "deployment_state": "PROSPECTIVE_PUBLIC_SHADOW_VALIDATED__WAITING_FIRST_ELIGIBLE_BOUNDARY",
                        "shadow_allowed": True,
                        "micro_live_allowed_now": False,
                    }],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["focus_counts"]["GATED"], 1)
            self.assertEqual(state["focus_counts"]["SHADOW"], 0)
            self.assertIn("lacks a completed healthy component cycle", " ".join(state["bots"][0]["blockers"]))

    def test_local_forward_runtime_fail_closed_blocks_all_local_forward_shadow_claims(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            (root / "forward_local_status.json").write_text(
                json.dumps({"health": "DEGRADED_FAIL_CLOSED", "errors": {"ema6h_regime": "source unavailable"}}),
                encoding="utf-8",
            )
            strategy = "EMA6H-50X200-REGIME-DEPENDENCY-001"
            registry.write_text(
                json.dumps({
                    "registry_version": "3.6-test",
                    "focus_strategy_ids": [strategy],
                    "candidates": [{
                        "strategy_id": strategy,
                        "scientific_tier": 3,
                        "deployment_state": "PROSPECTIVE_PUBLIC_SHADOW_VALIDATED__WAITING_FIRST_ELIGIBLE_BOUNDARY",
                        "shadow_allowed": True,
                        "micro_live_allowed_now": False,
                    }],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["focus_counts"]["BLOCKED"], 1)
            self.assertEqual(state["focus_counts"]["SHADOW"], 0)
            self.assertIn("FAIL_CLOSED", " ".join(state["bots"][0]["blockers"]))

    def test_options_source_failure_blocks_only_options_not_other_forward_motors(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            (root / "forward_local_status.json").write_text(
                json.dumps(self._healthy_forward_state({
                    "options_v21": "OptionsV21SourceError:Deribit trade has invalid IV/index"
                })),
                encoding="utf-8",
            )
            focus = [
                "ETF-CME-INSTFLOW-001",
                "BNB-LAUNCHPOOL-DEMAND-001",
                "OPTIONS-SPOTPERP-001-V2.1",
                "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
                "EMA6H-50X200-REGIME-DEPENDENCY-001",
            ]
            registry.write_text(
                json.dumps({
                    "registry_version": "3.6-test",
                    "focus_strategy_ids": focus,
                    "candidates": [
                        {
                            "strategy_id": strategy,
                            "scientific_tier": 2 if strategy in focus[:3] else 3,
                            "deployment_state": "PROSPECTIVE_FORWARD_SHADOW_OPERATIONAL",
                            "shadow_allowed": True,
                            "micro_live_allowed_now": False,
                        }
                        for strategy in focus
                    ],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(
                status_path=str(status),
                notification_path=str(events),
                registry_path=str(registry),
            )
            self.assertEqual(state["system"]["health"], "DEGRADED_FAIL_CLOSED")
            by_id = {b["strategy_id"]: b for b in state["bots"]}
            self.assertEqual(by_id["OPTIONS-SPOTPERP-001-V2.1"]["operating_state"], "BLOCKED")
            self.assertIn(
                "options_v21",
                " ".join(by_id["OPTIONS-SPOTPERP-001-V2.1"]["blockers"]),
            )
            for strategy in (
                "ETF-CME-INSTFLOW-001",
                "BNB-LAUNCHPOOL-DEMAND-001",
                "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
                "EMA6H-50X200-REGIME-DEPENDENCY-001",
            ):
                self.assertEqual(by_id[strategy]["operating_state"], "SHADOW", strategy)
                self.assertIn("MOTOR_HEALTH=OK", by_id[strategy]["runtime_status"])

    def test_shared_evidence_chain_failure_blocks_all_forward_motors(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            (root / "forward_local_status.json").write_text(
                json.dumps({
                    "health": "DEGRADED_FAIL_CLOSED",
                    "errors": {"evidence_chain": "hash mismatch"},
                }),
                encoding="utf-8",
            )
            focus = [
                "ETF-CME-INSTFLOW-001",
                "OPTIONS-SPOTPERP-001-V2.1",
            ]
            registry.write_text(
                json.dumps({
                    "registry_version": "3.6-test",
                    "focus_strategy_ids": focus,
                    "candidates": [
                        {
                            "strategy_id": strategy,
                            "scientific_tier": 2,
                            "deployment_state": "PROSPECTIVE_FORWARD_SHADOW_OPERATIONAL",
                            "shadow_allowed": True,
                            "micro_live_allowed_now": False,
                        }
                        for strategy in focus
                    ],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(
                status_path=str(status),
                notification_path=str(events),
                registry_path=str(registry),
            )
            self.assertEqual(state["focus_counts"]["BLOCKED"], 2)
            for bot in state["bots"]:
                self.assertIn("evidence_chain", " ".join(bot["blockers"]))

    def test_dh03_ready_registry_without_live_collector_stays_gated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            strategy = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
            registry.write_text(
                json.dumps({
                    "registry_version": "3.4-test",
                    "focus_strategy_ids": [strategy],
                    "candidates": [{
                        "strategy_id": strategy,
                        "scientific_tier": None,
                        "deployment_state": "PROSPECTIVE_ARCHIVE_SHADOW_READY__WINDOWS_LOCAL_COLLECTOR_BUILD_PASS",
                        "shadow_allowed": True,
                        "micro_live_allowed_now": False,
                        "blocking_gates": [],
                    }],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(
                status_path=str(status),
                notification_path=str(events),
                registry_path=str(registry),
            )
            self.assertEqual(state["focus_counts"]["GATED"], 1)
            self.assertEqual(state["focus_counts"]["SHADOW"], 0)
            self.assertEqual(state["bots"][0]["runtime_status"], "MISSING")
            self.assertIn("not COLLECTING", " ".join(state["bots"][0]["blockers"]))

    def test_dh03_collecting_runtime_promotes_cockpit_to_shadow_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            strategy = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
            registry.write_text(
                json.dumps({
                    "registry_version": "3.4-test",
                    "focus_strategy_ids": [strategy],
                    "candidates": [{
                        "strategy_id": strategy,
                        "scientific_tier": None,
                        "deployment_state": "PROSPECTIVE_ARCHIVE_SHADOW_READY__WINDOWS_LOCAL_COLLECTOR_BUILD_PASS",
                        "shadow_allowed": True,
                        "micro_live_allowed_now": False,
                    }],
                }),
                encoding="utf-8",
            )
            (root / "dh03_local_status.json").write_text(
                json.dumps({"status": "COLLECTING"}),
                encoding="utf-8",
            )
            state = build_control_room_state(
                status_path=str(status),
                notification_path=str(events),
                registry_path=str(registry),
            )
            self.assertEqual(state["focus_counts"]["SHADOW"], 1)
            self.assertEqual(state["focus_counts"]["GATED"], 0)
            self.assertEqual(state["bots"][0]["runtime_status"], "COLLECTING")

    def test_dh03_fail_closed_runtime_is_blocked_not_shadow(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            strategy = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
            registry.write_text(
                json.dumps({
                    "registry_version": "3.4-test",
                    "focus_strategy_ids": [strategy],
                    "candidates": [{
                        "strategy_id": strategy,
                        "scientific_tier": None,
                        "deployment_state": "PROSPECTIVE_ARCHIVE_SHADOW_READY__WINDOWS_LOCAL_COLLECTOR_BUILD_PASS",
                        "shadow_allowed": True,
                        "micro_live_allowed_now": False,
                    }],
                }),
                encoding="utf-8",
            )
            (root / "dh03_local_status.json").write_text(
                json.dumps({"status": "FAIL_CLOSED", "error": "clock drift"}),
                encoding="utf-8",
            )
            state = build_control_room_state(
                status_path=str(status),
                notification_path=str(events),
                registry_path=str(registry),
            )
            self.assertEqual(state["focus_counts"]["BLOCKED"], 1)
            self.assertEqual(state["focus_counts"]["SHADOW"], 0)
            self.assertIn("FAIL_CLOSED", " ".join(state["bots"][0]["blockers"]))

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

    def test_control_plane_stays_reachable_when_legacy_service_health_is_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            status.write_text(json.dumps({"health": "UNKNOWN", "provider": "CONTROL_PLANE_ONLY"}), encoding="utf-8")
            strategy = "EMA6H-50X200-REGIME-DEPENDENCY-001"
            registry.write_text(
                json.dumps({
                    "registry_version": "3.6-test",
                    "focus_strategy_ids": [strategy],
                    "candidates": [{
                        "strategy_id": strategy,
                        "scientific_tier": 3,
                        "deployment_state": "PROSPECTIVE_PUBLIC_SHADOW_VALIDATED__WAITING_FIRST_ELIGIBLE_BOUNDARY",
                        "shadow_allowed": True,
                        "micro_live_allowed_now": False,
                    }],
                }),
                encoding="utf-8",
            )
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["system"]["health"], "OK")
            self.assertEqual(state["system"]["market_health"], "UNKNOWN")
            self.assertEqual(state["focus_counts"]["SHADOW"], 1)

    def test_dh03_fail_closed_degrades_control_plane_but_dashboard_state_remains_available(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            strategy = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
            registry.write_text(
                json.dumps({
                    "registry_version": "3.6-test",
                    "focus_strategy_ids": [strategy],
                    "candidates": [{
                        "strategy_id": strategy,
                        "scientific_tier": None,
                        "deployment_state": "PROSPECTIVE_ARCHIVE_SHADOW_READY",
                        "shadow_allowed": True,
                        "micro_live_allowed_now": False,
                    }],
                }),
                encoding="utf-8",
            )
            (root / "dh03_local_status.json").write_text(
                json.dumps({"status": "FAIL_CLOSED", "error": "clock drift"}),
                encoding="utf-8",
            )
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["system"]["health"], "DEGRADED_FAIL_CLOSED")
            self.assertEqual(state["focus_counts"]["BLOCKED"], 1)
            self.assertEqual(state["bots"][0]["runtime_status"], "FAIL_CLOSED")

    def test_dashboard_html_has_live_state_endpoint(self):
        self.assertIn("/api/state", HTML)
        self.assertIn("Crypto Edge Radar", HTML)
        self.assertIn("Risk firewall", HTML)
        self.assertIn("Deployment baseline (historical)", HTML)
        self.assertIn("REGISTRY DESYNC", HTML)

    def test_registry_metadata_alone_cannot_arm_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            strategy = "ETF-CME-INSTFLOW-001"
            registry.write_text(json.dumps({
                "registry_version": "3.6-test",
                "focus_strategy_ids": [strategy],
                "candidates": [{
                    "strategy_id": strategy,
                    "scientific_tier": 2,
                    "deployment_state": "AUTHENTICATED_PREFLIGHT_PENDING",
                    "shadow_allowed": True,
                    "micro_live_allowed_now": True,
                }],
            }), encoding="utf-8")
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["focus_counts"]["ARMED"], 0)
            self.assertEqual(state["bots"][0]["operating_state"], "SHADOW")

    def test_ced1d_registry_shadow_requires_live_sentinel_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry, status, events = self._paths(root)
            strategy = "CED1D-0031"
            registry.write_text(json.dumps({
                "registry_version": "3.6-test",
                "focus_strategy_ids": [strategy],
                "candidates": [{"strategy_id": strategy, "scientific_tier": 2,
                    "deployment_state": "PROSPECTIVE_PUBLIC_ARCHIVE_SHADOW_ARMED",
                    "shadow_allowed": True, "micro_live_allowed_now": False}],
            }), encoding="utf-8")
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["bots"][0]["operating_state"], "BLOCKED")
            (root / "render_sentinel_status.json").write_text(json.dumps({
                "status": "OK", "remote_health": "OK", "checked_at_utc": "2026-09-22T08:00:00Z"
            }), encoding="utf-8")
            state = build_control_room_state(status_path=str(status), notification_path=str(events), registry_path=str(registry))
            self.assertEqual(state["bots"][0]["operating_state"], "SHADOW")


if __name__ == "__main__":
    unittest.main()
