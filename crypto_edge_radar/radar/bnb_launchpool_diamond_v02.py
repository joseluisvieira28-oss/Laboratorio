from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from math import isfinite
from statistics import median
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .evidence import EvidenceStore, PostgresEvidenceStore

Store = EvidenceStore | PostgresEvidenceStore

BASE_URL = "https://data-api.binance.vision"
KLINE_PATH = "/api/v3/klines"
ONE_MINUTE_MS = 60_000
WINDOW_MINUTES = 60
BASELINE_VALID_DAYS = 20
BASELINE_MAX_LOOKBACK_DAYS = 40
DIAMOND_TARGET_EVENTS = 25
POSITIVE_EVENT_MINIMUM = 17
MAX_SINGLE_POSITIVE_SHARE = 0.40

MEASUREMENT_EVENT = "BNB_DIAMOND_CAUSAL_MEASUREMENT_V02"
BLOCKED_EVENT = "BNB_DIAMOND_CAUSAL_BLOCKED_V02"


class BNBDiamondMeasurementError(RuntimeError):
    pass


@dataclass(frozen=True)
class MinuteBar:
    open_time: int
    open: float
    close: float
    quote_volume: float
    close_time: int


def first_minute_open_strictly_after(signal_timestamp_ms: int) -> int:
    if signal_timestamp_ms <= 0:
        raise ValueError("signal timestamp must be positive")
    return (signal_timestamp_ms // ONE_MINUTE_MS + 1) * ONE_MINUTE_MS


def _parse_row(row: Any) -> MinuteBar:
    if not isinstance(row, list) or len(row) < 8:
        raise BNBDiamondMeasurementError("invalid Binance 1m kline row")
    try:
        bar = MinuteBar(
            open_time=int(row[0]),
            open=float(row[1]),
            close=float(row[4]),
            quote_volume=float(row[7]),
            close_time=int(row[6]),
        )
    except (TypeError, ValueError) as exc:
        raise BNBDiamondMeasurementError("invalid Binance 1m kline values") from exc
    if bar.open_time % ONE_MINUTE_MS != 0:
        raise BNBDiamondMeasurementError("1m open timestamp not UTC aligned")
    if bar.close_time != bar.open_time + ONE_MINUTE_MS - 1:
        raise BNBDiamondMeasurementError("1m close timestamp mismatch")
    if not all(isfinite(x) for x in (bar.open, bar.close, bar.quote_volume)):
        raise BNBDiamondMeasurementError("non-finite 1m kline value")
    if bar.open <= 0 or bar.close <= 0 or bar.quote_volume < 0:
        raise BNBDiamondMeasurementError("invalid 1m price/quote volume")
    return bar


class BinancePublicMinuteFeed:
    provider = "BINANCE_SPOT_DATA_API_PUBLIC"
    base_url = BASE_URL
    path = KLINE_PATH

    def __init__(self, *, timeout: int = 10) -> None:
        self.timeout = int(timeout)

    def _get_json(self, query: dict[str, Any]) -> Any:
        url = f"{self.base_url}{self.path}?{urlencode(query)}"
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.9 bnb-diamond-read-only"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise BNBDiamondMeasurementError(
                        f"Binance 1m HTTP {response.status}"
                    )
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, BNBDiamondMeasurementError):
                raise
            raise BNBDiamondMeasurementError(
                f"Binance 1m source unavailable:{type(exc).__name__}:{exc}"
            ) from exc

    def exact_window(
        self,
        *,
        symbol: str,
        start_ms: int,
        minutes: int,
        now_ms: int,
    ) -> list[MinuteBar]:
        if minutes < 1 or minutes > 1000:
            raise BNBDiamondMeasurementError("invalid 1m window length")
        end_ms = start_ms + minutes * ONE_MINUTE_MS
        if now_ms <= end_ms:
            raise BNBDiamondMeasurementError("WINDOW_NOT_FULLY_AVAILABLE")
        payload = self._get_json(
            {
                "symbol": symbol,
                "interval": "1m",
                "startTime": start_ms,
                "endTime": end_ms - 1,
                "limit": minutes,
            }
        )
        if not isinstance(payload, list):
            raise BNBDiamondMeasurementError("Binance 1m payload is not a list")
        rows = [_parse_row(x) for x in payload]
        by_open = {x.open_time: x for x in rows}
        expected = [start_ms + i * ONE_MINUTE_MS for i in range(minutes)]
        if sorted(by_open) != expected:
            missing = [x for x in expected if x not in by_open]
            raise BNBDiamondMeasurementError(
                f"INCOMPLETE_1M_WINDOW:{symbol}:missing={len(missing)}"
            )
        return [by_open[x] for x in expected]


