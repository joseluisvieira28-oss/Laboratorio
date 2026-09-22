from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import json
from math import isfinite, log
from statistics import median, stdev
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DERIBIT_BASE_URL = "https://www.deribit.com"
DERIBIT_TRADES_PATH = "/api/v2/public/get_last_trades_by_currency_and_time"
BINANCE_DATA_BASE_URL = "https://data-api.binance.vision"
BINANCE_KLINES_PATH = "/api/v3/klines"

FREEZE_UTC = "2026-09-18T05:35:01Z"
FREEZE_MS = int(datetime.fromisoformat(FREEZE_UTC.replace("Z", "+00:00")).timestamp() * 1000)
FIRST_FULL_POST_FREEZE_SIGNAL_DAY = date(2026, 9, 19)
HISTORICAL_STATE_START = date(2021, 4, 1)

MIN_DTE = 30
MAX_DTE = 120
CALL_MIN = 1.05
CALL_MAX = 1.20
PUT_MIN = 0.80
PUT_MAX = 0.95
MIN_SIDE = 5
RV_WINDOW = 20
MIN_RV_HISTORY = 60
DAY_MS = 86_400_000
MAX_TRADES_PER_REQUEST = 1000


class OptionsV21SourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class OptionTrade:
    trade_id: str
    timestamp: int
    instrument_name: str
    iv: float
    index_price: float


@dataclass(frozen=True)
class DailyBar:
    open_time: int
    open: float
    close: float


def _utc_day_bounds(day: date) -> tuple[int, int]:
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    start_ms = int(start.timestamp() * 1000)
    return start_ms, start_ms + DAY_MS - 1


def _parse_instrument(name: str) -> tuple[date, float, str]:
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"C", "P"}:
        raise OptionsV21SourceError(f"invalid BTC option instrument: {name}")
    try:
        expiry = datetime.strptime(parts[1].upper(), "%d%b%y").date()
        strike = float(parts[2])
    except Exception as exc:
        raise OptionsV21SourceError(f"invalid BTC option instrument: {name}") from exc
    if not isfinite(strike) or strike <= 0:
        raise OptionsV21SourceError(f"invalid strike: {name}")
    return expiry, strike, parts[3]


def _parse_trade(row: Any, *, start_ms: int, end_ms: int) -> OptionTrade:
    if not isinstance(row, dict):
        raise OptionsV21SourceError("Deribit trade row is not an object")
    required = ("timestamp", "instrument_name", "iv", "index_price")
    if any(k not in row for k in required):
        raise OptionsV21SourceError("Deribit trade row missing frozen signal field")
    try:
        ts = int(row["timestamp"])
        iv = float(row["iv"])
        index_price = float(row["index_price"])
    except (TypeError, ValueError) as exc:
        raise OptionsV21SourceError("Deribit trade row has invalid numeric field") from exc
    if not start_ms <= ts <= end_ms:
        raise OptionsV21SourceError("Deribit returned trade outside requested time window")
    if not isfinite(iv) or iv <= 0 or not isfinite(index_price) or index_price <= 0:
        raise OptionsV21SourceError(
            "Deribit trade has invalid IV/index "
            f"(trade_id={row.get('trade_id')!r}, instrument={row.get('instrument_name')!r}, "
            f"iv={row.get('iv')!r}, index_price={row.get('index_price')!r})"
        )
    trade_id = str(row.get("trade_id") or "")
    if not trade_id:
        # Fail closed rather than deduplicating with a guessed identity.
        raise OptionsV21SourceError("Deribit trade missing trade_id")
    name = str(row["instrument_name"])
    _parse_instrument(name)
    return OptionTrade(trade_id, ts, name, iv, index_price)


