"""Synthetic-only operational readiness drill for the Prospective Microstructure Collector V0.1.

This module exercises the already-frozen offline collector primitives end to end with
fully deterministic synthetic bytes. It performs no network access, reads no exchange
credentials or market outcomes, and cannot authorize prospective target observation.

A PASS means operational collector readiness only. It is not evidence of edge,
profitability, directional predictability, or trading readiness.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Mapping

import microstructure_collector_offline_preparation_v01 as prep


DRILL_VERSION = "0.1"
DRILL_SCOPE = "SYNTHETIC_OFFLINE_NON_DIRECTIONAL_COLLECTOR_READINESS_ONLY"
PASS_LABEL = "COLLECTOR_OPERATIONAL_READINESS_PASS"
FAIL_LABEL = "COLLECTOR_OPERATIONAL_READINESS_FAIL"
SYNTHETIC_COMMIT_TOKEN = "synthetic-drill-no-repo-commit"
EVENT_TIMESTAMP_NS = 10_800 * 1_000_000_000


def _endpoint_host(venue: str, channel: str) -> str:
    if venue == "BINANCE_SPOT":
        return prep.BINANCE_REST_HOST if channel == "depth_snapshot" else prep.BINANCE_WS_HOST
    if venue == "COINBASE_ADVANCED_SPOT":
        return prep.COINBASE_WS_HOST
    raise prep.CollectorPreparationViolation("venue outside frozen collector scope")


def _synthetic_raw(venue: str, symbol: str, channel: str, message_index: int) -> bytes:
    payload = {
        "channel": channel,
        "message_index": message_index,
        "source": "SYNTHETIC_READINESS_DRILL",
        "symbol": symbol,
        "venue": venue,
    }
    return prep._canonical_bytes(payload)


def _manifest(index: int, venue: str, symbol: str, channel: str, *, suffix: str = "") -> prep.SessionManifest:
    token = f"drill-{index:02d}{suffix}"
    base = 5_000_000_000_000 + index * 10_000_000
    return prep.SessionManifest(
        session_id=token,
        venue=venue,
        symbol=symbol,
        channel=channel,
        endpoint_host=_endpoint_host(venue, channel),
        collector_commit_sha=SYNTHETIC_COMMIT_TOKEN,
        opened_wall_ns=base,
        opened_monotonic_ns=base // 2,
    )


def _receipt_fingerprint(receipt: prep.SegmentReceipt) -> str:
    return prep.canonical_fingerprint(asdict(receipt))


def _write_complete_scope(root: Path) -> Mapping[str, object]:
    manifest_fingerprints: list[str] = []
    segment_fingerprints: list[str] = []
    observed_keys: list[tuple[str, str, str]] = []
    total_raw_bytes = 0

    for index, (venue, symbol, channel) in enumerate(prep.required_observation_keys()):
        manifest = _manifest(index, venue, symbol, channel)
        writer = prep.ImmutableSegmentWriter(root, manifest, 0)
        for message_index in range(2):
            raw = _synthetic_raw(venue, symbol, channel, message_index)
            total_raw_bytes += len(raw)
            base = manifest.opened_wall_ns + (message_index + 1) * 1_000_000
            writer.append(
                raw,
                collector_wall_ns=base,
                collector_monotonic_ns=manifest.opened_monotonic_ns + (message_index + 1) * 1_000_000,
                exchange_ts_ns=base - 100_000,
                sequence_start=1000 + message_index,
                sequence_end=1000 + message_index,
            )
        receipt = writer.close()
        verified = prep.verify_closed_segment(writer.segment_dir)
        if verified != receipt:
            raise prep.CollectorPreparationViolation("verified receipt does not equal written receipt")
        manifest_fingerprints.append(manifest.fingerprint())
        segment_fingerprints.append(_receipt_fingerprint(receipt))
        observed_keys.append((venue, symbol, channel))

    completeness = prep.completeness_receipt(observed_keys)
    return {
        "manifest_fingerprints": manifest_fingerprints,
        "segment_receipt_fingerprints": segment_fingerprints,
        "completeness_receipt": completeness,
        "completeness_receipt_fingerprint": prep.canonical_fingerprint(completeness),
        "total_raw_bytes": total_raw_bytes,
    }


def _continuity_scenarios() -> Mapping[str, object]:
    binance = prep.ContinuityState("BINANCE_SPOT")
    binance.on_resync()
    binance_contiguous = prep.binance_sequence_status(100, 101, 102)
    binance_gap = prep.binance_sequence_status(102, 105, 106)
    if binance_gap == "GAP_FAIL_CLOSED":
        binance.on_gap("synthetic missing sequence interval")
    blocked_after_gap = not binance.synchronized
    binance.on_resync()

    coinbase = prep.ContinuityState("COINBASE_ADVANCED_SPOT")
    coinbase.on_resync()
    coinbase_contiguous = prep.coinbase_connection_sequence_status(900, 901)
    coinbase_gap = prep.coinbase_connection_sequence_status(901, 903)
    book_forward = prep.coinbase_book_sequence_status(44, 45)
    book_regression = prep.coinbase_book_sequence_status(45, 45)
    if coinbase_gap == "GAP_OR_REORDER_FAIL_CLOSED":
        coinbase.on_gap("synthetic global envelope sequence discontinuity")
    blocked_after_coinbase_gap = not coinbase.synchronized
    coinbase.on_resync()

    return {
        "binance": {
            "contiguous_status": binance_contiguous,
            "gap_status": binance_gap,
            "blocked_after_gap": blocked_after_gap,
            "resynchronized_after_explicit_resync": binance.synchronized,
            "gap_count": binance.gap_count,
            "resync_count": binance.resync_count,
        },
        "coinbase": {
            "connection_contiguous_status": coinbase_contiguous,
            "connection_gap_status": coinbase_gap,
            "book_forward_status": book_forward,
            "book_regression_status": book_regression,
            "blocked_after_gap": blocked_after_coinbase_gap,
            "resynchronized_after_explicit_resync": coinbase.synchronized,
            "gap_count": coinbase.gap_count,
            "resync_count": coinbase.resync_count,
        },
    }


def _clock_scenarios() -> Mapping[str, object]:
    good = prep.clock_diagnostics(
        [
            prep.ClockSample(1_000, 500),
            prep.ClockSample(2_000, 1_500),
            prep.ClockSample(3_000, 2_500),
        ]
    )
    bad = prep.clock_diagnostics(
        [
            prep.ClockSample(3_000, 1_000),
            prep.ClockSample(2_900, 1_100),
            prep.ClockSample(3_100, 1_100),
        ]
    )
    return {
        "clean_clock": dict(good),
        "fault_injection_clock": dict(bad),
        "fault_detected": (
            bad["wall_regressions"] > 0
            and bad["monotonic_nonincreasing"] > 0
            and bad["valid_for_receive_time_ordering"] is False
        ),
    }


def _crash_restart_scenario(root: Path) -> Mapping[str, object]:
    manifest = _manifest(40, "BINANCE_SPOT", "BTCUSDT", "trade", suffix="-restart")
    interrupted = prep.ImmutableSegmentWriter(root, manifest, 0)
    raw_before_crash = b'{"source":"SYNTHETIC_CRASH_FIXTURE","ordinal":0}'
    interrupted.append(
        raw_before_crash,
        collector_wall_ns=manifest.opened_wall_ns + 1,
        collector_monotonic_ns=manifest.opened_monotonic_ns + 1,
        exchange_ts_ns=manifest.opened_wall_ns,
        sequence_start=1,
        sequence_end=1,
    )
    partial_raw_path = interrupted.messages_dir / "000000000000.bin"
    partial_hash_before = prep.sha256_hex(partial_raw_path.read_bytes())

    open_segment_rejected_as_closed = False
    try:
        prep.verify_closed_segment(interrupted.segment_dir)
    except prep.CollectorPreparationViolation:
        open_segment_rejected_as_closed = True

    overwrite_collision_blocked = False
    try:
        prep.ImmutableSegmentWriter(root, manifest, 0)
    except FileExistsError:
        overwrite_collision_blocked = True

    restarted = prep.ImmutableSegmentWriter(root, manifest, 1)
    restarted.append(
        b'{"source":"SYNTHETIC_RESTART_FIXTURE","ordinal":0}',
        collector_wall_ns=manifest.opened_wall_ns + 2,
        collector_monotonic_ns=manifest.opened_monotonic_ns + 2,
        exchange_ts_ns=manifest.opened_wall_ns + 1,
        sequence_start=2,
        sequence_end=2,
    )
    restarted.note_reconnect()
    restarted.note_resync()
    restarted.append(
        b'{"source":"SYNTHETIC_RESTART_FIXTURE","ordinal":1}',
        collector_wall_ns=manifest.opened_wall_ns + 3,
        collector_monotonic_ns=manifest.opened_monotonic_ns + 3,
        exchange_ts_ns=manifest.opened_wall_ns + 2,
        sequence_start=3,
        sequence_end=3,
    )
    restarted_receipt = restarted.close()
    prep.verify_closed_segment(restarted.segment_dir)
    partial_hash_after = prep.sha256_hex(partial_raw_path.read_bytes())

    return {
        "open_segment_rejected_as_closed": open_segment_rejected_as_closed,
        "same_segment_index_overwrite_blocked": overwrite_collision_blocked,
        "interrupted_bytes_preserved": partial_hash_before == partial_hash_after,
        "interrupted_raw_sha256": partial_hash_after,
        "restart_used_new_segment_index": 1,
        "restart_closed_segment_fingerprint": _receipt_fingerprint(restarted_receipt),
        "reconnect_count": restarted_receipt.reconnect_count,
        "resync_count": restarted_receipt.resync_count,
    }


def _tamper_scenario(root: Path) -> Mapping[str, object]:
    manifest = _manifest(50, "COINBASE_ADVANCED_SPOT", "BTC-USD", "market_trades", suffix="-tamper")
    writer = prep.ImmutableSegmentWriter(root, manifest, 0)
    writer.append(
        b'{"source":"SYNTHETIC_TAMPER_FIXTURE","ordinal":0}',
        collector_wall_ns=manifest.opened_wall_ns + 1,
        collector_monotonic_ns=manifest.opened_monotonic_ns + 1,
        exchange_ts_ns=manifest.opened_wall_ns,
        sequence_start=10,
        sequence_end=10,
    )
    receipt = writer.close()
    prep.verify_closed_segment(writer.segment_dir)
    original_receipt_fingerprint = _receipt_fingerprint(receipt)

    raw_path = writer.messages_dir / "000000000000.bin"
    with raw_path.open("wb") as handle:
        handle.write(b'{"source":"SYNTHETIC_TAMPER_FIXTURE","ordinal":999}')

    tamper_detected = False
    try:
        prep.verify_closed_segment(writer.segment_dir)
    except prep.CollectorPreparationViolation:
        tamper_detected = True

    return {
        "deliberate_synthetic_tamper_detected": tamper_detected,
        "tampered_fixture_excluded_from_valid_segments": True,
        "pre_tamper_receipt_fingerprint": original_receipt_fingerprint,
    }


def _event_window_scenario() -> Mapping[str, object]:
    minute = 60 * 1_000_000_000
    offsets = [
        -30 * minute,
        -1,
        0,
        30 * minute - 1,
        30 * minute,
        60 * minute - 1,
        60 * minute,
    ]
    records = [
        prep.WindowRecord(
            timestamp_ns=EVENT_TIMESTAMP_NS + offset,
            source_order=index,
            source_hash_sha256=prep.sha256_hex(f"window-{index}".encode("ascii")),
        )
        for index, offset in enumerate(offsets)
    ]
    windows = prep.extract_frozen_event_windows(records, event_timestamp_ns=EVENT_TIMESTAMP_NS)
    selected = {
        name: [record.source_hash_sha256 for record in values]
        for name, values in windows.items()
    }
    exactly_plus_60_hash = records[-1].source_hash_sha256
    all_selected_hashes = {item for values in selected.values() for item in values}
    receipt = {
        "event_timestamp_ns": EVENT_TIMESTAMP_NS,
        "half_open_counts": {name: len(values) for name, values in windows.items()},
        "selected_hashes": selected,
        "exactly_plus_60m_excluded": exactly_plus_60_hash not in all_selected_hashes,
    }
    return {
        **receipt,
        "event_window_extraction_fingerprint": prep.canonical_fingerprint(receipt),
    }


def _synthetic_observation_receipt(
    *,
    manifest_fingerprints: list[str],
    segment_receipt_fingerprints: list[str],
    completeness_receipt_fingerprint: str,
    clock_fingerprints: list[str],
    event_window_fingerprint: str,
) -> Mapping[str, object]:
    receipt = dict(prep.observation_receipt_template())
    receipt.update(
        {
            "status": "SYNTHETIC_DRILL_ONLY_NOT_A_TARGET_OBSERVATION",
            "target_observation_started": False,
            "target_outcomes_evaluated": False,
            "trading_signals_generated": False,
            "session_manifest_fingerprints": manifest_fingerprints,
            "segment_receipt_fingerprints": segment_receipt_fingerprints,
            "completeness_receipt_fingerprint": completeness_receipt_fingerprint,
            "clock_diagnostic_fingerprints": clock_fingerprints,
            "event_window_extraction_fingerprint": event_window_fingerprint,
            "scientific_classification": None,
            "note": "Synthetic readiness drill only. No market observation occurred and no edge classification is permitted.",
        }
    )
    return receipt


def _single_run(root: Path) -> Mapping[str, object]:
    root.mkdir(parents=True, exist_ok=False)
    complete_scope = _write_complete_scope(root / "complete_scope")
    continuity = _continuity_scenarios()
    clocks = _clock_scenarios()
    crash_restart = _crash_restart_scenario(root / "crash_restart")
    tamper = _tamper_scenario(root / "tamper_detection")
    event_windows = _event_window_scenario()

    storage = prep.storage_estimate(
        observed_bytes=int(complete_scope["total_raw_bytes"]),
        observed_seconds=60.0,
        target_hours=2.0,
    )
    preflight = prep.preflight_gate(
        implementation_fingerprint=prep.canonical_fingerprint({"drill_version": DRILL_VERSION}),
        contract_fingerprint=prep.canonical_fingerprint({"contract": "frozen_non_directional_v0.1"}),
        complete_official_2027_calendar_frozen=False,
        separate_explicit_target_observation_authorization=False,
    )
    governance = prep.governance_receipt()

    clock_fingerprints = [
        prep.canonical_fingerprint(clocks["clean_clock"]),
        prep.canonical_fingerprint(clocks["fault_injection_clock"]),
    ]
    observation = _synthetic_observation_receipt(
        manifest_fingerprints=list(complete_scope["manifest_fingerprints"]),
        segment_receipt_fingerprints=list(complete_scope["segment_receipt_fingerprints"]),
        completeness_receipt_fingerprint=str(complete_scope["completeness_receipt_fingerprint"]),
        clock_fingerprints=clock_fingerprints,
        event_window_fingerprint=str(event_windows["event_window_extraction_fingerprint"]),
    )

    checks = {
        "all_required_scope_keys_completed": bool(complete_scope["completeness_receipt"]["complete"]),
        "all_closed_scope_segments_verified": len(complete_scope["segment_receipt_fingerprints"]) == len(prep.required_observation_keys()),
        "binance_gap_failed_closed": continuity["binance"]["gap_status"] == "GAP_FAIL_CLOSED" and continuity["binance"]["blocked_after_gap"],
        "binance_resync_restored_state": continuity["binance"]["resynchronized_after_explicit_resync"],
        "coinbase_gap_failed_closed": continuity["coinbase"]["connection_gap_status"] == "GAP_OR_REORDER_FAIL_CLOSED" and continuity["coinbase"]["blocked_after_gap"],
        "coinbase_book_regression_detected": continuity["coinbase"]["book_regression_status"] == "REGRESSION_FAIL_CLOSED",
        "coinbase_resync_restored_state": continuity["coinbase"]["resynchronized_after_explicit_resync"],
        "clock_faults_detected": bool(clocks["fault_detected"]),
        "crash_open_segment_not_accepted": bool(crash_restart["open_segment_rejected_as_closed"]),
        "crash_same_segment_overwrite_blocked": bool(crash_restart["same_segment_index_overwrite_blocked"]),
        "crash_prior_bytes_preserved": bool(crash_restart["interrupted_bytes_preserved"]),
        "restart_new_segment_closed_and_verified": bool(crash_restart["restart_closed_segment_fingerprint"]),
        "closed_segment_tamper_detected": bool(tamper["deliberate_synthetic_tamper_detected"]),
        "event_windows_half_open_exact": event_windows["half_open_counts"] == {"prebaseline": 2, "primary_state": 2, "recovery_descriptive": 2} and bool(event_windows["exactly_plus_60m_excluded"]),
        "preflight_remains_blocked": preflight["target_observation_may_start"] is False and preflight["status"] == "OFFLINE_READY_TARGET_OBSERVATION_BLOCKED",
        "h02_remains_not_authorized": governance["h02_status"] == "NOT_AUTHORIZED",
        "no_target_observation_started": observation["target_observation_started"] is False,
        "no_target_outcomes_evaluated": observation["target_outcomes_evaluated"] is False,
        "no_trading_signals_generated": observation["trading_signals_generated"] is False,
        "synthetic_observation_receipt_marked": observation["status"] == "SYNTHETIC_DRILL_ONLY_NOT_A_TARGET_OBSERVATION",
    }

    audit_records = [
        {"name": "complete_scope", "fingerprint": prep.canonical_fingerprint(complete_scope)},
        {"name": "continuity", "fingerprint": prep.canonical_fingerprint(continuity)},
        {"name": "clocks", "fingerprint": prep.canonical_fingerprint(clocks)},
        {"name": "crash_restart", "fingerprint": prep.canonical_fingerprint(crash_restart)},
        {"name": "tamper", "fingerprint": prep.canonical_fingerprint(tamper)},
        {"name": "event_windows", "fingerprint": prep.canonical_fingerprint(event_windows)},
        {"name": "storage", "fingerprint": prep.canonical_fingerprint(storage)},
        {"name": "preflight", "fingerprint": prep.canonical_fingerprint(preflight)},
        {"name": "synthetic_observation_receipt", "fingerprint": prep.canonical_fingerprint(observation)},
    ]
    previous = None
    audit_chain = []
    for record in audit_records:
        previous = prep.audit_chain_fingerprint(previous, record)
        audit_chain.append(previous)

    body = {
        "document_type": "MICROSTRUCTURE_PROSPECTIVE_COLLECTOR_READINESS_DRILL_SINGLE_RUN",
        "version": DRILL_VERSION,
        "scope": DRILL_SCOPE,
        "synthetic_only": True,
        "operational_checks": checks,
        "complete_scope": complete_scope,
        "continuity": continuity,
        "clock_diagnostics": clocks,
        "crash_restart": crash_restart,
        "tamper_detection": tamper,
        "event_windows": event_windows,
        "storage_planning_descriptive_only": storage,
        "preflight": preflight,
        "synthetic_observation_receipt": observation,
        "audit_chain": audit_chain,
        "scientific_meaning": "Operational readiness only; not edge, profitability, direction, or trading readiness.",
    }
    fingerprint = prep.canonical_fingerprint(body)
    return {**body, "single_run_fingerprint": fingerprint}


def run_full_readiness_drill(parent_root: Path) -> Mapping[str, object]:
    parent = Path(parent_root)
    parent.mkdir(parents=True, exist_ok=False)
    run_a = _single_run(parent / "run_a")
    run_b = _single_run(parent / "run_b")
    deterministic = run_a["single_run_fingerprint"] == run_b["single_run_fingerprint"]
    run_checks_pass = all(bool(value) for value in run_a["operational_checks"].values())
    mirrored_checks_pass = run_a["operational_checks"] == run_b["operational_checks"]
    status = PASS_LABEL if deterministic and run_checks_pass and mirrored_checks_pass else FAIL_LABEL

    closeout_body = {
        "document_type": "MICROSTRUCTURE_PROSPECTIVE_COLLECTOR_READINESS_DRILL_CLOSEOUT",
        "version": DRILL_VERSION,
        "scope": DRILL_SCOPE,
        "status": status,
        "synthetic_only": True,
        "run_a_fingerprint": run_a["single_run_fingerprint"],
        "run_b_fingerprint": run_b["single_run_fingerprint"],
        "deterministic_repeat_equal": deterministic,
        "operational_checks_pass": run_checks_pass,
        "mirrored_checks_equal": mirrored_checks_pass,
        "operational_checks": run_a["operational_checks"],
        "required_observation_key_count": len(prep.required_observation_keys()),
        "target_observation_started": False,
        "target_outcomes_evaluated": False,
        "directional_signals_generated": False,
        "h02_status": prep.H02_STATUS,
        "complete_official_2027_calendar_frozen": False,
        "separate_explicit_target_observation_authorization": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "mexc_2025_09_through_2025_12_accessed": False,
        "holdout_2026_reused": False,
        "scientific_classification": None,
        "scientific_meaning": "PASS proves deterministic synthetic collector operational readiness only. It is not market evidence.",
        "stop_condition": "STOP_AT_COMPLETE_2027_OFFICIAL_BLS_CALENDAR_AND_SEPARATE_EXPLICIT_TARGET_OBSERVATION_AUTHORIZATION_GATE",
    }
    return {
        **closeout_body,
        "readiness_closeout_fingerprint": prep.canonical_fingerprint(closeout_body),
        "run_a": run_a,
    }