def _simple_return(rows: list[MinuteBar], minutes: int) -> float:
    if len(rows) < minutes:
        raise BNBDiamondMeasurementError("insufficient return rows")
    return rows[minutes - 1].close / rows[0].open - 1.0


def _quote_volume(rows: list[MinuteBar]) -> float:
    return float(sum(x.quote_volume for x in rows))


def _same_clock_start(event_start_ms: int, days_back: int) -> int:
    dt = datetime.fromtimestamp(event_start_ms / 1000, tz=timezone.utc)
    prior = dt - timedelta(days=days_back)
    return int(prior.timestamp() * 1000)


def prior_same_clock_volume_baseline(
    feed: BinancePublicMinuteFeed,
    *,
    event_start_ms: int,
    now_ms: int,
) -> tuple[float, list[str]]:
    values: list[float] = []
    dates: list[str] = []
    for days_back in range(1, BASELINE_MAX_LOOKBACK_DAYS + 1):
        start = _same_clock_start(event_start_ms, days_back)
        try:
            rows = feed.exact_window(
                symbol="BNBUSDT",
                start_ms=start,
                minutes=WINDOW_MINUTES,
                now_ms=now_ms,
            )
        except BNBDiamondMeasurementError as exc:
            if str(exc).startswith("INCOMPLETE_1M_WINDOW"):
                continue
            raise
        values.append(_quote_volume(rows))
        dates.append(
            datetime.fromtimestamp(start / 1000, tz=timezone.utc).date().isoformat()
        )
        if len(values) == BASELINE_VALID_DAYS:
            break
    if len(values) != BASELINE_VALID_DAYS:
        raise BNBDiamondMeasurementError(
            "MECHANISM_DATA_BLOCKED_FEWER_THAN_20_VALID_BASELINE_DAYS"
        )
    baseline = float(median(values))
    if not isfinite(baseline) or baseline <= 0:
        raise BNBDiamondMeasurementError("INVALID_VOLUME_BASELINE")
    return baseline, dates


