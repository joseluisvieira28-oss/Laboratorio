from __future__ import annotations

from datetime import datetime, timezone
import tempfile

from radar.evidence import EvidenceStore
from radar.meta_sidecar import MetaT0Observer


def _signal():
    return {
        "candidate_id": "BNB-LAUNCHPOOL-DEMAND-001",
        "strategy_id": "BNB-LAUNCHPOOL-DEMAND-001",
        "immutable_signal_key": "fixture-signal-001",
        "symbol": "BNB_USDT",
        "direction": "LONG",
        "entry_target_utc": "2026-10-01T17:00:00Z",
    }


def test_sidecar_restart_is_durably_idempotent():
    with tempfile.TemporaryDirectory() as td:
        db=f"{td}/evidence.db"
        captured="2026-10-01T16:59:59Z"
        signal=_signal()

        first=MetaT0Observer(EvidenceStore(db)).observe(
            signal=signal,
            captured_at_utc=captured,
            simultaneous_signals=[signal],
        )
        second=MetaT0Observer(EvidenceStore(db)).observe(
            signal=signal,
            captured_at_utc=captured,
            simultaneous_signals=[signal],
        )

        assert first["status"]=="RECORDED"
        assert second["status"]=="DUPLICATE_NOOP"
        assert first["idempotency_key"]==second["idempotency_key"]

        store=EvidenceStore(db)
        rows=store.read_payloads("RADAR_META_T0_SNAPSHOT")
        assert len(rows)==1
        ok, detail=store.verify_chain()
        assert ok, detail
