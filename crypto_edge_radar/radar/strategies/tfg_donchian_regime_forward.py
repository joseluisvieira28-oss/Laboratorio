from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from math import isfinite
from statistics import mean
from typing import Any, Iterable
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MEXC_SPOT_BASE_URL = "https://api.mexc.com"
FROZEN_UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
FIFTEEN_MIN_MS = 900_000
TWELVE_HOUR_MS = 43_200_000
DAY_MS = 86_400_000
LOOKBACK = 40
ATR_LENGTH = 28
STOP_ATR_FRACTION = 0.25
TARGET_R = 3.0
MAX_HOLD_BARS = 80
BASE_COST_PCT = 0.20
STRESS_COST_PCT = 0.30
FORWARD_FREEZE_UTC = "2026-09-16T15:16:53Z"
FORWARD_FREEZE_MS = int(
    datetime.fromisoformat(FORWARD_FREEZE_UTC.replace("Z", "+00:00"))
    .astimezone(timezone.utc)
    .timestamp() * 1000
)


class TFGSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


@dataclass(frozen=True)
class SignalCandidate:
    symbol: str
    signal_close_ms: int
    signal_open_ms: int
    prior_40_high: float
    atr28: float
    signal_low: float
    signal_close: float
    stop: float


@dataclass(frozen=True)
class PaperTrade:
    symbol: str
    signal_close_ms: int
    entry_open_time: int
    entry: float
    stop: float
    target: float
    initial_risk_fraction: float


@dataclass(frozen=True)
class PaperOutcome:
    exit_reason: str
    exit_open_time: int | None
    exit_price: float | None
    bars_held: int | None
    gross_return_pct: float | None
    base_net_r: float | None
    stress_net_r: float | None
    same_bar_stop_target_ambiguity: bool


def utc_iso_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_symbol(symbol: str) -> str:
    s = symbol.upper()
    if s not in FROZEN_UNIVERSE:
        raise TFGSourceError(f"symbol outside frozen TFG universe: {symbol}")
    return s


def _duration_ms(interval: str) -> int:
    if interval == "15m":
        return FIFTEEN_MIN_MS
    if interval == "1d":
        return DAY_MS
    raise TFGSourceError(f"interval not frozen/allowed: {interval}")


def _parse_kline(row: Any, interval: str) -> Candle:
    if not isinstance(row, list) or len(row) < 7:
        raise TFGSourceError("invalid MEXC spot kline row")
    try:
        c = Candle(
            open_time=int(row[0]),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
            close_time=int(row[6]),
        )
    except (TypeError, ValueError) as exc:
        raise TFGSourceError("invalid MEXC spot kline values") from exc
    step = _duration_ms(interval)
    # MEXC Spot V3 reports closeTime at the next interval boundary (open + step),
    # unlike Binance's common inclusive end timestamp (open + step - 1). Validate
    # the provider-native timestamp strictly, then normalize internally to the
    # inclusive-end convention used by the frozen TFG mechanics.
    if c.open_time % step != 0 or c.close_time != c.open_time + step:
        raise TFGSourceError("MEXC spot kline timestamp/alignment violation")
    c = Candle(
        open_time=c.open_time,
        open=c.open,
        high=c.high,
        low=c.low,
        close=c.close,
        volume=c.volume,
        close_time=c.open_time + step - 1,
    )
    vals = (c.open, c.high, c.low, c.close, c.volume)
    if any(not isfinite(v) for v in vals):
        raise TFGSourceError("non-finite MEXC kline value")
    if min(c.open, c.high, c.low, c.close) <= 0 or c.volume < 0:
        raise TFGSourceError("invalid non-positive MEXC OHLC/negative volume")
    if c.high < max(c.open, c.close, c.low) or c.low > min(c.open, c.close, c.high):
        raise TFGSourceError("MEXC OHLC ordering violation")
    return c


