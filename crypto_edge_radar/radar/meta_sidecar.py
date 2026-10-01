from __future__ import annotations
from typing import Any
from .meta_layer import append_t0_snapshot, build_t0_snapshot

TRIPLE_FISHING_IDS = frozenset({
    "BNB-LAUNCHPOOL-DEMAND-001",
    "OPTIONS-SPOTPERP-001-V2.1",
    "HTF-DH03-12H-STANDALONE-FORWARD-V1",
})

class MetaT0Observer:
    """Observational-only T0 recorder. It has no execution authority."""
    def __init__(self, store: Any) -> None:
        self.store = store

    def observe(self, *, signal: dict[str, Any], captured_at_utc: str,
                simultaneous_signals: list[dict[str, Any]]) -> dict[str, Any]:
        candidate = str(signal.get("candidate_id") or signal.get("strategy_id") or "")
        if candidate not in TRIPLE_FISHING_IDS:
            return {"status": "IGNORED_NOT_TRIPLE_FISHING"}
        snapshot = build_t0_snapshot(
            signal=signal,
            captured_at_utc=captured_at_utc,
            market_snapshot=None,
            public_context=None,
            simultaneous_signals=simultaneous_signals,
        )
        receipt = append_t0_snapshot(self.store, snapshot)
        return {"status": "DUPLICATE_NOOP" if receipt.get("duplicate") else "RECORDED",
                "idempotency_key": snapshot["idempotency_key"]}

__all__ = ["MetaT0Observer", "TRIPLE_FISHING_IDS"]