def measure_causal_event(
    feed: BinancePublicMinuteFeed,
    *,
    signal_timestamp_ms: int,
    now_ms: int,
) -> dict[str, Any]:
    start_ms = first_minute_open_strictly_after(signal_timestamp_ms)
    end_ms = start_ms + WINDOW_MINUTES * ONE_MINUTE_MS
    if now_ms <= end_ms:
        return {
            "status": "WAITING_CAUSAL_WINDOW",
            "aligned_start_ms": start_ms,
            "measurement_available_after_ms": end_ms + 1,
        }

    windows = {
        symbol: feed.exact_window(
            symbol=symbol,
            start_ms=start_ms,
            minutes=WINDOW_MINUTES,
            now_ms=now_ms,
        )
        for symbol in ("BNBBTC", "BNBUSDT", "BTCUSDT")
    }
    event_volume = _quote_volume(windows["BNBUSDT"])
    baseline, baseline_dates = prior_same_clock_volume_baseline(
        feed,
        event_start_ms=start_ms,
        now_ms=now_ms,
    )
    result = {
        "status": "COMPLETE",
        "signal_timestamp_ms": signal_timestamp_ms,
        "aligned_start_ms": start_ms,
        "aligned_start_utc": datetime.fromtimestamp(
            start_ms / 1000, tz=timezone.utc
        ).isoformat().replace("+00:00", "Z"),
        "bnbbtc_return_15m": _simple_return(windows["BNBBTC"], 15),
        "bnbbtc_return_60m": _simple_return(windows["BNBBTC"], 60),
        "bnbusdt_return_15m": _simple_return(windows["BNBUSDT"], 15),
        "bnbusdt_return_60m": _simple_return(windows["BNBUSDT"], 60),
        "btcusdt_return_15m": _simple_return(windows["BTCUSDT"], 15),
        "btcusdt_return_60m": _simple_return(windows["BTCUSDT"], 60),
        "bnbusdt_quote_volume_60m": event_volume,
        "bnbusdt_baseline_median_prior20_same_clock_60m": baseline,
        "bnbusdt_volume_shock_ratio": event_volume / baseline,
        "baseline_dates_utc": baseline_dates,
        "provider": feed.provider,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["measurement_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result


def _pf(values: list[float]) -> float | None:
    positive = sum(x for x in values if x > 0)
    negative = -sum(x for x in values if x < 0)
    if negative == 0:
        return float("inf") if positive > 0 else None
    return positive / negative


def _positive_concentration(values: list[float]) -> float | None:
    positives = [x for x in values if x > 0]
    total = sum(positives)
    if total <= 0:
        return None
    return max(positives) / total


def evaluate_bnb_diamond_v02(store: Store) -> dict[str, Any]:
    measurements = {
        str(x.get("event_key")): x
        for x in store.read_payloads(MEASUREMENT_EVENT)
        if x.get("event_key")
    }
    resolutions = {
        str(x.get("event_key")): x
        for x in store.read_payloads("BNB_FORWARD_RESOLUTION")
        if x.get("event_key")
    }
    missed = store.read_payloads("BNB_FORWARD_MISSED_PROSPECTIVE_OBSERVATION")
    blocked = store.read_payloads(BLOCKED_EVENT)

    matched = []
    for key in sorted(
        set(measurements) & set(resolutions),
        key=lambda k: (
            int(measurements[k].get("signal_timestamp_ms") or 0),
            k,
        ),
    ):
        matched.append((key, measurements[key], resolutions[key]))

    first25 = matched[:DIAMOND_TARGET_EVENTS]
    locked = len(first25) == DIAMOND_TARGET_EVENTS
    base = [float(r["base_net_bps"]) for _, _, r in first25]
    r60 = [float(m["bnbbtc_return_60m"]) for _, m, _ in first25]
    volume = [float(m["bnbusdt_volume_shock_ratio"]) for _, m, _ in first25]

    base_mean = sum(base) / len(base) if base else None
    base_pf = _pf(base)
    concentration = _positive_concentration(base)
    positive_60 = sum(x > 0 for x in r60)
    volume_gt_one = sum(x > 1 for x in volume)

    gates = {
        "sample_exact_25": locked,
        "base_mean_gt_0": base_mean is not None and base_mean > 0,
        "base_pf_gt_1": base_pf is not None and base_pf > 1,
        "single_positive_share_lte_040": (
            concentration is not None and concentration <= MAX_SINGLE_POSITIVE_SHARE
        ),
        "bnbbtc_60m_positive_events_gte_17": positive_60 >= POSITIVE_EVENT_MINIMUM,
        "median_bnbbtc_60m_gt_0": bool(r60) and median(r60) > 0,
        "volume_shock_gt_1_events_gte_17": volume_gt_one >= POSITIVE_EVENT_MINIMUM,
        "median_volume_shock_gt_1": bool(volume) and median(volume) > 1,
        "missed_eligible_events_eq_0": len(missed) == 0,
    }
    if not locked:
        classification = "DIAMOND_TEST_COLLECTING"
    elif all(gates.values()):
        classification = "DIAMOND_TEST_SURVIVES__REVIEW_REQUIRED"
    else:
        classification = "DIAMOND_TEST_FAIL__EXACT_CANDIDATE_NO_RESCUE"

    return {
        "strategy_id": "BNB-LAUNCHPOOL-DEMAND-001",
        "authority": "BNB-LAUNCHPOOL-DIAMOND-V0.2-2026-09-24",
        "classification": classification,
        "complete_causal_measurements": len(measurements),
        "matched_resolved_events": len(matched),
        "target_events": DIAMOND_TARGET_EVENTS,
        "evaluated_events": len(first25),
        "base_mean_bps": base_mean,
        "base_profit_factor": base_pf,
        "largest_single_positive_base_share": concentration,
        "positive_bnbbtc_60m_events": positive_60,
        "median_bnbbtc_60m_return": float(median(r60)) if r60 else None,
        "volume_shock_gt_one_events": volume_gt_one,
        "median_volume_shock_ratio": float(median(volume)) if volume else None,
        "missed_prospective_observations": len(missed),
        "mechanism_data_blocked_events": len(blocked),
        "gates": gates,
        "automatic_promotion": False,
        "live_trading_authorized": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
    }
