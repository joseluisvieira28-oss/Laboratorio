from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

BASE_URL = "https://api.mexc.com/api/v3/klines"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_UTC = "2023-02-01T00:00:00Z"
SEED_END_UTC = "2026-09-16T12:00:00Z"
FIFTEEN_MS = 900_000
TWELVE_H_MS = 43_200_000
DAY_MS = 86_400_000
ATR_LENGTH = 28
DONCHIAN_LOOKBACK = 40
DAILY_HISTORY = 220
OUT = Path("radar/seeds/tfg_donchian_regime_v1_seed.json")
UA = "crypto-edge-radar-donchian-seed-v0.7/1.0"


def ms(ts: str) -> int:
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)


@dataclass(frozen=True)
class Bar:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def canonical_hash(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def get_json(url: str, retries: int = 5):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status != 200:
                    raise RuntimeError(f"HTTP {r.status}")
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(min(8, 2 ** attempt))
    raise RuntimeError(f"MEXC request failed: {last}")


def fetch_range(symbol: str, interval: str, start: int, end_exclusive: int, step_ms: int) -> list[Bar]:
    rows: list[Bar] = []
    cursor = start
    requests = 0
    while cursor < end_exclusive:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": str(cursor),
            "endTime": str(end_exclusive - 1),
            "limit": "1000",
        }
        payload = get_json(BASE_URL + "?" + urllib.parse.urlencode(params))
        requests += 1
        if not isinstance(payload, list):
            raise RuntimeError(f"unexpected MEXC payload for {symbol} {interval}: {type(payload).__name__}")
        parsed = []
        for x in payload:
            if not isinstance(x, list) or len(x) < 6:
                raise RuntimeError(f"malformed MEXC kline for {symbol} {interval}")
            t = int(x[0])
            if t < cursor or t >= end_exclusive:
                continue
            parsed.append(Bar(t, float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])))
        parsed.sort(key=lambda b: b.open_time)
        if not parsed:
            raise RuntimeError(f"SOURCE_HISTORY_UNAVAILABLE:{symbol}:{interval}:{cursor}")
        if parsed[0].open_time != cursor:
            raise RuntimeError(f"SOURCE_GAP_AT_CURSOR:{symbol}:{interval}:expected={cursor}:got={parsed[0].open_time}")
        for b in parsed:
            if b.open_time % step_ms != 0:
                raise RuntimeError(f"MISALIGNED_BAR:{symbol}:{interval}:{b.open_time}")
            if min(b.open, b.high, b.low, b.close) <= 0 or b.volume < 0:
                raise RuntimeError(f"INVALID_OHLCV:{symbol}:{interval}:{b.open_time}")
            if b.high < max(b.open, b.close, b.low) or b.low > min(b.open, b.close, b.high):
                raise RuntimeError(f"INVALID_RANGE:{symbol}:{interval}:{b.open_time}")
        if rows and parsed[0].open_time <= rows[-1].open_time:
            raise RuntimeError(f"NONMONOTONIC_PAGE:{symbol}:{interval}")
        rows.extend(parsed)
        cursor = parsed[-1].open_time + step_ms
        if requests > 2000:
            raise RuntimeError(f"PAGINATION_RUNAWAY:{symbol}:{interval}")
        time.sleep(0.025)
    expected = (end_exclusive - start) // step_ms
    if len(rows) != expected:
        raise RuntimeError(f"SOURCE_COUNT_MISMATCH:{symbol}:{interval}:expected={expected}:got={len(rows)}")
    for i in range(1, len(rows)):
        if rows[i].open_time != rows[i - 1].open_time + step_ms:
            raise RuntimeError(f"SOURCE_GAP:{symbol}:{interval}:{rows[i-1].open_time}:{rows[i].open_time}")
    return rows


def aggregate_12h(rows: list[Bar]) -> list[Bar]:
    if len(rows) % 48 != 0:
        raise RuntimeError(f"15m count not divisible by 48: {len(rows)}")
    out: list[Bar] = []
    for i in range(0, len(rows), 48):
        chunk = rows[i:i + 48]
        start = chunk[0].open_time
        if start % TWELVE_H_MS != 0:
            raise RuntimeError(f"12H_ALIGNMENT_FAIL:{start}")
        expected = [start + j * FIFTEEN_MS for j in range(48)]
        if [x.open_time for x in chunk] != expected:
            raise RuntimeError(f"INCOMPLETE_12H:{start}")
        out.append(
            Bar(
                start,
                chunk[0].open,
                max(x.high for x in chunk),
                min(x.low for x in chunk),
                chunk[-1].close,
                sum(x.volume for x in chunk),
            )
        )
    return out


