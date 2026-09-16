from __future__ import annotations

import json
import math
import time
import urllib.parse

from research import tfg_donchian_1d_oos_2025_runner_v01c1 as c1

FIX_PATH = c1.base.ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_2025_OOS_TECHNICAL_API_LIMIT_FIX_V0.1C2.json"
EXPECTED_FIX_FP = "611ff5d056ea4cf7565abb343cc1ae6a3e07d40641ffe21d4913987481f52cab"


def verify_fix() -> dict:
    payload = json.loads(FIX_PATH.read_text(encoding="utf-8"))
    assert payload["fix_id"] == "TFG-DONCHIAN-1D-001-OOS2025-V0.1C2-API-LIMIT"
    assert payload["status"] == "FROZEN_BEFORE_2025_OUTCOME_EVALUATION"
    assert payload["failed_run"]["2025_data_accessed"] is False
    assert payload["failed_run"]["2025_outcome_evaluation_performed"] is False
    assert payload["failed_run"]["2026_accessed"] is False
    assert payload["fix"]["api_interval_enum"] == "60m"
    assert payload["fix"]["pagination_window_hours_to"] == 500
    for key in ("scientific_rule_changed", "source_changed", "assets_changed", "costs_changed", "oos_window_changed", "decision_gates_changed"):
        assert payload["fix"][key] is False
    clone = dict(payload)
    stored = clone.pop("fingerprint")
    assert stored == EXPECTED_FIX_FP
    assert c1.base.canonical_hash(clone) == EXPECTED_FIX_FP
    return payload


def fetch_mexc_60m_500(symbol: str, start_ms: int, end_ms_exclusive: int):
    rows = []
    cursor = start_ms
    window = 500 * c1.base.HOUR_MS
    while cursor < end_ms_exclusive:
        chunk_end = min(end_ms_exclusive, cursor + window)
        params = urllib.parse.urlencode({
            "symbol": symbol,
            "interval": "60m",
            "startTime": cursor,
            "endTime": chunk_end - 1,
            "limit": 500,
        })
        payload = c1.base._request_json("https://api.mexc.com/api/v3/klines?" + params)
        if not isinstance(payload, list):
            raise RuntimeError(f"MEXC_RESPONSE_NOT_LIST:{symbol}:{type(payload).__name__}")
        chunk = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 6:
                raise RuntimeError(f"MEXC_MALFORMED_KLINE:{symbol}")
            t = int(item[0])
            if not (cursor <= t < chunk_end):
                continue
            if t % c1.base.HOUR_MS != 0:
                raise RuntimeError(f"MEXC_60M_NOT_UTC_ALIGNED:{symbol}:{t}")
            o, h, l, c, v = map(float, (item[1], item[2], item[3], item[4], item[5]))
            if not all(math.isfinite(x) for x in (o, h, l, c, v)):
                raise RuntimeError(f"MEXC_NONFINITE:{symbol}:{t}")
            if min(o, h, l, c) <= 0 or v < 0 or h < max(o, c, l) or l > min(o, c, h):
                raise RuntimeError(f"MEXC_INVALID_OHLC:{symbol}:{t}")
            chunk.append(c1.base.common.Candle(t, o, h, l, c, v, t + c1.base.HOUR_MS - 1))
        chunk.sort(key=lambda x: x.open_time)
        expected = list(range(cursor, chunk_end, c1.base.HOUR_MS))
        observed = [x.open_time for x in chunk]
        if observed != expected:
            missing = sorted(set(expected) - set(observed))
            extra = sorted(set(observed) - set(expected))
            raise RuntimeError(
                f"MEXC_60M_500_CONTINUITY_FAIL:{symbol}:{c1.base._iso(cursor)}:{c1.base._iso(chunk_end)}:"
                f"count={len(chunk)}:expected={len(expected)}:missing={[c1.base._iso(x) for x in missing[:5]]}:extra={[c1.base._iso(x) for x in extra[:5]]}"
            )
        rows.extend(chunk)
        cursor = chunk_end
        time.sleep(0.02)
    if len({r.open_time for r in rows}) != len(rows):
        raise RuntimeError(f"MEXC_DUPLICATE_60M:{symbol}")
    return rows


def main() -> int:
    verify_fix()
    c1.fetch_mexc_60m = fetch_mexc_60m_500
    return c1.main()


if __name__ == "__main__":
    raise SystemExit(main())