class MEXCSpotKlineFeed:
    """Public GET-only MEXC Spot klines bound to the frozen TFG watcher."""

    base_url = MEXC_SPOT_BASE_URL
    provider = "MEXC_SPOT_PUBLIC"
    path = "/api/v3/klines"

    def __init__(
        self,
        timeout: int = 10,
        *,
        max_attempts: int = 3,
        retry_backoff_seconds: float = 0.5,
    ) -> None:
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.retry_backoff_seconds = retry_backoff_seconds
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds must be >= 0")

    def _get_json(self, query: dict[str, Any]) -> Any:
        url = f"{self.base_url}{self.path}?{urlencode(query)}"
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.9 tfg-forward-read-only"},
        )
        last_exc: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    if response.status != 200:
                        raise TFGSourceError(f"MEXC spot HTTP {response.status}")
                    return json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                if isinstance(exc, TFGSourceError):
                    raise
                last_exc = exc
                if attempt < self.max_attempts and self.retry_backoff_seconds:
                    time.sleep(self.retry_backoff_seconds * attempt)
        assert last_exc is not None
        raise TFGSourceError(
            f"MEXC spot source unavailable after {self.max_attempts} attempts: "
            f"{type(last_exc).__name__}: {last_exc}"
        ) from last_exc

    def klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int,
        end_ms: int,
        now_ms: int,
    ) -> list[Candle]:
        symbol = _validate_symbol(symbol)
        step = _duration_ms(interval)
        if start_ms >= end_ms:
            raise TFGSourceError("invalid kline time range")
        cursor = start_ms - (start_ms % step)
        end_exclusive = end_ms - (end_ms % step)
        if end_exclusive <= cursor:
            return []

        rows: dict[int, Candle] = {}
        while cursor < end_exclusive:
            payload = self._get_json(
                {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": cursor,
                    "endTime": end_exclusive - 1,
                    "limit": 1000,
                }
            )
            if not isinstance(payload, list):
                raise TFGSourceError("MEXC spot kline payload is not a list")
            if not payload:
                break
            parsed = [_parse_kline(row, interval) for row in payload]
            for c in parsed:
                if start_ms <= c.open_time < end_exclusive and c.close_time < now_ms:
                    rows[c.open_time] = c
            last_open = max(c.open_time for c in parsed)
            next_cursor = last_open + step
            if next_cursor <= cursor:
                raise TFGSourceError("MEXC spot pagination did not advance")
            cursor = next_cursor
        return [rows[t] for t in sorted(rows)]


def validate_regular(candles: Iterable[Candle], step_ms: int) -> list[Candle]:
    rows = sorted(candles, key=lambda c: c.open_time)
    for i, c in enumerate(rows):
        if c.open_time % step_ms != 0 or c.close_time != c.open_time + step_ms - 1:
            raise TFGSourceError("candle alignment violation")
        if i and c.open_time - rows[i - 1].open_time != step_ms:
            raise TFGSourceError("candle gap")
    return rows


def aggregate_15m_to_12h(candles: Iterable[Candle]) -> tuple[list[Candle], int]:
    rows = sorted(candles, key=lambda c: c.open_time)
    buckets: dict[int, list[Candle]] = {}
    for c in rows:
        if c.open_time % FIFTEEN_MIN_MS != 0 or c.close_time != c.open_time + FIFTEEN_MIN_MS - 1:
            raise TFGSourceError("15m source alignment violation")
        bucket = c.open_time - (c.open_time % TWELVE_HOUR_MS)
        buckets.setdefault(bucket, []).append(c)

    out: list[Candle] = []
    incomplete = 0
    for bucket in sorted(buckets):
        items = sorted(buckets[bucket], key=lambda c: c.open_time)
        expected = [bucket + i * FIFTEEN_MIN_MS for i in range(48)]
        if len(items) != 48 or [c.open_time for c in items] != expected:
            incomplete += 1
            continue
        out.append(
            Candle(
                open_time=bucket,
                open=items[0].open,
                high=max(c.high for c in items),
                low=min(c.low for c in items),
                close=items[-1].close,
                volume=sum(c.volume for c in items),
                close_time=bucket + TWELVE_HOUR_MS - 1,
            )
        )
    return out, incomplete


def atr_series(candles: list[Candle], length: int) -> list[float | None]:
    """Exact family ATR: omit first TR, SMA seed, then Wilder RMA."""
    out: list[float | None] = [None] * len(candles)
    if len(candles) <= length:
        return out
    trs: list[float | None] = [None]
    for i in range(1, len(candles)):
        c, p = candles[i], candles[i - 1]
        trs.append(max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)))
    seed_values = [float(x) for x in trs[1 : length + 1] if x is not None]
    if len(seed_values) != length:
        return out
    value = mean(seed_values)
    out[length] = value
    for i in range(length + 1, len(candles)):
        tr = float(trs[i])
        value = ((value * (length - 1)) + tr) / length
        out[i] = value
    return out