def atr_series(bars: list[Bar], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(bars)
    if len(bars) <= length:
        return out
    trs: list[float | None] = [None]
    for i in range(1, len(bars)):
        c, p = bars[i], bars[i - 1]
        trs.append(max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)))
    seed = [float(x) for x in trs[1:length + 1] if x is not None]
    if len(seed) != length:
        return out
    value = mean(seed)
    out[length] = value
    for i in range(length + 1, len(bars)):
        value = ((value * (length - 1)) + float(trs[i])) / length
        out[i] = value
    return out


def main() -> int:
    start = ms(START_UTC)
    seed_end = ms(SEED_END_UTC)
    result = {
        "seed_id": "TFG-DONCHIAN-REGIME-V1-RUNTIME-SEED-V0.7",
        "status": "SOURCE_SEED_PASS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "provider": "MEXC",
            "market": "SPOT",
            "access": "PUBLIC_UNAUTHENTICATED_READ_ONLY_REST",
            "endpoint": "GET /api/v3/klines",
            "raw_signal_interval": "15m",
            "regime_interval": "1d",
            "start_utc": START_UTC,
            "seed_end_exclusive_utc": SEED_END_UTC,
            "outcome_evaluation_performed": False,
            "orders_created": False,
            "authenticated_api_used": False,
        },
        "freeze": {
            "forward_freeze_commit": "b2325b97bbc8090e9702526a6abdaa5c830bba10",
            "watcher_spec_commit": "3539b56cb2c57f5e910aaaaf67b59f13172120a6",
            "donchian_lookback": DONCHIAN_LOOKBACK,
            "atr_length": ATR_LENGTH,
            "target_r": 3.0,
            "max_hold_12h_bars": 80,
            "base_round_trip_cost_pct": 0.20,
            "stress_round_trip_cost_pct": 0.30,
        },
        "symbols": {},
    }

    for symbol in SYMBOLS:
        print(f"SEED_SOURCE_START {symbol}", flush=True)
        raw15 = fetch_range(symbol, "15m", start, seed_end, FIFTEEN_MS)
        bars12 = aggregate_12h(raw15)
        atr = atr_series(bars12, ATR_LENGTH)
        if atr[-1] is None or len(bars12) < DONCHIAN_LOOKBACK + 1:
            raise RuntimeError(f"ATR_OR_DONCHIAN_WARMUP_FAIL:{symbol}")

        # Daily seed stores exactly the last 220 fully closed daily observations
        # available strictly before seed_end. We fetch from the same source start
        # and retain the tail only after proving continuity.
        daily_end = seed_end - (seed_end % DAY_MS)
        daily = fetch_range(symbol, "1d", start, daily_end, DAY_MS)
        if len(daily) < DAILY_HISTORY:
            raise RuntimeError(f"DAILY_WARMUP_FAIL:{symbol}:{len(daily)}")
        daily_tail = daily[-DAILY_HISTORY:]

        symbol_seed = {
            "last_complete_12h_open_time_ms": bars12[-1].open_time,
            "last_complete_12h_close_exclusive_ms": bars12[-1].open_time + TWELVE_H_MS,
            "last_atr28": float(atr[-1]),
            "previous_12h_close": bars12[-1].close,
            "last_40_complete_12h": [asdict(x) for x in bars12[-DONCHIAN_LOOKBACK:]],
            "last_220_complete_daily": [asdict(x) for x in daily_tail],
            "counts": {
                "raw_15m": len(raw15),
                "derived_12h": len(bars12),
                "daily": len(daily),
            },
        }
        symbol_seed["sha256"] = canonical_hash(symbol_seed)
        result["symbols"][symbol] = symbol_seed
        print(f"SEED_SOURCE_PASS {symbol} 15m={len(raw15)} 12h={len(bars12)} daily={len(daily)}", flush=True)

    result["seed_sha256"] = canonical_hash(result)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "seed_sha256": result["seed_sha256"], "path": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
