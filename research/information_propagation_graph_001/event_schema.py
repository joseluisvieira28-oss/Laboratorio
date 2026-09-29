"""Canonical event schema for INFORMATION-PROPAGATION-GRAPH-001.

Research-only. No exchange mutation. The schema deliberately preserves both source
and receive clocks so downstream analysis cannot silently turn network latency into
predictive lead-lag.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import time
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class NormalizedEvent:
    source: str
    venue: str
    instrument: str
    event_type: str
    source_event_ts_ms: Optional[int]
    source_publish_ts_ms: Optional[int]
    recv_wall_ts_ms: int
    recv_monotonic_ns: int
    source_sequence: Optional[str]
    raw_sha256: str
    payload: Mapping[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _now_pair() -> tuple[int, int]:
    return time.time_ns() // 1_000_000, time.monotonic_ns()


def _as_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_binance(
    message: Mapping[str, Any],
    *,
    recv_wall_ts_ms: Optional[int] = None,
    recv_monotonic_ns: Optional[int] = None,
) -> NormalizedEvent:
    """Normalize a Binance raw or combined-stream public market message.

    Event-time precedence:
    - trade/aggTrade semantic transaction time T when available;
    - otherwise exchange event time E.

    E is retained separately as source_publish_ts_ms when present.
    """
    if "data" in message and isinstance(message.get("data"), Mapping):
        data = dict(message["data"])
        stream = str(message.get("stream") or "")
    else:
        data = dict(message)
        stream = ""

    if recv_wall_ts_ms is None or recv_monotonic_ns is None:
        wall, mono = _now_pair()
        recv_wall_ts_ms = wall if recv_wall_ts_ms is None else recv_wall_ts_ms
        recv_monotonic_ns = mono if recv_monotonic_ns is None else recv_monotonic_ns

    event_type = str(data.get("e") or (stream.split("@", 1)[1] if "@" in stream else "unknown"))
    instrument = str(data.get("s") or (stream.split("@", 1)[0] if stream else "unknown")).upper()

    semantic_ts = _as_int(data.get("T"))
    publish_ts = _as_int(data.get("E"))
    source_event_ts = semantic_ts if semantic_ts is not None else publish_ts

    seq = None
    for key in ("u", "a", "t", "lastUpdateId"):
        if key in data and data[key] is not None:
            seq = f"{key}:{data[key]}"
            break

    return NormalizedEvent(
        source="binance_public_market",
        venue="BINANCE",
        instrument=instrument,
        event_type=event_type,
        source_event_ts_ms=source_event_ts,
        source_publish_ts_ms=publish_ts,
        recv_wall_ts_ms=int(recv_wall_ts_ms),
        recv_monotonic_ns=int(recv_monotonic_ns),
        source_sequence=seq,
        raw_sha256=_hash_payload(message),
        payload=data,
    )


def normalize_deribit(
    message: Mapping[str, Any],
    *,
    recv_wall_ts_ms: Optional[int] = None,
    recv_monotonic_ns: Optional[int] = None,
) -> NormalizedEvent:
    """Normalize a Deribit public subscription notification.

    The parser retains change_id/prev_change_id evidence when present.
    Deribit ordering is treated as per-instrument only; no cross-instrument
    ordering is inferred from receive order.
    """
    params = message.get("params") if isinstance(message.get("params"), Mapping) else {}
    channel = str(params.get("channel") or "")
    raw_data = params.get("data")
    data = dict(raw_data) if isinstance(raw_data, Mapping) else {"value": raw_data}

    if recv_wall_ts_ms is None or recv_monotonic_ns is None:
        wall, mono = _now_pair()
        recv_wall_ts_ms = wall if recv_wall_ts_ms is None else recv_wall_ts_ms
        recv_monotonic_ns = mono if recv_monotonic_ns is None else recv_monotonic_ns

    parts = channel.split(".")
    event_type = parts[0] if parts and parts[0] else "unknown"
    instrument = str(data.get("instrument_name") or (parts[1] if len(parts) > 1 else "unknown"))

    source_event_ts = _as_int(data.get("timestamp"))
    seq = None
    if data.get("change_id") is not None:
        prev = data.get("prev_change_id")
        seq = f"change_id:{data.get('change_id')};prev:{prev}"
    elif data.get("trade_seq") is not None:
        seq = f"trade_seq:{data.get('trade_seq')}"

    return NormalizedEvent(
        source="deribit_public_market",
        venue="DERIBIT",
        instrument=instrument,
        event_type=event_type,
        source_event_ts_ms=source_event_ts,
        source_publish_ts_ms=source_event_ts,
        recv_wall_ts_ms=int(recv_wall_ts_ms),
        recv_monotonic_ns=int(recv_monotonic_ns),
        source_sequence=seq,
        raw_sha256=_hash_payload(message),
        payload=data,
    )


def clock_quality(event: NormalizedEvent, *, max_abs_wall_skew_ms: int = 10_000) -> dict[str, Any]:
    """Return diagnostics only; never 'correct' source timestamps silently."""
    if event.source_event_ts_ms is None:
        return {
            "usable_for_event_time": False,
            "reason": "MISSING_SOURCE_EVENT_TIMESTAMP",
            "observed_wall_minus_source_ms": None,
        }

    skew = event.recv_wall_ts_ms - event.source_event_ts_ms
    return {
        "usable_for_event_time": abs(skew) <= max_abs_wall_skew_ms,
        "reason": "OK" if abs(skew) <= max_abs_wall_skew_ms else "CLOCK_OR_LATENCY_OUTLIER",
        "observed_wall_minus_source_ms": skew,
    }
