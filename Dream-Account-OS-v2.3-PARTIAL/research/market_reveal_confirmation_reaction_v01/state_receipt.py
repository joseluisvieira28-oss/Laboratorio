"""Deterministic evidence receipts for MRCR decision-time state vectors.

Receipts contain feature/provenance evidence only. Future target/outcome fields are
explicitly rejected.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


FORBIDDEN_KEYS = {
    "future_return",
    "target_return",
    "outcome",
    "pnl",
    "sharpe",
    "profit_factor",
    "win",
    "trade_direction",
    "entry",
    "exit",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _walk_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            found.add(str(key).lower())
            found.update(_walk_keys(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.update(_walk_keys(child))
    return found


def build_state_receipt(
    *,
    lab_id: str,
    venue: str,
    native_symbol: str,
    event_or_impulse_id: str,
    anchor_ns: int,
    decision_ns: int,
    state: Mapping[str, float | None],
    raw_segment_sha256: Sequence[str],
    timestamp_semantics: Mapping[str, str],
    sequence_diagnostics: Mapping[str, Any],
    implementation_head_sha: str,
    measurement_catalog_sha256: str,
) -> dict[str, Any]:
    if not raw_segment_sha256:
        raise ValueError("at least one raw-segment SHA-256 is required")
    for value in raw_segment_sha256:
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
            raise ValueError("raw segment hashes must be 64-character hex SHA-256 values")
    if decision_ns < anchor_ns:
        raise ValueError("decision must be >= anchor")

    preimage = {
        "document_type": "MRCR_STATE_VECTOR_RECEIPT_V01",
        "lab_id": lab_id,
        "venue": venue,
        "native_symbol": native_symbol,
        "event_or_impulse_id": event_or_impulse_id,
        "anchor_ns": int(anchor_ns),
        "decision_ns": int(decision_ns),
        "state": dict(state),
        "raw_segment_sha256": sorted(set(raw_segment_sha256)),
        "timestamp_semantics": dict(timestamp_semantics),
        "sequence_diagnostics": dict(sequence_diagnostics),
        "implementation_head_sha": implementation_head_sha,
        "measurement_catalog_sha256": measurement_catalog_sha256,
    }

    forbidden = FORBIDDEN_KEYS & _walk_keys(preimage)
    if forbidden:
        raise ValueError(f"target/economic keys forbidden in state receipt: {sorted(forbidden)}")

    receipt = dict(preimage)
    receipt["receipt_sha256"] = _sha(preimage)
    return receipt


def verify_state_receipt(receipt: Mapping[str, Any]) -> bool:
    claimed = receipt.get("receipt_sha256")
    if not isinstance(claimed, str):
        return False
    preimage = dict(receipt)
    preimage.pop("receipt_sha256", None)
    if FORBIDDEN_KEYS & _walk_keys(preimage):
        return False
    return claimed == _sha(preimage)
