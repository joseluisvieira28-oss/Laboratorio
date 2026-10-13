"""BTC-CONVEX multifront: offline, no exchange/network/order side effects.

Source price paths are ONLY proxies. Synthetic tests validate causality and
arithmetic, not executable fills or profitable forward trading.
Authority: PRE_OUTCOME_FREEZE_2026-10-13.md.
"""
from __future__ import annotations
import math
import re

H = 3_600_000
FIVE = 300_000
BOUNDARY = 1_792_022_400_000  # 2026-10-15T00:00:00Z
MAX_WITNESS_LAG = 600_000
BASE_FEE = 0.0008
TP = 0.0075
STOP = 0.0035
MAX_HOLD = 4 * H


def _finite(*values):
    return all(isinstance(x, (float, int)) and math.isfinite(x) for x in values)


def validate_signal(signal):
    """Witness must be recorded promptly AFTER the 1h signal has closed."""
    try:
        t = signal["bar_open_ms"]
        witnessed = signal["witness_ms"]
        sha = signal["source_sha256"]
    except (KeyError, TypeError):
        return "SIGNAL_PROVENANCE_BLOCKED"
    if not isinstance(t, int) or t % H or t < BOUNDARY:
        return "OUTSIDE_NEW_BOUNDARY"
    if not isinstance(witnessed, int) or not (t + H <= witnessed <= t + H + MAX_WITNESS_LAG):
        return "NOT_TIMELY_AT_T0"
    if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None:
        return "SIGNAL_PROVENANCE_BLOCKED"
    if signal.get("symbol") != "BTCUSDT" or signal.get("side") != "LONG":
        return "UNFROZEN_SYMBOL_OR_DIRECTION"
    return "PASS"


