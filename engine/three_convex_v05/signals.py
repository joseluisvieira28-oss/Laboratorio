"""Deterministic source-locked CONVEX V5 signal/close-time engine.

Only the original five signal functions are compiled from a pinned text copy
of the historic parent using AST. Nothing else from that script is executed.
No sockets, credentials, exchange writes, or executable broker adapters.
"""
from __future__ import annotations
import ast
from collections import deque
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path

MS5 = 300000
PERIODS = {"SOL_CONVEX_NATIVE_5M": 1,
           "SOL_CONVEX_1H": 12,
           "BNB_CONVEX_4H": 48}
SYMBOLS = {"SOL_CONVEX_NATIVE_5M": "SOL_USDT",
           "SOL_CONVEX_1H": "SOL_USDT",
           "BNB_CONVEX_4H": "BNB_USDT"}
PARENT_GIT_BLOB = "19c8b8e2363f253458db42111b6701f3a3ef1f4b"
PARENT_PATH = Path(__file__).parent / "vendor" / "V5_PARENT_PINNED_SOURCE.py.txt"
SIGNAL_FUNCTION_NAMES = ("sma", "stdev", "rma", "rsi", "build_signals")


class Halt(ValueError):
    pass


@dataclass(frozen=True)
class Bar:
    t: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def validate(self):
        if type(self.t) is not int or self.t < 0 or self.t % MS5:
            raise Halt("BAD_FIVE_MINUTE_TIMESTAMP")
        vals = (self.open, self.high, self.low, self.close, self.volume)
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in vals):
            raise Halt("NONFINITE_CANDLE")
        if min(self.open, self.high, self.low, self.close) <= 0 or self.volume < 0:
            raise Halt("NONPOSITIVE_CANDLE")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise Halt("IMPOSSIBLE_OHLC")
        if self.low > self.high:
            raise Halt("IMPOSSIBLE_RANGE")
        return self

    def to_parent(self):
        return dict(t=self.t, open=self.open, high=self.high, low=self.low,
                    close=self.close, volume=self.volume)


def git_blob_sha(raw):
    h = hashlib.sha1()
    h.update(("blob " + str(len(raw)) + "\x00").encode("ascii"))
    h.update(raw)
    return h.hexdigest()


def parent_signal_function(source_path=PARENT_PATH):
    raw = Path(source_path).read_bytes()
    if git_blob_sha(raw) != PARENT_GIT_BLOB:
        raise Halt("V5_PARENT_BLOB_IDENTITY_MISMATCH")
    tree = ast.parse(raw, filename=str(source_path))
    found = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in SIGNAL_FUNCTION_NAMES}
    if set(found) != set(SIGNAL_FUNCTION_NAMES):
        raise Halt("V5_PARENT_SIGNAL_DEFINITIONS_MISSING")
    # The single trusted parent was vetted and pinned to this exact Git blob.
    # Only functions are compiled, never the top-level program (no network).
    sub = ast.Module(body=[found[n] for n in SIGNAL_FUNCTION_NAMES],
                     type_ignores=[])
    ast.fix_missing_locations(sub)
    ns = {"math": math, "deque": deque}
    exec(compile(sub, "<pinned_v5_signal_functions_only>", "exec"), ns)
    return ns["build_signals"]


def aggregate_complete(candles, n):
    """Strict left-aligned resampling from canonical sequential closed 5m."""
    if type(n) is not int or n <= 0:
        raise Halt("BAD_TIMEFRAME")
    if not candles:
        return []
    bars = [b.validate() for b in candles]
    if any(b.t != bars[0].t + i * MS5 for i, b in enumerate(bars)):
        raise Halt("GAP_OR_DUPLICATE_OR_REORDERED_CANONICAL_BARS")
    if n == 1:
        return [b.to_parent() for b in bars]
    out = []
    start = 0
    while start < len(bars):
        group_t = (bars[start].t // (n * MS5)) * (n * MS5)
        aligned_first = group_t == bars[start].t
        chunk = bars[start:start+n]
        if aligned_first and len(chunk) == n and chunk[-1].t == group_t + (n-1)*MS5:
            out.append(dict(t=group_t, open=chunk[0].open,
                            high=max(b.high for b in chunk),
                            low=min(b.low for b in chunk),
                            close=chunk[-1].close,
                            volume=sum(b.volume for b in chunk)))
            start += n
        elif not aligned_first:
            start += ((group_t + n * MS5 - bars[start].t) // MS5)
        else:
            break
    return out


def closed_signal_decisions(symbol, candles, now_ms, *, warmup_bars=250):
    """Signal on completed 5m / 1h / 4h only, entry at close+5m.

    warmup_bars is a conservative operational floor, not a new V5 filter.
    Exact historical RSI equality needs the same start of indicator history;
    do not claim external signal parity solely on passing these calculations.
    """
    if symbol not in ("SOL_USDT", "BNB_USDT"):
        raise Halt("UNKNOWN_SYMBOL")
    if type(now_ms) is not int:
        raise Halt("INVALID_CLOCK")
    if not candles:
        return []
    ordered = list(candles)
    if ordered[-1].t + MS5 + 1000 > now_ms:
        raise Halt("INCOMPLETE_OR_NONCAUSAL_BAR")
    if ordered[0].t > ordered[-1].t:
        raise Halt("REVERSED_BAR_SOURCE")
    fn = parent_signal_function()
    results = []
    for lane, n in PERIODS.items():
        if SYMBOLS[lane] != symbol:
            continue
        tf = aggregate_complete(ordered, n)
        if len(tf) < warmup_bars:
            continue
        last = tf[-1]
        if last["t"] + n * MS5 != ordered[-1].t + MS5:
            continue  # last 5m bar is not the last bar of this TF
        flags, details = fn(tf)
        if flags[-1]:
            close_ms = last["t"] + n * MS5
            results.append({
                "lane": lane, "symbol": symbol,
                "signal_close_ms": close_ms,
                "entry_open_ms": close_ms + MS5,
                "tf_minutes": 5*n,
                "signal_id": f"{lane}:{close_ms}",
                "score": details[-1]["score"],
                "signal_source": "PINNED_V5_PARENT_BLOB",
                "historical_signal_parity_externally_proven": False,
            })
    return results
