#!/usr/bin/env python3
"""Deterministic synthetic self-test for the PMD-001 V0.12 event decoder."""
from __future__ import annotations

import base64

from extract_chain_exact_features_v012 import (
    TRADE_EVENT_DISC,
    b58encode,
    extract_events,
    window_metrics,
)


def u64(x: int) -> bytes:
    return int(x).to_bytes(8, "little", signed=False)


def i64(x: int) -> bytes:
    return int(x).to_bytes(8, "little", signed=True)


def main() -> None:
    mint_raw = bytes(range(1, 33))
    user_raw = bytes(range(33, 65))
    mint = b58encode(mint_raw)
    user = b58encode(user_raw)
    block_time = 1_800_000_000
    payload = b"".join([
        TRADE_EVENT_DISC,
        mint_raw,
        u64(1_250_000_000),
        u64(77_000_000),
        b"\x01",
        user_raw,
        i64(block_time),
        u64(31_250_000_000),
        u64(999_000_000_000),
        u64(1_250_000_000),
        u64(888_000_000_000),
    ])
    item = {
        "transaction": {"message": {"accountKeys": [mint, user], "instructions": []}},
        "meta": {"err": None, "logMessages": ["Program data: " + base64.b64encode(payload).decode()], "innerInstructions": []},
    }
    events = extract_events(item, mint, block_time)
    assert len(events) == 1, events
    ev = events[0]
    assert ev["mint"] == mint
    assert ev["user"] == user
    assert ev["side"] == "buy"
    assert abs(ev["sol_amount"] - 1.25) < 1e-12
    ev["block_time"] = block_time - 5
    audit = [{"block_time": block_time - 5, "intent_count": 1, "undecoded_intents": 0, "ambiguous_events": 0}]
    m = window_metrics([ev], audit, float(block_time), 30, True)
    assert m["decoder_complete"] is True
    assert m["buy_count"] == 1 and m["sell_count"] == 0
    assert m["unique_participants"] == 1
    assert abs(m["net_flow_sol"] - 1.25) < 1e-12
    assert abs(m["volume_balance"] - 1.0) < 1e-12
    assert TRADE_EVENT_DISC.hex() == "bddb7fd34ee661ee"
    print("PMD-001 V0.12 synthetic decoder self-test: PASS")


if __name__ == "__main__":
    main()