def regime_state(
    daily_by_symbol: dict[str, list[Candle]],
    *,
    signal_close_ms: int,
) -> dict[str, Any]:
    required: dict[str, list[Candle]] = {}
    for symbol in FROZEN_UNIVERSE:
        rows = [c for c in daily_by_symbol.get(symbol, []) if c.close_time < signal_close_ms]
        if len(rows) < 220:
            return {"state": "MISSING", "reason": f"insufficient_daily_history:{symbol}"}
        tail = rows[-220:]
        try:
            validate_regular(tail, DAY_MS)
        except TFGSourceError:
            return {"state": "MISSING", "reason": f"daily_gap:{symbol}"}
        required[symbol] = tail

    btc = required["BTCUSDT"]
    btc_close = btc[-1].close
    btc_sma200 = mean(c.close for c in btc[-200:])
    btc_sma200_20d_ago = mean(c.close for c in btc[-220:-20])
    breadth = 0
    per_asset: dict[str, bool] = {}
    for symbol in FROZEN_UNIVERSE:
        rows = required[symbol]
        own_sma100 = mean(c.close for c in rows[-100:])
        above = rows[-1].close > own_sma100
        per_asset[symbol] = above
        breadth += int(above)

    checks = {
        "btc_close_gt_sma200": btc_close > btc_sma200,
        "btc_sma200_rising_20d": btc_sma200 > btc_sma200_20d_ago,
        "breadth_ge_4_of_6": breadth >= 4,
    }
    return {
        "state": "ON" if all(checks.values()) else "OFF",
        "checks": checks,
        "breadth_count": breadth,
        "asset_above_sma100": per_asset,
        "btc_close": btc_close,
        "btc_sma200": btc_sma200,
        "btc_sma200_20d_ago": btc_sma200_20d_ago,
        "snapshot_daily_open_ms": btc[-1].open_time,
    }


def detect_signal(
    symbol: str,
    bars_12h: list[Candle],
    *,
    signal_close_ms: int,
) -> SignalCandidate | None:
    symbol = _validate_symbol(symbol)
    rows = validate_regular(bars_12h, TWELVE_HOUR_MS)
    idx = next(
        (i for i, c in enumerate(rows) if c.open_time + TWELVE_HOUR_MS == signal_close_ms),
        None,
    )
    if idx is None:
        raise TFGSourceError("required 12H signal bar unavailable")
    if signal_close_ms <= FORWARD_FREEZE_MS:
        return None
    if idx < max(LOOKBACK, ATR_LENGTH):
        raise TFGSourceError("insufficient 12H warmup")
    atr28 = atr_series(rows, ATR_LENGTH)
    if atr28[idx] is None:
        raise TFGSourceError("ATR28 unavailable")
    signal = rows[idx]
    prior_high = max(c.high for c in rows[idx - LOOKBACK : idx])
    if not signal.close > prior_high:
        return None
    stop = signal.low - STOP_ATR_FRACTION * float(atr28[idx])
    if stop <= 0:
        return None
    return SignalCandidate(
        symbol=symbol,
        signal_close_ms=signal_close_ms,
        signal_open_ms=signal.open_time,
        prior_40_high=prior_high,
        atr28=float(atr28[idx]),
        signal_low=signal.low,
        signal_close=signal.close,
        stop=stop,
    )


def materialize_entry(candidate: SignalCandidate, source_15m: list[Candle]) -> PaperTrade | None:
    entry_bar = next((c for c in source_15m if c.open_time == candidate.signal_close_ms), None)
    if entry_bar is None:
        return None
    entry = entry_bar.open
    if entry <= candidate.stop:
        return None
    risk = (entry - candidate.stop) / entry
    if risk <= 0 or not isfinite(risk):
        return None
    target = entry + TARGET_R * (entry - candidate.stop)
    return PaperTrade(
        symbol=candidate.symbol,
        signal_close_ms=candidate.signal_close_ms,
        entry_open_time=candidate.signal_close_ms,
        entry=entry,
        stop=candidate.stop,
        target=target,
        initial_risk_fraction=risk,
    )


