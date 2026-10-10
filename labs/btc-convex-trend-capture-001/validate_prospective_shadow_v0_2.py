#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — V0.2 AGGRESSIVE SHADOW EVIDENCE VALIDATOR

Technical fail-closed validator only.
It does not generate signals, change rules, tune parameters, or create promotion authority.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
FORWARD_START = datetime(2026, 9, 24, 7, 0, 0, tzinfo=timezone.utc)
FORWARD_START_MS = int(FORWARD_START.timestamp() * 1000)
HOUR_MS = 3_600_000

DEFAULT = Path(__file__).resolve().parent / "evidence" / "PROSPECTIVE_SHADOW_SNAPSHOT_V0.2_AGGRESSIVE.json"


def fail(msg: str) -> None:
    raise SystemExit(f"V0.2_EVIDENCE_VALIDATION_FAIL: {msg}")


def finite_number(v, name: str) -> None:
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(float(v)):
        fail(f"{name} must be finite numeric")


def main() -> None:
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not p.exists():
        fail(f"missing snapshot {p}")

    x = json.loads(p.read_text(encoding="utf-8"))
    if x.get("lab") != "BTC-CONVEX-TREND-CAPTURE-001":
        fail("lab identity mismatch")
    if x.get("snapshot") != "PROSPECTIVE_SHADOW_SNAPSHOT_V0.2_AGGRESSIVE":
        fail("snapshot identity mismatch")
    if x.get("authority") != "PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE":
        fail("authority mismatch")
    if x.get("forward_start_utc") != FORWARD_START.isoformat():
        fail("forward boundary mismatch")

    try:
        snap = datetime.fromisoformat(x["snapshot_time_utc"])
    except Exception as e:
        fail(f"invalid snapshot_time_utc: {e}")
    if snap.tzinfo is None:
        fail("snapshot_time_utc must be timezone-aware")
    snap_ms = int(snap.timestamp() * 1000)

    symbols = x.get("symbols")
    family = x.get("family")
    if not isinstance(symbols, dict) or not isinstance(family, dict):
        fail("missing symbols/family")
    if list(symbols.keys()) != EXPECTED_SYMBOLS:
        fail(f"frozen universe/order mismatch: {list(symbols.keys())}")

    valid = family.get("valid_symbols")
    blocked = family.get("blocked_symbols")
    if not isinstance(valid, list) or not isinstance(blocked, list):
        fail("valid_symbols/blocked_symbols must be lists")
    if set(valid) | set(blocked) != set(EXPECTED_SYMBOLS) or set(valid) & set(blocked):
        fail("valid/blocked partition does not equal frozen universe")

    total_closed = 0
    assets_ge5 = 0

    for s in EXPECTED_SYMBOLS:
        node = symbols[s]
        status = node.get("source_status")
        result = node.get("result")

        if s in blocked:
            if status != "FORWARD_DATA_BLOCKED" or result is not None:
                fail(f"{s}: blocked state inconsistent")
            continue

        if status != "PASS" or not isinstance(result, dict):
            fail(f"{s}: valid symbol must be PASS with result")

        signals = result.get("signals")
        trades = result.get("trades")
        if not isinstance(signals, list) or not isinstance(trades, list):
            fail(f"{s}: signals/trades must be lists")
        if result.get("signal_count") != len(signals):
            fail(f"{s}: signal_count mismatch")
        if result.get("closed_trades") != len(trades):
            fail(f"{s}: closed_trades mismatch")
        if result.get("wins", 0) + result.get("losses", 0) != len(trades):
            fail(f"{s}: wins/losses mismatch")

        completed = result.get("completed_forward_bars")
        if not isinstance(completed, int) or completed < 0:
            fail(f"{s}: invalid completed_forward_bars")
        if completed > 0 and result.get("first_forward_bar_t") != FORWARD_START_MS:
            fail(f"{s}: first forward bar boundary mismatch")

        for i, sig in enumerate(signals):
            ot = sig.get("decision_bar_open_t")
            ct = sig.get("decision_bar_close_t")
            if not isinstance(ot, int) or not isinstance(ct, int):
                fail(f"{s}: signal {i} timestamps invalid")
            if ot < FORWARD_START_MS:
                fail(f"{s}: pre-boundary signal")
            if ct < ot or ct >= snap_ms:
                fail(f"{s}: non-causal signal close timestamp")

        for i, tr in enumerate(trades):
            et, xt = tr.get("entry_t"), tr.get("exit_t")
            if not isinstance(et, int) or not isinstance(xt, int):
                fail(f"{s}: trade {i} timestamps invalid")
            if et < FORWARD_START_MS + HOUR_MS:
                fail(f"{s}: trade {i} entry precedes earliest causal next-bar entry")
            if xt < et:
                fail(f"{s}: trade {i} exit precedes entry")
            for k in ("entry", "exit", "net_pnl", "funding", "commission", "slippage_cost", "return_pct"):
                finite_number(tr.get(k), f"{s}.trade[{i}].{k}")

        op = result.get("open_position")
        if op is not None:
            if not isinstance(op, dict):
                fail(f"{s}: open_position invalid")
            if op.get("entry_t", 0) < FORWARD_START_MS + HOUR_MS:
                fail(f"{s}: open position pre-causal boundary")
            for k in ("entry", "qty", "peak", "initial_stop", "active_stop", "funding", "marked_price"):
                finite_number(op.get(k), f"{s}.open_position.{k}")
            if op["entry"] <= 0 or op["qty"] <= 0 or op["initial_stop"] <= 0 or op["active_stop"] <= 0:
                fail(f"{s}: non-positive long position field")
            if op["active_stop"] + 1e-12 < op["initial_stop"]:
                fail(f"{s}: active stop below frozen hard stop")
            if op["active_stop"] - 1e-12 > op["peak"]:
                fail(f"{s}: active stop above observed peak")
            if result.get("pending_entry") is True:
                fail(f"{s}: cannot be pending and open simultaneously")

        total_closed += len(trades)
        assets_ge5 += int(len(trades) >= 5)

    if family.get("closed_trades_total") != total_closed:
        fail("family closed_trades_total mismatch")
    if family.get("assets_with_ge_5_closed_trades") != assets_ge5:
        fail("family assets_with_ge_5_closed_trades mismatch")

    cp = family.get("v3_aggressive_checkpoints")
    if not isinstance(cp, dict):
        fail("missing v3_aggressive_checkpoints")
    clean = len(blocked) == 0
    causal = cp.get("causal_integrity_blocker")
    if not isinstance(causal, bool):
        fail("causal_integrity_blocker must be boolean")
    expected_a = total_closed >= 10
    expected_b = total_closed >= 25 and assets_ge5 >= 2 and clean and not causal
    expected_c = total_closed >= 50 and assets_ge5 >= 3 and clean and not causal

    if cp.get("source_coverage_clean") is not clean:
        fail("source_coverage_clean mismatch")
    if cp.get("A_10_trades_operational_audit") is not expected_a:
        fail("Checkpoint A mismatch")
    if cp.get("B_25_trades_fragility_audit") is not expected_b:
        fail("Checkpoint B mismatch")
    if cp.get("C_50_trades_v3_readjudication") is not expected_c:
        fail("Checkpoint C mismatch")

    expected_state = (
        "CHECKPOINT_C_READY_FOR_V3_READJUDICATION" if expected_c else
        "CHECKPOINT_B_REACHED" if expected_b else
        "CHECKPOINT_A_REACHED" if expected_a else
        "FORWARD_COLLECTING_ONLY"
    )
    if family.get("current_state") != expected_state:
        fail("family current_state mismatch")
    if family.get("tier_promotion_automatic") is not False:
        fail("automatic promotion must remain disabled")

    print(json.dumps({
        "validator": "BTC-CONVEX-V0.2-EVIDENCE-VALIDATOR",
        "result": "PASS",
        "closed_trades_total": total_closed,
        "assets_with_ge_5_closed_trades": assets_ge5,
        "checkpoint_A": expected_a,
        "checkpoint_B": expected_b,
        "checkpoint_C": expected_c,
        "source_coverage_clean": clean,
        "causal_integrity_blocker": causal,
    }, indent=2))


if __name__ == "__main__":
    main()
