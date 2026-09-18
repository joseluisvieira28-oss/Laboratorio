from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

UTC = timezone.utc
BASE_URL = "https://fapi.binance.com"
SYMBOL = "AVAXUSDT"
CANDIDATE = "CED1D-0031"
PROVIDER = "BINANCE_USDM_PUBLIC"
FIRST_SHADOW_COMPLETION = datetime(2026, 9, 19, 0, 0, tzinfo=UTC)
SHADOW_EVENT_TYPE = "CED1D0031_VALID_SHADOW_SIGNAL"


class CED1D0031SourceError(RuntimeError):
    pass


class BinanceAVAXDailySource:
    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def daily_klines(self, *, limit: int = 40) -> list[list[Any]]:
        if limit < 21 or limit > 200:
            raise CED1D0031SourceError("daily kline limit out of bounds")
        query = urlencode({"symbol": SYMBOL, "interval": "1d", "limit": limit})
        req = Request(
            f"{BASE_URL}/fapi/v1/klines?{query}",
            method="GET",
            headers={"User-Agent": "crypto-edge-radar-ced1d0031/0.2 public-read-only"},
        )
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    raise CED1D0031SourceError(f"Binance public HTTP {resp.status}")
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, CED1D0031SourceError):
                raise
            raise CED1D0031SourceError(f"Binance USD-M daily source unavailable: {exc}") from exc

        if not isinstance(payload, list) or not payload:
            raise CED1D0031SourceError("invalid kline payload")

        previous_open = None
        out: list[list[Any]] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 7:
                raise CED1D0031SourceError("malformed daily kline")
            try:
                open_ms = int(row[0])
                close_px = float(row[4])
                close_ms = int(row[6])
            except (TypeError, ValueError) as exc:
                raise CED1D0031SourceError("daily kline parse failure") from exc
            if open_ms <= 0 or close_ms <= open_ms or close_px <= 0:
                raise CED1D0031SourceError("invalid daily kline values")
            if previous_open is not None and open_ms <= previous_open:
                raise CED1D0031SourceError("daily klines not strictly ascending")
            previous_open = open_ms
            out.append(row)
        return out


def signal_for_completion(
    *,
    completion: datetime,
    source: BinanceAVAXDailySource,
) -> dict[str, Any]:
    completion = completion.astimezone(UTC)
    if completion.second or completion.microsecond or completion.minute or completion.hour:
        raise CED1D0031SourceError("completion must be exact UTC midnight")
    if completion < FIRST_SHADOW_COMPLETION:
        raise CED1D0031SourceError("pre prospective-shadow boundary")

    rows = source.daily_klines(limit=40)
    completion_ms = int(completion.timestamp() * 1000)
    closes_by_day: dict[str, float] = {}
    for row in rows:
        open_ms = int(row[0])
        close_px = float(row[4])
        close_ms = int(row[6])
        if close_ms >= completion_ms:
            continue
        day = datetime.fromtimestamp(open_ms / 1000, tz=UTC).date().isoformat()
        if day in closes_by_day:
            raise CED1D0031SourceError(f"duplicate daily candle: {day}")
        closes_by_day[day] = close_px

    signal_day = completion.date() - timedelta(days=1)
    lag_day = signal_day - timedelta(days=20)
    sd = signal_day.isoformat()
    ld = lag_day.isoformat()
    if sd not in closes_by_day or ld not in closes_by_day:
        raise CED1D0031SourceError(
            f"exact 20-calendar-day path unavailable: signal_day={sd} lag_day={ld}"
        )

    close_d = closes_by_day[sd]
    close_lag = closes_by_day[ld]
    momentum = math.log(close_d / close_lag)
    if momentum > 0:
        direction = "LONG"
    elif momentum < 0:
        direction = "SHORT"
    else:
        direction = "NONE"

    reference_entry = completion + timedelta(minutes=1)
    reference_exit = reference_entry + timedelta(days=1)
    return {
        "candidate": CANDIDATE,
        "strategy_id": CANDIDATE,
        "symbol": SYMBOL,
        "provider": PROVIDER,
        "signal_key": f"{CANDIDATE}:{sd}",
        "signal_day": sd,
        "lag_day": ld,
        "signal_completion": completion.isoformat(),
        "reference_entry": reference_entry.isoformat(),
        "reference_exit": reference_exit.isoformat(),
        "lookback_calendar_days": 20,
        "horizon_calendar_days": 1,
        "direction_rule": "CONTINUATION_SIGN_LOG_CLOSE_RATIO",
        "direction": direction,
        "close_D": close_d,
        "close_D_minus_20": close_lag,
        "momentum_ln": momentum,
        "live_authorized": False,
        "orders_authorized_by_signal": False,
        "shadow_boundary": FIRST_SHADOW_COMPLETION.isoformat(),
    }


def maybe_emit_signal(*, now: datetime, store, source: BinanceAVAXDailySource) -> dict[str, Any] | None:
    now = now.astimezone(UTC)
    completion = now.replace(hour=0, minute=0, second=0, microsecond=0)
    reference_entry = completion + timedelta(minutes=1)

    if completion < FIRST_SHADOW_COMPLETION:
        return None
    if not (completion <= now < reference_entry):
        return None

    payload = signal_for_completion(completion=completion, source=source)
    if payload["direction"] == "NONE":
        key = payload["signal_key"] + ":ZERO"
        store.append_once("CED1D0031_ZERO_MOMENTUM", key, payload)
        return None

    receipt = store.append_once(
        SHADOW_EVENT_TYPE,
        payload["signal_key"],
        payload,
    )
    payload = dict(payload)
    payload["evidence_receipt"] = receipt
    return payload
