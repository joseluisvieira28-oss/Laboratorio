#!/usr/bin/env python3
"""L2-RESILIENCY-001 source-time normalization V0.2.

SOURCE-ONLY. No sweep construction, replenishment, midpoint outcome, return or PnL.

Canonical clocks:
- top-level envelope time = archive availability/order
- raw.data.time = payload snapshot time
- stale payload rewind = preserve evidence, quarantine from normalized state continuity
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Optional

ISO_RE = re.compile(r"^(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2})(?:\\.(\\d+))?Z?$")


class NormalizationFailure(RuntimeError):
    pass


def parse_envelope_ns(value: str) -> int:
    if not isinstance(value, str):
        raise NormalizationFailure("envelope time must be string")
    m = ISO_RE.fullmatch(value.strip())
    if not m:
        raise NormalizationFailure("invalid envelope timestamp")
    base, frac = m.groups()
    d = dt.datetime.strptime(base, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    ns = ((frac or "") + "000000000")[:9]
    return int(d.timestamp()) * 1_000_000_000 + int(ns)


@dataclass(frozen=True)
class NormalizedDecision:
    envelope_ns: int
    payload_ms: int
    classification: str
    accepted_for_state: bool
    last_accepted_payload_ms: int
    rewind_ms: int


class SegmentNormalizer:
    """Deterministic per-contiguous-source-segment timestamp normalizer."""

    def __init__(self) -> None:
        self.last_envelope_ns: Optional[int] = None
        self.last_accepted_payload_ms: Optional[int] = None

    def consume(self, envelope_time: str, payload_ms: int) -> NormalizedDecision:
        if isinstance(payload_ms, bool) or not isinstance(payload_ms, int):
            raise NormalizationFailure("payload timestamp must be integer ms")

        env_ns = parse_envelope_ns(envelope_time)

        if self.last_envelope_ns is not None and env_ns < self.last_envelope_ns:
            raise NormalizationFailure("envelope time moved backwards")

        if payload_ms * 1_000_000 > env_ns:
            raise NormalizationFailure("payload timestamp is later than envelope")

        previous = self.last_accepted_payload_ms
        if previous is None:
            classification = "BASELINE"
            accepted = True
            rewind = 0
            new_last = payload_ms
        elif payload_ms < previous:
            classification = "STALE_LATE_PAYLOAD"
            accepted = False
            rewind = previous - payload_ms
            new_last = previous
        elif payload_ms == previous:
            classification = "EQUAL_PAYLOAD_TIME"
            accepted = True
            rewind = 0
            new_last = payload_ms
        else:
            classification = "FORWARD_PAYLOAD"
            accepted = True
            rewind = 0
            new_last = payload_ms

        self.last_envelope_ns = env_ns
        self.last_accepted_payload_ms = new_last

        return NormalizedDecision(
            envelope_ns=env_ns,
            payload_ms=payload_ms,
            classification=classification,
            accepted_for_state=accepted,
            last_accepted_payload_ms=new_last,
            rewind_ms=rewind,
        )

    def reset_for_missing_hour_boundary(self) -> None:
        self.last_envelope_ns = None
        self.last_accepted_payload_ms = None