def causal_first_5m_open(signal):
    """Never backfill the already-passed next-hour open when witness is late."""
    status = validate_signal(signal)
    if status != "PASS":
        raise ValueError(status)
    witness = signal["witness_ms"]
    return ((witness // FIVE) + 1) * FIVE  # strictly AFTER witness


def _valid_bar(b, t):
    fields = ("t", "open", "high", "low", "close")
    if not isinstance(b, dict) or any(x not in b for x in fields):
        return False
    o, hi, lo, c = (b[x] for x in ("open", "high", "low", "close"))
    return (
        isinstance(b["t"], int) and b["t"] == t and
        _finite(o, hi, lo, c) and lo > 0 and
        lo <= min(o, c) and hi >= max(o, c)
    )


def fast_rebound(signal, five_minute_bars, *,
                 slip_bps=2.0, funding_events=(), funding_attested=False):
    """F2 paper path, stop-first; no quote -> NEVER declare executable.

    Price PnL includes both taker fees and assumed adverse price slippage.
    Funding cash flow is a fraction of entry notional (positive means received).
    The 4h end is a completed 5m bar, with no forced liquidation of open paths.
    """
    gate = validate_signal(signal)
    if gate != "PASS":
        return {"status": gate, "net_pct": None}
    if not funding_attested:
        return {"status": "FUNDING_NOT_ATTESTED", "net_pct": None}
    if not _finite(slip_bps) or slip_bps < 0:
        return {"status": "INVALID_COST_INPUT", "net_pct": None}
    entry_t = causal_first_5m_open(signal)
    if not five_minute_bars:
        return {"status": "OPEN_UNRESOLVED", "net_pct": None}
    if len(five_minute_bars) > MAX_HOLD // FIVE:
        return {"status": "UNFROZEN_HORIZON_INPUT", "net_pct": None}
    for j, b in enumerate(five_minute_bars):
        if not _valid_bar(b, entry_t + j * FIVE):
            return {"status": "SOURCE_GAP_OR_BAD_OHLC", "net_pct": None}
    funding_map = {}
    for f in funding_events:
        if not isinstance(f, dict) or "t" not in f or "cash_fraction" not in f:
            return {"status": "FUNDING_BAD_RECORD", "net_pct": None}
        ts, cash = f["t"], f["cash_fraction"]
        if not isinstance(ts, int) or ts in funding_map or not _finite(cash):
            return {"status": "FUNDING_BAD_RECORD", "net_pct": None}
        funding_map[ts] = cash
    slip = slip_bps / 10000.0
    entry_raw = five_minute_bars[0]["open"]
    entry = entry_raw * (1 + slip)
    stop = entry * (1 - STOP)
    target = entry * (1 + TP)
    exit_raw, exit_t, why = None, None, None
    for i, b in enumerate(five_minute_bars):
        if b["open"] <= stop:
            exit_raw, why = b["open"], "STOP_GAP"
        elif b["open"] >= target:
            exit_raw, why = b["open"], "TARGET_GAP"
        elif b["low"] <= stop:
            exit_raw, why = stop, "STOP_FIRST"
        elif b["high"] >= target:
            exit_raw, why = target, "TARGET"
        elif i == MAX_HOLD // FIVE - 1:
            exit_raw, why = b["close"], "TIME_EXIT"
        if why is not None:
            exit_t = b["t"] + FIVE
            break
    if why is None:
        return {"status": "OPEN_UNRESOLVED", "net_pct": None,
                "entry_t": entry_t, "bars_seen": len(five_minute_bars)}
    # Exact future funding settlement coverage is an upstream source gate.
    accrued = sum(cash for t, cash in funding_map.items() if entry_t < t <= exit_t)
    if any(t < entry_t or t > exit_t for t in funding_map):
        return {"status": "FUNDING_OUTSIDE_POSITION", "net_pct": None}
    exit_exec = exit_raw * (1 - slip)
    price_pnl = (exit_exec - entry) / entry
    fees = BASE_FEE * (1 + exit_exec / entry)
    net = price_pnl - fees + accrued
    return {"status": "MODEL_ONLY_NOT_EXECUTABLE", "entry_t": entry_t,
            "exit_t": exit_t, "exit_reason": why,
            "entry_proxy": entry, "exit_proxy": exit_exec,
            "price_pnl_fraction": price_pnl, "fee_fraction": fees,
            "funding_fraction": accrued, "net_pct": 100 * net}


def observed_quote_pair(witness_ms, quotes, *, notional_usdt=100.0):
    """F1 source-only first-now vs first-at+5m ask comparison.

    Quote MUST be contemporaneous, immutable witness supplied elsewhere.
    In absence of source/size evidence: BLOCK instead of guessed fills.
    """
    if not isinstance(witness_ms, int) or not _finite(notional_usdt) or notional_usdt <= 0:
        return {"status": "BAD_INPUT"}
    def first_at(t):
        eligible = [q for q in quotes
                    if isinstance(q.get("t"), int) and t <= q["t"] <= t + 2000
                    and q.get("venue") == "MEXC"
                    and q.get("witnessed_at_ms") is not None
                    and q["witnessed_at_ms"] >= q["t"]
                    and q["witnessed_at_ms"] <= q["t"] + 2000
                    and _finite(q.get("ask"), q.get("bid"), q.get("depth_ask_usdt"))
                    and q["bid"] > 0 and q["ask"] >= q["bid"]
                    and q["depth_ask_usdt"] >= notional_usdt]
        return min(eligible, key=lambda q: q["t"]) if eligible else None
    a, b = first_at(witness_ms), first_at(witness_ms + FIVE)
    if a is None or b is None:
        return {"status": "QUOTE_OR_DEPTH_BLOCKED", "A": a is not None, "B": b is not None}
    return {"status": "SOURCE_ONLY_NO_FILL_PROOF",
            "entry_improvement_bps_B_vs_A": 10000 * (a["ask"]-b["ask"])/a["ask"],
            "A_ask": a["ask"], "B_ask": b["ask"]}


def normalized_parent_qty(equity, entry, *, fee_bps=8, slip_bps=2,
                          active_planned_risk_fraction=0):
    """F3: capped hypothetical sizing, not guaranteed maximum loss."""
    if not _finite(equity, entry, fee_bps, slip_bps, active_planned_risk_fraction):
        raise ValueError("bad numeric input")
    if equity <= 0 or entry <= 0 or min(fee_bps, slip_bps, active_planned_risk_fraction) < 0:
        raise ValueError("invalid size")
    fee, slip = fee_bps / 10000, slip_bps / 10000
    filled = entry * (1 + slip)
    stop = filled * 0.96 * (1 - slip)
    risk_per_unit = filled - stop + fee * (filled + stop)
    permitted = min(0.0025, max(0, 0.005 - active_planned_risk_fraction))
    qty = min((equity * 0.2) / filled, equity * permitted / risk_per_unit)
    return {"qty": qty, "entry": filled, "planned_stop": stop,
            "planned_loss": qty * risk_per_unit,
            "risk_fraction": qty * risk_per_unit / equity,
            "status": "MODEL_ONLY_NOT_RISK_GUARANTEE"}


def six_hour_placebo_signal(signal):
    """F4: predeclared 6h delayed witness, never rewrites original signal."""
    if validate_signal(signal) != "PASS":
        raise ValueError("original signal invalid")
    p = dict(signal)
    p["bar_open_ms"] += 6 * H
    p["witness_ms"] += 6 * H
    p["control_type"] = "FIXED_DELAY_6H_NOT_A_NEW_PARENT_SIGNAL"
    return p