class DeribitBTCOptionTradeFeed:
    provider = "DERIBIT_PUBLIC_HTTP"
    base_url = DERIBIT_BASE_URL
    path = DERIBIT_TRADES_PATH

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def _get_json(self, query: dict[str, Any]) -> Any:
        url = f"{self.base_url}{self.path}?{urlencode(query)}"
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.9 options-v21-public-read-only"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise OptionsV21SourceError(f"Deribit HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, OptionsV21SourceError):
                raise
            raise OptionsV21SourceError(
                f"Deribit public source unavailable: {type(exc).__name__}: {exc}"
            ) from exc

    def _one_window(self, start_ms: int, end_ms: int) -> tuple[list[OptionTrade], bool]:
        payload = self._get_json(
            {
                "currency": "BTC",
                "kind": "option",
                "start_timestamp": start_ms,
                "end_timestamp": end_ms,
                "count": MAX_TRADES_PER_REQUEST,
                "sorting": "asc",
            }
        )
        if not isinstance(payload, dict) or "result" not in payload:
            raise OptionsV21SourceError("Deribit payload missing result")
        result = payload["result"]
        if not isinstance(result, dict):
            raise OptionsV21SourceError("Deribit result is not an object")
        rows = result.get("trades")
        if not isinstance(rows, list):
            raise OptionsV21SourceError("Deribit result missing trades")
        trades = [_parse_trade(row, start_ms=start_ms, end_ms=end_ms) for row in rows]
        return trades, bool(result.get("has_more", False)) or len(rows) >= MAX_TRADES_PER_REQUEST

    def trades(self, *, start_ms: int, end_ms: int) -> list[OptionTrade]:
        if start_ms < 0 or end_ms < start_ms:
            raise OptionsV21SourceError("invalid Deribit time range")

        def collect(lo: int, hi: int) -> list[OptionTrade]:
            rows, saturated = self._one_window(lo, hi)
            if not saturated:
                return rows
            if lo == hi:
                raise OptionsV21SourceError("Deribit source saturated within one millisecond")
            mid = lo + (hi - lo) // 2
            return collect(lo, mid) + collect(mid + 1, hi)

        rows = collect(start_ms, end_ms)
        by_id: dict[str, OptionTrade] = {}
        for row in rows:
            existing = by_id.get(row.trade_id)
            if existing is not None and existing != row:
                raise OptionsV21SourceError("Deribit trade_id collision with different payload")
            by_id[row.trade_id] = row
        out = sorted(by_id.values(), key=lambda x: (x.timestamp, x.trade_id))
        return out


def build_daily_skew(day: date, trades: list[OptionTrade]) -> dict[str, Any]:
    call_by_inst: dict[str, list[float]] = {}
    put_by_inst: dict[str, list[float]] = {}
    eligible_rows = 0
    rejected_dte = 0
    rejected_moneyness = 0

    for row in trades:
        trade_day = datetime.fromtimestamp(row.timestamp / 1000, tz=timezone.utc).date()
        if trade_day != day:
            raise OptionsV21SourceError("trade belongs to a different UTC day")
        expiry, strike, side = _parse_instrument(row.instrument_name)
        dte = (expiry - day).days
        if not MIN_DTE <= dte <= MAX_DTE:
            rejected_dte += 1
            continue
        moneyness = strike / row.index_price
        eligible = (
            side == "C" and CALL_MIN <= moneyness <= CALL_MAX
        ) or (
            side == "P" and PUT_MIN <= moneyness <= PUT_MAX
        )
        if not eligible:
            rejected_moneyness += 1
            continue
        target = call_by_inst if side == "C" else put_by_inst
        target.setdefault(row.instrument_name, []).append(row.iv)
        eligible_rows += 1

    calls = [float(median(values)) for values in call_by_inst.values()]
    puts = [float(median(values)) for values in put_by_inst.values()]
    valid = len(calls) >= MIN_SIDE and len(puts) >= MIN_SIDE
    skew = float(median(calls) - median(puts)) if valid else None
    position = 1 if skew is not None and skew > 0 else (-1 if skew is not None and skew < 0 else 0)

    return {
        "signal_date": day.isoformat(),
        "valid": valid,
        "distinct_eligible_calls": len(calls),
        "distinct_eligible_puts": len(puts),
        "eligible_trade_rows": eligible_rows,
        "rejected_dte": rejected_dte,
        "rejected_moneyness": rejected_moneyness,
        "skew": skew,
        "position": position,
    }


class BinanceBTCUSDTDailyFeed:
    provider = "BINANCE_SPOT_DATA_API_PUBLIC"
    base_url = BINANCE_DATA_BASE_URL
    path = BINANCE_KLINES_PATH

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def _get_json(self, query: dict[str, Any]) -> Any:
        url = f"{self.base_url}{self.path}?{urlencode(query)}"
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.9 options-v21-btc-state-read-only"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise OptionsV21SourceError(f"Binance HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, OptionsV21SourceError):
                raise
            raise OptionsV21SourceError(
                f"Binance BTCUSDT public source unavailable: {type(exc).__name__}: {exc}"
            ) from exc

    def daily(self, *, start_day: date, end_day_exclusive: date) -> list[DailyBar]:
        if end_day_exclusive <= start_day:
            raise OptionsV21SourceError("invalid BTC daily range")
        start_ms, _ = _utc_day_bounds(start_day)
        end_ms, _ = _utc_day_bounds(end_day_exclusive)
        cursor = start_ms
        rows: dict[int, DailyBar] = {}
        while cursor < end_ms:
            payload = self._get_json(
                {
                    "symbol": "BTCUSDT",
                    "interval": "1d",
                    "startTime": cursor,
                    "endTime": end_ms - 1,
                    "limit": 1000,
                }
            )
            if not isinstance(payload, list):
                raise OptionsV21SourceError("Binance BTC daily payload is not a list")
            if not payload:
                break
            parsed: list[DailyBar] = []
            for row in payload:
                if not isinstance(row, list) or len(row) < 7:
                    raise OptionsV21SourceError("invalid Binance BTC daily row")
                open_ms = int(row[0])
                close_ms = int(row[6])
                op = float(row[1])
                cl = float(row[4])
                if open_ms % DAY_MS != 0 or close_ms != open_ms + DAY_MS - 1:
                    raise OptionsV21SourceError("BTC daily timestamp alignment violation")
                if not all(isfinite(x) and x > 0 for x in (op, cl)):
                    raise OptionsV21SourceError("invalid BTC daily OHLC")
                parsed.append(DailyBar(open_ms, op, cl))
            for row in parsed:
                if start_ms <= row.open_time < end_ms:
                    rows[row.open_time] = row
            last_open = max(x.open_time for x in parsed)
            next_cursor = last_open + DAY_MS
            if next_cursor <= cursor:
                raise OptionsV21SourceError("Binance BTC daily pagination did not advance")
            cursor = next_cursor

        out = [rows[k] for k in sorted(rows)]
        expected = list(range(start_ms, end_ms, DAY_MS))
        got = [x.open_time for x in out]
        if got != expected:
            missing = [x for x in expected if x not in rows]
            raise OptionsV21SourceError(f"BTC daily continuity failure: missing={missing[:10]}")
        return out


