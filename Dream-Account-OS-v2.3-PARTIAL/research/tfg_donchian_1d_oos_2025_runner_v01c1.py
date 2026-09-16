from __future__ import annotations

import json
import math
import time
import urllib.parse
from pathlib import Path

from research import tfg_donchian_1d_oos_2025_runner_v01c as base

FIX_PATH = base.ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_2025_OOS_TECHNICAL_API_ENUM_FIX_V0.1C1.json"
EXPECTED_FIX_FP = "34b74fdcf63287e1fba1d60d6f2d09e08f313f159cbd1694b60494d8c4d9105c"


def verify_fix() -> dict:
    payload = json.loads(FIX_PATH.read_text(encoding="utf-8"))
    assert payload["fix_id"] == "TFG-DONCHIAN-1D-001-OOS2025-V0.1C1-API-ENUM"
    assert payload["status"] == "FROZEN_BEFORE_2025_OUTCOME_EVALUATION"
    assert payload["failed_run"]["2025_data_accessed"] is False
    assert payload["failed_run"]["2025_outcome_evaluation_performed"] is False
    assert payload["failed_run"]["2026_accessed"] is False
    assert payload["fix"]["api_interval_enum_to"] == "60m"
    assert payload["fix"]["semantic_timeframe"] == "1H"
    for key in ("scientific_rule_changed", "source_changed", "assets_changed", "costs_changed", "oos_window_changed", "decision_gates_changed"):
        assert payload["fix"][key] is False
    clone = dict(payload)
    stored = clone.pop("fingerprint")
    assert stored == EXPECTED_FIX_FP
    assert base.canonical_hash(clone) == EXPECTED_FIX_FP
    return payload


def fetch_mexc_60m(symbol: str, start_ms: int, end_ms_exclusive: int):
    rows = []
    cursor = start_ms
    window = 1000 * base.HOUR_MS
    while cursor < end_ms_exclusive:
        chunk_end = min(end_ms_exclusive, cursor + window)
        params = urllib.parse.urlencode({
            "symbol": symbol,
            "interval": "60m",
            "startTime": cursor,
            "endTime": chunk_end - 1,
            "limit": 1000,
        })
        payload = base._request_json("https://api.mexc.com/api/v3/klines?" + params)
        if not isinstance(payload, list):
            raise RuntimeError(f"MEXC_RESPONSE_NOT_LIST:{symbol}:{type(payload).__name__}")
        chunk = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 6:
                raise RuntimeError(f"MEXC_MALFORMED_KLINE:{symbol}")
            t = int(item[0])
            if not (cursor <= t < chunk_end):
                continue
            if t % base.HOUR_MS != 0:
                raise RuntimeError(f"MEXC_60M_NOT_UTC_ALIGNED:{symbol}:{t}")
            o, h, l, c, v = map(float, (item[1], item[2], item[3], item[4], item[5]))
            if not all(math.isfinite(x) for x in (o, h, l, c, v)):
                raise RuntimeError(f"MEXC_NONFINITE:{symbol}:{t}")
            if min(o, h, l, c) <= 0 or v < 0 or h < max(o, c, l) or l > min(o, c, h):
                raise RuntimeError(f"MEXC_INVALID_OHLC:{symbol}:{t}")
            chunk.append(base.common.Candle(t, o, h, l, c, v, t + base.HOUR_MS - 1))
        chunk.sort(key=lambda x: x.open_time)
        expected = list(range(cursor, chunk_end, base.HOUR_MS))
        observed = [c.open_time for c in chunk]
        if observed != expected:
            missing = sorted(set(expected) - set(observed))
            extra = sorted(set(observed) - set(expected))
            raise RuntimeError(
                f"MEXC_60M_CHUNK_CONTINUITY_FAIL:{symbol}:{base._iso(cursor)}:{base._iso(chunk_end)}:"
                f"count={len(chunk)}:expected={len(expected)}:missing={[base._iso(x) for x in missing[:5]]}:extra={[base._iso(x) for x in extra[:5]]}"
            )
        rows.extend(chunk)
        cursor = chunk_end
        time.sleep(0.02)
    if len({r.open_time for r in rows}) != len(rows):
        raise RuntimeError(f"MEXC_DUPLICATE_60M:{symbol}")
    return rows


def main() -> int:
    verify_fix()
    # Technical enum correction only. All scientific logic remains the V0.1C frozen implementation.
    base.fetch_mexc_1h = fetch_mexc_60m
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
