from pathlib import Path
import sys
import tempfile
import unittest

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH_DIR))

import microstructure_collector_offline_preparation_v01 as prep


def _hash(n: int) -> str:
    return prep.sha256_hex(f"record-{n}".encode("utf-8"))


class MicrostructureCollectorOfflinePreparationV01Tests(unittest.TestCase):
    def _manifest(self, **overrides):
        data = {
            "session_id": "session-001",
            "venue": "BINANCE_SPOT",
            "symbol": "BTCUSDT",
            "channel": "trade",
            "endpoint_host": prep.BINANCE_WS_HOST,
            "collector_commit_sha": "abc123def456",
            "opened_wall_ns": 1_000,
            "opened_monotonic_ns": 500,
        }
        data.update(overrides)
        return prep.SessionManifest(**data)

    def test_manifest_fingerprint_deterministic_and_allowlisted(self):
        manifest = self._manifest()
        manifest.validate()
        self.assertEqual(manifest.fingerprint(), manifest.fingerprint())
        self.assertEqual(len(manifest.fingerprint()), 64)

        with self.assertRaises(prep.CollectorPreparationViolation):
            self._manifest(endpoint_host="api.binance.com").validate()
        with self.assertRaises(prep.CollectorPreparationViolation):
            self._manifest(symbol="SOLUSDT").validate()
        with self.assertRaises(prep.CollectorPreparationViolation):
            self._manifest(channel="userData").validate()

    def test_binance_snapshot_must_use_market_data_only_rest_host(self):
        manifest = self._manifest(
            channel="depth_snapshot",
            endpoint_host=prep.BINANCE_REST_HOST,
        )
        manifest.validate()
        with self.assertRaises(prep.CollectorPreparationViolation):
            self._manifest(
                channel="depth_snapshot",
                endpoint_host=prep.BINANCE_WS_HOST,
            ).validate()

    def test_immutable_segment_preserves_exact_bytes_and_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            writer = prep.ImmutableSegmentWriter(Path(td), self._manifest(), 0)
            raw1 = b'{"e":"trade","s":"BTCUSDT","t":1}\n'
            raw2 = b"\x00\x01exact-source-bytes\xff"
            writer.append(
                raw1,
                collector_wall_ns=1_000,
                collector_monotonic_ns=500,
                exchange_ts_ns=900,
                sequence_start=1,
                sequence_end=1,
            )
            writer.note_reconnect()
            writer.note_gap()
            writer.note_resync()
            writer.append(
                raw2,
                collector_wall_ns=1_100,
                collector_monotonic_ns=600,
                exchange_ts_ns=950,
                sequence_start=2,
                sequence_end=2,
            )
            receipt = writer.close()
            self.assertEqual(receipt.message_count, 2)
            self.assertEqual(receipt.reconnect_count, 1)
            self.assertEqual(receipt.gap_count, 1)
            self.assertEqual(receipt.resync_count, 1)
            verified = prep.verify_closed_segment(writer.segment_dir)
            self.assertEqual(verified.ordered_segment_sha256, receipt.ordered_segment_sha256)
            self.assertEqual(
                (writer.segment_dir / "messages" / "000000000001.bin").read_bytes(),
                raw2,
            )
            with self.assertRaises(prep.CollectorPreparationViolation):
                writer.append(
                    b"late",
                    collector_wall_ns=1_200,
                    collector_monotonic_ns=700,
                )

    def test_post_close_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            writer = prep.ImmutableSegmentWriter(Path(td), self._manifest(), 0)
            writer.append(
                b"original",
                collector_wall_ns=1_000,
                collector_monotonic_ns=500,
            )
            writer.close()
            raw = writer.segment_dir / "messages" / "000000000000.bin"
            raw.write_bytes(b"tampered")
            with self.assertRaises(prep.CollectorPreparationViolation):
                prep.verify_closed_segment(writer.segment_dir)

    def test_segment_identity_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            prep.ImmutableSegmentWriter(Path(td), self._manifest(), 0)
            with self.assertRaises(FileExistsError):
                prep.ImmutableSegmentWriter(Path(td), self._manifest(), 0)

    def test_clock_diagnostics_fail_closed_on_regression(self):
        good = prep.clock_diagnostics(
            [
                prep.ClockSample(100, 10),
                prep.ClockSample(200, 20),
                prep.ClockSample(300, 30),
            ]
        )
        self.assertTrue(good["valid_for_receive_time_ordering"])
        bad = prep.clock_diagnostics(
            [
                prep.ClockSample(100, 10),
                prep.ClockSample(90, 20),
                prep.ClockSample(110, 20),
            ]
        )
        self.assertFalse(bad["valid_for_receive_time_ordering"])
        self.assertEqual(bad["wall_regressions"], 1)
        self.assertEqual(bad["monotonic_nonincreasing"], 1)

    def test_frozen_sequence_rules(self):
        self.assertEqual(
            prep.binance_sequence_status(100, 101, 102),
            "CONTIGUOUS_OR_OVERLAP",
        )
        self.assertEqual(
            prep.binance_sequence_status(100, 99, 101),
            "CONTIGUOUS_OR_OVERLAP",
        )
        self.assertEqual(
            prep.binance_sequence_status(100, 103, 104),
            "GAP_FAIL_CLOSED",
        )
        self.assertEqual(
            prep.binance_sequence_status(100, 99, 100),
            "STALE_OR_DUPLICATE",
        )
        self.assertEqual(
            prep.coinbase_connection_sequence_status(10, 11),
            "CONTIGUOUS",
        )
        self.assertEqual(
            prep.coinbase_connection_sequence_status(10, 12),
            "GAP_OR_REORDER_FAIL_CLOSED",
        )
        self.assertEqual(
            prep.coinbase_book_sequence_status(10, 12),
            "STRICTLY_INCREASING",
        )
        self.assertEqual(
            prep.coinbase_book_sequence_status(10, 10),
            "REGRESSION_FAIL_CLOSED",
        )

    def test_reconnect_and_gap_require_resync(self):
        state = prep.ContinuityState("COINBASE_ADVANCED_SPOT", synchronized=True)
        state.on_reconnect("socket_closed")
        self.assertFalse(state.synchronized)
        state.on_resync()
        self.assertTrue(state.synchronized)
        state.on_gap("sequence_gap")
        self.assertFalse(state.synchronized)
        self.assertEqual(state.gap_count, 1)

    def test_storage_estimation_is_descriptive(self):
        estimate = prep.storage_estimate(
            observed_bytes=3_600_000,
            observed_seconds=3600,
            target_hours=24,
        )
        self.assertAlmostEqual(estimate["bytes_per_second"], 1000.0)
        self.assertEqual(estimate["baseline_bytes"], 86_400_000)
        self.assertEqual(estimate["planning_2x_bytes"], 172_800_000)

    def test_event_windows_are_half_open_and_deterministic(self):
        minute = 60 * 1_000_000_000
        event = 100 * minute
        records = [
            prep.WindowRecord(event - 30 * minute, 0, _hash(0)),
            prep.WindowRecord(event - 1, 1, _hash(1)),
            prep.WindowRecord(event, 2, _hash(2)),
            prep.WindowRecord(event + 30 * minute - 1, 3, _hash(3)),
            prep.WindowRecord(event + 30 * minute, 4, _hash(4)),
            prep.WindowRecord(event + 60 * minute - 1, 5, _hash(5)),
            prep.WindowRecord(event + 60 * minute, 6, _hash(6)),
        ]
        windows = prep.extract_frozen_event_windows(
            reversed(records),
            event_timestamp_ns=event,
        )
        self.assertEqual([r.source_order for r in windows["prebaseline"]], [0, 1])
        self.assertEqual([r.source_order for r in windows["primary_state"]], [2, 3])
        self.assertEqual([r.source_order for r in windows["recovery_descriptive"]], [4, 5])

    def test_completeness_receipt_reports_missing_without_inventing_data(self):
        required = prep.required_observation_keys()
        partial = prep.completeness_receipt(required[:-1])
        self.assertFalse(partial["complete"])
        self.assertEqual(len(partial["missing_keys"]), 1)
        complete = prep.completeness_receipt(required)
        self.assertTrue(complete["complete"])
        with self.assertRaises(prep.CollectorPreparationViolation):
            prep.completeness_receipt([("MEXC", "BTCUSDT", "trade")])

    def test_preflight_blocks_without_calendar_and_separate_authorization(self):
        impl = _hash(100)
        contract = _hash(101)
        blocked_calendar = prep.preflight_gate(
            implementation_fingerprint=impl,
            contract_fingerprint=contract,
            complete_official_2027_calendar_frozen=False,
            separate_explicit_target_observation_authorization=True,
        )
        self.assertFalse(blocked_calendar["target_observation_may_start"])
        blocked_auth = prep.preflight_gate(
            implementation_fingerprint=impl,
            contract_fingerprint=contract,
            complete_official_2027_calendar_frozen=True,
            separate_explicit_target_observation_authorization=False,
        )
        self.assertFalse(blocked_auth["target_observation_may_start"])
        eligible = prep.preflight_gate(
            implementation_fingerprint=impl,
            contract_fingerprint=contract,
            complete_official_2027_calendar_frozen=True,
            separate_explicit_target_observation_authorization=True,
        )
        self.assertTrue(eligible["target_observation_may_start"])
        self.assertEqual(eligible["status"], "ELIGIBLE_FOR_RUNTIME_PREFLIGHT_NOT_STARTED")

    def test_observation_receipt_is_template_only(self):
        receipt = prep.observation_receipt_template()
        self.assertEqual(receipt["status"], "TEMPLATE_NOT_EXECUTED")
        self.assertFalse(receipt["target_observation_started"])
        self.assertIsNone(receipt["scientific_classification"])
        self.assertEqual(receipt["h02_status"], "NOT_AUTHORIZED")

    def test_audit_chain_is_order_and_parent_sensitive(self):
        a = {"kind": "A", "value": 1}
        b = {"kind": "B", "value": 2}
        first = prep.audit_chain_fingerprint(None, a)
        second = prep.audit_chain_fingerprint(first, b)
        reversed_first = prep.audit_chain_fingerprint(None, b)
        reversed_second = prep.audit_chain_fingerprint(reversed_first, a)
        self.assertNotEqual(second, reversed_second)

    def test_governance_receipt_preserves_fail_closed_boundaries(self):
        receipt = prep.governance_receipt()
        self.assertEqual(receipt["h02_status"], "NOT_AUTHORIZED")
        self.assertFalse(receipt["target_observation_authorized_by_this_module"])
        self.assertFalse(receipt["network_access_in_this_module"])
        self.assertFalse(receipt["exchange_mutation_authorized"])
        self.assertFalse(receipt["live_trading_authorized"])
        self.assertFalse(receipt["target_outcomes_accessed"])
        self.assertFalse(receipt["directional_signals_generated"])
        self.assertFalse(receipt["mexc_2025_09_through_2025_12_accessed"])


if __name__ == "__main__":
    unittest.main()
