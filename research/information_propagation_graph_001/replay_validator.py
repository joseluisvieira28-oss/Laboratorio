"""Deterministic replay/integrity checks for IPG-001 NDJSON captures.

Research-only. This module never opens network connections and never mutates an
exchange. It validates append-order, hashes, timestamp presence and explicit
sequence evidence before any propagation analysis is allowed.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional


@dataclass
class ReplaySummary:
    rows: int = 0
    source_timestamp_missing: int = 0
    hash_mismatch: int = 0
    monotonic_regressions: int = 0
    deribit_sequence_gaps: int = 0

    @property
    def valid(self) -> bool:
        return (
            self.rows > 0
            and self.hash_mismatch == 0
            and self.monotonic_regressions == 0
            and self.deribit_sequence_gaps == 0
        )


def canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def iter_ndjson(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"INVALID_JSON_LINE:{lineno}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"NON_OBJECT_LINE:{lineno}")
            yield item


def _parse_deribit_change_id(sequence: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    if not sequence or not sequence.startswith("change_id:"):
        return None, None
    try:
        left, right = sequence.split(";prev:", 1)
        return int(left.split(":", 1)[1]), int(right)
    except (ValueError, IndexError):
        return None, None


def validate_rows(rows: Iterable[dict[str, Any]]) -> ReplaySummary:
    summary = ReplaySummary()
    prev_mono: Optional[int] = None
    last_deribit_change: dict[str, int] = {}

    for row in rows:
        summary.rows += 1

        if row.get("source_event_ts_ms") is None:
            summary.source_timestamp_missing += 1

        mono = row.get("recv_monotonic_ns")
        if isinstance(mono, int):
            if prev_mono is not None and mono < prev_mono:
                summary.monotonic_regressions += 1
            prev_mono = mono

        raw_payload = row.get("raw_payload")
        declared_hash = row.get("raw_sha256")
        if raw_payload is not None and declared_hash is not None:
            if canonical_hash(raw_payload) != declared_hash:
                summary.hash_mismatch += 1

        if row.get("venue") == "DERIBIT":
            change_id, prev_change_id = _parse_deribit_change_id(row.get("source_sequence"))
            instrument = str(row.get("instrument") or "unknown")
            if change_id is not None and prev_change_id is not None:
                prior = last_deribit_change.get(instrument)
                if prior is not None and prev_change_id != prior:
                    summary.deribit_sequence_gaps += 1
                last_deribit_change[instrument] = change_id

    return summary


def validate_file(path: str | Path) -> ReplaySummary:
    return validate_rows(iter_ndjson(path))
