from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from math import isfinite
from statistics import median
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .evidence import EvidenceStore, PostgresEvidenceStore

Store = EvidenceStore | PostgresEvidenceStore

PROVIDER = "BINANCE_SPOT_DATA_API_PUBLIC"
BASE_URL = "https://data-api.binance.vision"
KLINE_PATH = "/api/v3/klines"
ONE_MIN_MS = 60_000
MEASUREMENT_EVENT = "BNB_DIAMOND_CAUSAL_V02"
BLOCKED_EVENT = "BNB_DIAMOND_CAUSAL_V02_BLOCKED"
PARENT_SELECTION_EVENT = "BNB_FORWARD_PAPER_SELECTION"
REQUIRED_BASELINE_DAYS = 20
MAX_BASELINE_LOOKBACK_DAYS = 40
FINAL_SAMPLE = 25


class BNBDiamondV02Error(RuntimeError):
    pass


class BNBDiamondWindowUnavailable(BNBDiamondV02Error):
    pass


@dataclass(frozen=True)
class MinuteBar:
    open_time: int
    open: float
    close: float
    quote_volume: float
    close_time: int


def strict_next_minute_open_ms(signal_timestamp_ms: int) -> int:
    if signal_timestamp_ms <= 0:
        raise ValueError("signal timestamp must be positive")
    return (signal_timestamp_ms // ONE_MIN_MS + 1) * ONE_MIN_MS


def _parse_bar(row: Any) -> MinuteBar:
    if not isinstance(row, list) or len(row) < 8:
        raise BNBDiamondV02Error("invalid Binance 1m kline row")
    try:
        bar = MinuteBar(
            open_time=int(row[0]),
            open=float(row[1]),
            close=float(row[4]),
            close_time=int(row[6]),
            quote_volume=float(row[7]),
        )
    except (TypeError, ValueError) as exc:
        raise BNBDiamondV02Error("invalid Binance 1m kline values") from exc
    if bar.open_time % ONE_MIN_MS != 0:
        raise BNBDiamondV02Error("1m open timestamp not UTC aligned")
    if bar.close_time != bar.open_time + ONE_MIN_MS - 1:
        raise BNBDiamondV02Error("1m close timestamp mismatch")
    if not all(isfinite(x) for x in (bar.open, bar.close, bar.quote_volume)):
        raise BNBDiamondV02Error("non-finite 1m kline value")
    if bar.open <= 0 or bar.close <= 0 or bar.quote_volume < 0:
        raise BNBDiamondV02Error("invalid 1m kline numeric domain")
    return bar


class BinanceSpotOneMinuteFeed:
    provider = PROVIDER

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = int(timeout)

    def _get_json(self, query: dict[str, Any]) -> Any:
        url = f"{BASE_URL}{KLINE_PATH}?{urlencode(query)}"
        request = Request(
            url,
            method="GET",
            headers={"User-Agent": "crypto-edge-radar/0.9 bnb-diamond-v02-read-only"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise BNBDiamondV02Error(f"Binance Spot HTTP {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, BNBDiamondV02Error):
                raise
            raise BNBDiamondV02Error(
                f"Binance 1m public source unavailable:{type(exc).__name__}:{exc}"
            ) from exc

    def exact_window(
        self,
        *,
        symbol: str,
        start_ms: int,
        minutes: int,
        now_ms: int,
    ) -> list[MinuteBar]:
        if symbol not in {"BNBBTC", "BNBUSDT", "BTCUSDT"}:
            raise BNBDiamondV02Error("symbol outside frozen Diamond V0.2 allowlist")
        if start_ms % ONE_MIN_MS != 0 or minutes < 1 or minutes > 60:
            raise BNBDiamondV02Error("invalid frozen 1m window request")
        end_ms = start_ms + minutes * ONE_MIN_MS
        if now_ms < end_ms:
            raise BNBDiamondWindowUnavailable("WINDOW_NOT_YET_COMPLETE")
        payload = self._get_json(
            {
                "symbol": symbol,
                "interval": "1m",
                "startTime": start_ms,
                "endTime": end_ms - 1,
                "limit": minutes + 2,
            }
        )
        if not isinstance(payload, list):
            raise BNBDiamondV02Error("Binance 1m payload is not a list")
        bars = [_parse_bar(row) for row in payload]
        by_open = {
            b.open_time: b for b in bars if start_ms <= b.open_time < end_ms
        }
        expected = [start_ms + i * ONE_MIN_MS for i in range(minutes)]
        if sorted(by_open) != expected:
            raise BNBDiamondWindowUnavailable("INCOMPLETE_EXACT_1M_WINDOW")
        return [by_open[t] for t in expected]


def _simple_return(bars: list[MinuteBar]) -> float:
    return bars[-1].close / bars[0].open - 1.0


def _quote_volume(bars: list[MinuteBar]) -> float:
    return float(sum(x.quote_volume for x in bars))


def measure_causal_event(
    feed: BinanceSpotOneMinuteFeed,
    *,
    signal_timestamp_ms: int,
    now_ms: int,
) -> dict[str, Any]:
    start_ms = strict_next_minute_open_ms(signal_timestamp_ms)
    if now_ms < start_ms + 60 * ONE_MIN_MS:
        return {
            "status": "WAITING_CAUSAL_60M_WINDOW",
            "aligned_start_ms": start_ms,
        }

    windows: dict[str, list[MinuteBar]] = {}
    for symbol in ("BNBBTC", "BNBUSDT", "BTCUSDT"):
        windows[symbol] = feed.exact_window(
            symbol=symbol,
            start_ms=start_ms,
            minutes=60,
            now_ms=now_ms,
        )

    baseline_values: list[float] = []
    baseline_dates: list[str] = []
    event_start = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc)
    for days_back in range(1, MAX_BASELINE_LOOKBACK_DAYS + 1):
        candidate = event_start - timedelta(days=days_back)
        candidate_ms = int(candidate.timestamp() * 1000)
        try:
            bars = feed.exact_window(
                symbol="BNBUSDT",
                start_ms=candidate_ms,
                minutes=60,
                now_ms=now_ms,
            )
        except BNBDiamondWindowUnavailable:
            continue
        baseline_values.append(_quote_volume(bars))
        baseline_dates.append(candidate.date().isoformat())
        if len(baseline_values) == REQUIRED_BASELINE_DAYS:
            break

    if len(baseline_values) != REQUIRED_BASELINE_DAYS:
        raise BNBDiamondWindowUnavailable(
            "MECHANISM_DATA_BLOCKED_FEWER_THAN_20_COMPLETE_PRIOR_SAME_CLOCK_DAYS"
        )

    volume_baseline = float(median(baseline_values))
    if volume_baseline <= 0:
        raise BNBDiamondWindowUnavailable("MECHANISM_DATA_BLOCKED_NONPOSITIVE_VOLUME_BASELINE")

    bnbbtc = windows["BNBBTC"]
    bnbusdt = windows["BNBUSDT"]
    btcusdt = windows["BTCUSDT"]
    result = {
        "status": "CAUSAL_MEASUREMENT_COMPLETE",
        "signal_timestamp_ms": signal_timestamp_ms,
        "aligned_start_ms": start_ms,
        "bnbbtc_return_15m": _simple_return(bnbbtc[:15]),
        "bnbbtc_return_60m": _simple_return(bnbbtc),
        "bnbusdt_return_15m": _simple_return(bnbusdt[:15]),
        "bnbusdt_return_60m": _simple_return(bnbusdt),
        "btcusdt_return_15m": _simple_return(btcusdt[:15]),
        "btcusdt_return_60m": _simple_return(btcusdt),
        "bnbusdt_minus_btcusdt_return_60m": _simple_return(bnbusdt) - _simple_return(btcusdt),
        "bnbusdt_quote_volume_60m": _quote_volume(bnbusdt),
        "bnbusdt_quote_volume_baseline_median_prior20": volume_baseline,
        "bnbusdt_volume_shock_ratio": _quote_volume(bnbusdt) / volume_baseline,
        "baseline_dates_utc": baseline_dates,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }
    return result


def summarize_complete_measurements(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != FINAL_SAMPLE:
        return {
            "status": "COLLECTING",
            "complete_measurements": len(rows),
            "required_measurements": FINAL_SAMPLE,
            "verdict_allowed_now": False,
        }
    r60 = [float(r["bnbbtc_return_60m"]) for r in rows]
    vr = [float(r["bnbusdt_volume_shock_ratio"]) for r in rows]
    positive_r60 = sum(x > 0 for x in r60)
    volume_gt_one = sum(x > 1 for x in vr)
    return {
        "status": "CAUSAL_GATE_READY_FOR_PARENT_RECONCILIATION",
        "complete_measurements": FINAL_SAMPLE,
        "required_measurements": FINAL_SAMPLE,
        "positive_bnbbtc_60m_events": positive_r60,
        "median_bnbbtc_60m_return": float(median(r60)),
        "volume_shock_ratio_gt_one_events": volume_gt_one,
        "median_volume_shock_ratio": float(median(vr)),
        "causal_gate_pass": (
            positive_r60 >= 17
            and median(r60) > 0
            and volume_gt_one >= 17
            and median(vr) > 1
        ),
        "verdict_allowed_now": True,
    }


class BNBDiamondV02Sidecar:
    """Measurement-only sidecar over already-selected parent forward events.

    A failure here must never alter the parent event, selection, resolution,
    direction, costs, timing, or overlap semantics.
    """

    def __init__(
        self,
        *,
        store: Store,
        feed: BinanceSpotOneMinuteFeed | None = None,
    ) -> None:
        self.store = store
        self.feed = feed or BinanceSpotOneMinuteFeed()

    @staticmethod
    def _signal_ms(payload: dict[str, Any]) -> int:
        value = payload.get("signal_timestamp_utc")
        if not isinstance(value, str):
            raise BNBDiamondV02Error("parent selection missing signal_timestamp_utc")
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise BNBDiamondV02Error("parent signal timestamp must be timezone aware")
        return int(dt.astimezone(timezone.utc).timestamp() * 1000)

    def run_once(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        selections = self.store.read_payloads(PARENT_SELECTION_EVENT)
        complete = {
            str(x.get("event_key")): x
            for x in self.store.read_payloads(MEASUREMENT_EVENT)
            if x.get("event_key")
        }
        blocked = {
            str(x.get("event_key")): x
            for x in self.store.read_payloads(BLOCKED_EVENT)
            if x.get("event_key")
        }

        inserted = 0
        waiting = 0
        transient_failures = 0
        newly_blocked = 0
        for selection in selections:
            key = str(selection.get("event_key") or "")
            if not key or key in complete or key in blocked:
                continue
            try:
                signal_ms = self._signal_ms(selection)
                result = measure_causal_event(
                    self.feed,
                    signal_timestamp_ms=signal_ms,
                    now_ms=now_ms,
                )
                if result["status"] == "WAITING_CAUSAL_60M_WINDOW":
                    waiting += 1
                    continue
                payload = {
                    **result,
                    "event_key": key,
                    "parent_selection_required": True,
                    "parent_science_changed": False,
                    "measurement_contract": "BNB-LAUNCHPOOL-DIAMOND-V0.2-2026-09-24",
                }
                rec = self.store.append_once(MEASUREMENT_EVENT, key, payload)
                if rec["inserted"]:
                    inserted += 1
                    complete[key] = payload
            except BNBDiamondWindowUnavailable as exc:
                reason = str(exc)
                if reason.startswith("MECHANISM_DATA_BLOCKED"):
                    payload = {
                        "event_key": key,
                        "status": "MECHANISM_DATA_BLOCKED",
                        "reason": reason,
                        "counts_toward_diamond_25": False,
                        "parent_science_changed": False,
                        "authenticated_exchange_api_used": False,
                        "orders_created": False,
                        "exchange_mutation_performed": False,
                        "live_capital_enabled": False,
                    }
                    rec = self.store.append_once(BLOCKED_EVENT, key, payload)
                    if rec["inserted"]:
                        newly_blocked += 1
                        blocked[key] = payload
                else:
                    waiting += 1
            except Exception:
                transient_failures += 1

        rows = sorted(
            complete.values(),
            key=lambda x: (int(x.get("signal_timestamp_ms") or 0), str(x.get("event_key") or "")),
        )
        # V0.2 is frozen to the first 25 complete causal measurements.
        # Later observations may be preserved, but may not rewrite the first-25 gate.
        summary_rows = rows[:FINAL_SAMPLE]
        summary = summarize_complete_measurements(summary_rows)
        summary["total_complete_measurements_preserved"] = len(rows)
        return {
            "status": (
                "DIAMOND_MEASUREMENT_BLOCKED"
                if blocked
                else "OK"
            ),
            "measurement_contract": "BNB-LAUNCHPOOL-DIAMOND-V0.2-2026-09-24",
            "parent_science_changed": False,
            "parent_selected_events_seen": len(selections),
            "complete_causal_measurements": len(complete),
            "blocked_causal_measurements": len(blocked),
            "inserted_measurements_this_run": inserted,
            "newly_blocked_this_run": newly_blocked,
            "waiting_events_this_run": waiting,
            "transient_source_failures_this_run": transient_failures,
            "summary": summary,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