def rv20_and_weight(bars: list[DailyBar], *, signal_day: date) -> dict[str, float]:
    by_day = {
        datetime.fromtimestamp(x.open_time / 1000, tz=timezone.utc).date(): x
        for x in bars
    }
    days = sorted(by_day)
    if signal_day not in by_day:
        raise OptionsV21SourceError("BTC signal-day close unavailable")
    rets: list[tuple[date, float]] = []
    for i in range(1, len(days)):
        if days[i] - days[i - 1] != timedelta(days=1):
            raise OptionsV21SourceError("BTC daily continuity failure")
        rets.append((days[i], log(by_day[days[i]].close / by_day[days[i - 1]].close)))

    rv: dict[date, float] = {}
    for i in range(RV_WINDOW - 1, len(rets)):
        sample = [rets[j][1] for j in range(i - RV_WINDOW + 1, i + 1)]
        value = stdev(sample)
        if not isfinite(value) or value <= 0:
            raise OptionsV21SourceError("invalid RV20")
        rv[rets[i][0]] = float(value)

    history: list[float] = []
    weights: dict[date, tuple[float, float]] = {}
    for day in sorted(rv):
        x = rv[day]
        history.append(x)
        if len(history) < MIN_RV_HISTORY:
            continue
        baseline = float(median(history))
        weight = min(1.0, baseline / x)
        if not isfinite(weight) or not 0 < weight <= 1:
            raise OptionsV21SourceError("invalid V2.1 causal weight")
        weights[day] = (baseline, weight)

    if signal_day not in weights:
        raise OptionsV21SourceError("insufficient RV20 expanding history for signal day")
    baseline, weight = weights[signal_day]
    return {
        "rv20": rv[signal_day],
        "expanding_median_rv20": baseline,
        "weight": weight,
        "valid_rv20_history_count": len([d for d in rv if d <= signal_day]),
    }


def source_schema_probe(feed: DeribitBTCOptionTradeFeed, *, start_ms: int, end_ms: int) -> dict[str, Any]:
    if start_ms < FREEZE_MS:
        raise OptionsV21SourceError("probe may not access pre-freeze 2026 option trades")
    rows = feed.trades(start_ms=start_ms, end_ms=end_ms)
    return {
        "status": "PASS_SOURCE_SCHEMA" if rows else "PASS_SOURCE_EMPTY_WINDOW",
        "provider": feed.provider,
        "endpoint": feed.path,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "trade_count": len(rows),
        "required_fields_validated": ["timestamp", "instrument_name", "iv", "index_price", "trade_id"],
        "used_as_forward_evidence": False,
        "authenticated_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
    }


def _day_open_ms(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp() * 1000)


def latest_complete_signal_day(now_ms: int) -> date | None:
    now = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc)
    candidate = now.date() - timedelta(days=1)
    return candidate if candidate >= FIRST_FULL_POST_FREEZE_SIGNAL_DAY else None


def exact_daily_open_if_available(
    feed: BinanceBTCUSDTDailyFeed,
    *,
    day: date,
    now_ms: int,
) -> float | None:
    target_ms = _day_open_ms(day)
    if now_ms < target_ms:
        return None
    payload = feed._get_json(
        {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "startTime": target_ms,
            "endTime": target_ms + DAY_MS - 1,
            "limit": 2,
        }
    )
    if not isinstance(payload, list) or not payload:
        return None
    row = payload[0]
    if not isinstance(row, list) or len(row) < 2 or int(row[0]) != target_ms:
        raise OptionsV21SourceError("BTC exact daily open binding mismatch")
    value = float(row[1])
    if not isfinite(value) or value <= 0:
        raise OptionsV21SourceError("invalid BTC exact daily open")
    return value
