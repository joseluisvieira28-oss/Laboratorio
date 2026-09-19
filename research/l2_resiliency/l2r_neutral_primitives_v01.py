#!/usr/bin/env python3
"""Neutral L2 primitives for L2-RESILIENCY-001.

PRE-DISCOVERY / OUTCOME-BLIND.
No sweep threshold, event count, replenishment label, midpoint outcome or PnL.
"""
from __future__ import annotations
from dataclasses import dataclass
from bisect import bisect_left
from typing import Sequence


class PrimitiveFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class Top5State:
    envelope_ns: int
    payload_ms: int
    bid_px: tuple[float, float, float, float, float]
    bid_sz: tuple[float, float, float, float, float]
    ask_px: tuple[float, float, float, float, float]
    ask_sz: tuple[float, float, float, float, float]

    @property
    def midpoint(self) -> float:
        return (self.bid_px[0] + self.ask_px[0]) / 2.0

    @property
    def bid_depth5(self) -> float:
        return sum(self.bid_sz)

    @property
    def ask_depth5(self) -> float:
        return sum(self.ask_sz)


def _num(x) -> float:
    if isinstance(x, bool):
        raise PrimitiveFailure("boolean numeric field")
    try:
        v = float(x)
    except Exception as exc:
        raise PrimitiveFailure("non-numeric field") from exc
    if not (v == v and abs(v) != float("inf")):
        raise PrimitiveFailure("non-finite field")
    return v


def extract_top5(envelope_ns: int, payload_ms: int, levels) -> Top5State:
    if not isinstance(levels, list) or len(levels) != 2:
        raise PrimitiveFailure("expected two book sides")
    bids, asks = levels
    if len(bids) < 5 or len(asks) < 5:
        raise PrimitiveFailure("need at least five levels per side")

    bp, bs, ap, ass = [], [], [], []
    for side, pxs, szs in ((bids, bp, bs), (asks, ap, ass)):
        for level in side[:5]:
            if not isinstance(level, dict):
                raise PrimitiveFailure("level not object")
            px, sz = _num(level.get("px")), _num(level.get("sz"))
            n = level.get("n")
            if px <= 0 or sz < 0 or isinstance(n, bool) or not isinstance(n, int) or n < 0:
                raise PrimitiveFailure("invalid level")
            pxs.append(px); szs.append(sz)

    if not all(bp[i] > bp[i+1] for i in range(4)):
        raise PrimitiveFailure("bids not descending")
    if not all(ap[i] < ap[i+1] for i in range(4)):
        raise PrimitiveFailure("asks not ascending")
    if bp[0] >= ap[0]:
        raise PrimitiveFailure("locked/crossed book")

    return Top5State(
        envelope_ns=envelope_ns,
        payload_ms=payload_ms,
        bid_px=tuple(bp), bid_sz=tuple(bs),
        ask_px=tuple(ap), ask_sz=tuple(ass),
    )


def first_state_at_or_after(
    states: Sequence[Top5State],
    anchor_envelope_ns: int,
    horizon_ms: int,
    max_lateness_ms: int | None = None,
) -> Top5State | None:
    """Return first state whose availability time is >= anchor+horizon.

    No interpolation. Optional max_lateness is a source-quality guard only and
    must be frozen separately before scientific use.
    """
    if horizon_ms < 0:
        raise PrimitiveFailure("negative horizon")
    target = anchor_envelope_ns + horizon_ms * 1_000_000
    times = [x.envelope_ns for x in states]
    i = bisect_left(times, target)
    if i >= len(states):
        return None
    x = states[i]
    if max_lateness_ms is not None:
        late_ms = (x.envelope_ns - target) / 1_000_000
        if late_ms > max_lateness_ms:
            return None
    return x


FROZEN_HORIZONS_MS = (1000, 5000, 15000, 60000)