def _net_r(entry: float, price: float, risk: float, cost_pct: float) -> tuple[float, float]:
    gross = (price - entry) / entry
    cost_fraction = cost_pct / 100.0
    denom = risk + cost_fraction
    return gross * 100.0, (gross - cost_fraction) / denom


def resolve_paper_trade(trade: PaperTrade, bars_12h: list[Candle]) -> PaperOutcome:
    rows = validate_regular(bars_12h, TWELVE_HOUR_MS)
    entry_idx = next((i for i, c in enumerate(rows) if c.open_time == trade.entry_open_time), None)
    if entry_idx is None:
        return PaperOutcome("UNRESOLVED_ENTRY_BAR_MISSING", None, None, None, None, None, None, False)
    if abs(rows[entry_idx].open - trade.entry) > max(1e-12, abs(trade.entry) * 1e-12):
        raise TFGSourceError("paper trade entry price mismatch")

    def finish(reason: str, c: Candle, price: float, bars: int, ambiguity: bool) -> PaperOutcome:
        gross_pct, base_r = _net_r(trade.entry, price, trade.initial_risk_fraction, BASE_COST_PCT)
        _, stress_r = _net_r(trade.entry, price, trade.initial_risk_fraction, STRESS_COST_PCT)
        return PaperOutcome(reason, c.open_time, price, bars, gross_pct, base_r, stress_r, ambiguity)

    last_idx = min(len(rows) - 1, entry_idx + MAX_HOLD_BARS - 1)
    for i in range(entry_idx, last_idx + 1):
        c = rows[i]
        bars = i - entry_idx + 1
        if c.open <= trade.stop:
            return finish("STOP_GAP", c, c.open, bars, False)
        if c.open >= trade.target:
            return finish("TARGET", c, trade.target, bars, False)
        stop_hit = c.low <= trade.stop
        target_hit = c.high >= trade.target
        if stop_hit and target_hit:
            return finish("STOP_AMBIGUOUS_SAME_BAR", c, trade.stop, bars, True)
        if stop_hit:
            return finish("STOP", c, trade.stop, bars, False)
        if target_hit:
            return finish("TARGET", c, trade.target, bars, False)

    exit_idx = entry_idx + MAX_HOLD_BARS
    if exit_idx >= len(rows):
        return PaperOutcome("UNRESOLVED_END_OF_DATA", None, None, None, None, None, None, False)
    c = rows[exit_idx]
    return finish("TIME_EXIT_NEXT_OPEN", c, c.open, MAX_HOLD_BARS, False)


def latest_due_signal_close_ms(now_ms: int) -> int | None:
    boundary = now_ms - (now_ms % TWELVE_HOUR_MS)
    if now_ms < boundary + 10 * 60_000:
        boundary -= TWELVE_HOUR_MS
    return boundary if boundary > FORWARD_FREEZE_MS else None


def source_probe(feed: MEXCSpotKlineFeed, *, now_ms: int) -> dict[str, Any]:
    due = latest_due_signal_close_ms(now_ms)
    if due is None:
        return {"status": "WAITING_POST_FREEZE_BOUNDARY", "provider": feed.provider}
    start_15m = due - 25 * DAY_MS
    start_1d = due - 240 * DAY_MS
    coverage: dict[str, Any] = {}
    for symbol in FROZEN_UNIVERSE:
        m15 = feed.klines(symbol, "15m", start_ms=start_15m, end_ms=due + FIFTEEN_MIN_MS, now_ms=now_ms)
        d1 = feed.klines(symbol, "1d", start_ms=start_1d, end_ms=due, now_ms=now_ms)
        h12, incomplete = aggregate_15m_to_12h(m15)
        coverage[symbol] = {
            "15m_rows": len(m15),
            "12h_complete_rows": len(h12),
            "12h_incomplete_buckets": incomplete,
            "1d_rows": len(d1),
        }
    return {
        "status": "PASS_SOURCE_ONLY",
        "provider": feed.provider,
        "market": "SPOT",
        "endpoint": feed.path,
        "signal_close_utc": utc_iso_from_ms(due),
        "coverage": coverage,
        "authenticated_exchange_api_used": False,
        "order_created": False,
        "exchange_mutation_performed": False,
    }
