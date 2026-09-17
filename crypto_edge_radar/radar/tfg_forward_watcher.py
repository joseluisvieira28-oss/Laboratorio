from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import time
from typing import Any

from .evidence import EvidenceStore, PostgresEvidenceStore
from .strategies.tfg_donchian_regime_forward import (
    DAY_MS,
    FIFTEEN_MIN_MS,
    FORWARD_FREEZE_MS,
    FROZEN_UNIVERSE,
    TWELVE_HOUR_MS,
    MEXCSpotKlineFeed,
    TFGSourceError,
    aggregate_15m_to_12h,
    detect_signal,
    materialize_entry,
    regime_state,
    resolve_paper_trade,
    utc_iso_from_ms,
)

Store = EvidenceStore | PostgresEvidenceStore
WARMUP_15M_MS = 25 * DAY_MS
WARMUP_DAILY_MS = 240 * DAY_MS


def _first_forward_boundary_ms() -> int:
    return ((FORWARD_FREEZE_MS // TWELVE_HOUR_MS) + 1) * TWELVE_HOUR_MS


def latest_certifiable_signal_close_ms(now_ms: int) -> int | None:
    """Latest 12h boundary whose exact entry 15m bar is fully closed and auditable."""
    boundary = now_ms - (now_ms % TWELVE_HOUR_MS)
    if now_ms < boundary + FIFTEEN_MIN_MS:
        boundary -= TWELVE_HOUR_MS
    return boundary if boundary > FORWARD_FREEZE_MS else None


def _boundaries_through(latest_due_ms: int) -> list[int]:
    first = _first_forward_boundary_ms()
    if latest_due_ms < first:
        return []
    return list(range(first, latest_due_ms + 1, TWELVE_HOUR_MS))


def _paper_trade_key(symbol: str, signal_close_ms: int) -> str:
    return f"TFG-DONCHIAN-REGIME-V1:{symbol}:{signal_close_ms}"


class TFGForwardShadowWatcher:
    """Prospective, replay-safe TFG watcher. Public data only; never creates orders."""

    watcher_id = "TFG-DONCHIAN-REGIME-V1-FORWARD-SHADOW"

    def __init__(self, *, store: Store, feed: MEXCSpotKlineFeed | None = None) -> None:
        self.store = store
        self.feed = feed or MEXCSpotKlineFeed()

    def run_once(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        latest_due = latest_certifiable_signal_close_ms(now_ms)
        if latest_due is None:
            return {
                "watcher_id": self.watcher_id,
                "status": "WAITING_POST_FREEZE_BOUNDARY",
                "authenticated_exchange_api_used": False,
                "order_created": False,
            }

        boundaries = _boundaries_through(latest_due)
        if not boundaries:
            return {
                "watcher_id": self.watcher_id,
                "status": "WAITING_POST_FREEZE_BOUNDARY",
                "authenticated_exchange_api_used": False,
                "order_created": False,
            }

        first_boundary = boundaries[0]
        source_15m: dict[str, list] = {}
        bars_12h: dict[str, list] = {}
        daily: dict[str, list] = {}
        for symbol in FROZEN_UNIVERSE:
            m15 = self.feed.klines(
                symbol,
                "15m",
                start_ms=first_boundary - WARMUP_15M_MS,
                end_ms=now_ms,
                now_ms=now_ms,
            )
            d1 = self.feed.klines(
                symbol,
                "1d",
                start_ms=first_boundary - WARMUP_DAILY_MS,
                end_ms=now_ms,
                now_ms=now_ms,
            )
            h12, _incomplete = aggregate_15m_to_12h(m15)
            complete_opens = {c.open_time for c in h12}
            m15_opens = {c.open_time for c in m15}
            for boundary in boundaries:
                signal_open = boundary - TWELVE_HOUR_MS
                if signal_open not in complete_opens:
                    expected = [signal_open + i * FIFTEEN_MIN_MS for i in range(48)]
                    missing = [ts for ts in expected if ts not in m15_opens]
                    first_seen = m15[0].open_time if m15 else None
                    last_seen = m15[-1].open_time if m15 else None
                    raise TFGSourceError(
                        "missing complete 12H source bucket:"
                        f"{symbol}:{signal_open}:"
                        f"missing_15m={missing}:"
                        f"received_15m={len(m15)}:"
                        f"first_seen={first_seen}:last_seen={last_seen}"
                    )
            source_15m[symbol] = m15
            bars_12h[symbol] = h12
            daily[symbol] = d1

        inserted_signals = 0
        duplicate_signals = 0
        inserted_resolutions = 0
        duplicate_resolutions = 0
        eligible_signal_count = 0
        regime_on_boundaries = 0

        for boundary in boundaries:
            regime = regime_state(daily, signal_close_ms=boundary)
            if regime.get("state") == "MISSING":
                raise TFGSourceError(f"regime source incomplete at {boundary}: {regime.get('reason')}")
            if regime.get("state") != "ON":
                continue
            regime_on_boundaries += 1

            for symbol in FROZEN_UNIVERSE:
                candidate = detect_signal(symbol, bars_12h[symbol], signal_close_ms=boundary)
                if candidate is None:
                    continue
                eligible_signal_count += 1
                trade = materialize_entry(candidate, source_15m[symbol])
                if trade is None:
                    raise TFGSourceError(f"eligible signal cannot bind exact entry:{symbol}:{boundary}")

                key = _paper_trade_key(symbol, boundary)
                signal_payload = {
                    "watcher_id": self.watcher_id,
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "event_key": key,
                    "signal_close_utc": utc_iso_from_ms(boundary),
                    "candidate": asdict(candidate),
                    "paper_trade": asdict(trade),
                    "regime": regime,
                    "authenticated_exchange_api_used": False,
                    "order_created": False,
                    "exchange_mutation_performed": False,
                }
                receipt = self.store.append_once("TFG_FORWARD_SIGNAL", key, signal_payload)
                if receipt["inserted"]:
                    inserted_signals += 1
                else:
                    duplicate_signals += 1

                outcome = resolve_paper_trade(trade, bars_12h[symbol])
                if outcome.exit_price is None:
                    continue
                resolution_payload = {
                    "watcher_id": self.watcher_id,
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "event_key": key,
                    "signal_close_utc": utc_iso_from_ms(boundary),
                    "paper_trade": asdict(trade),
                    "outcome": asdict(outcome),
                    "authenticated_exchange_api_used": False,
                    "order_created": False,
                    "exchange_mutation_performed": False,
                }
                resolution = self.store.append_once("TFG_FORWARD_RESOLUTION", key, resolution_payload)
                if resolution["inserted"]:
                    inserted_resolutions += 1
                else:
                    duplicate_resolutions += 1

        return {
            "watcher_id": self.watcher_id,
            "status": "OK",
            "mode": "PUBLIC_SHADOW_ONLY",
            "provider": self.feed.provider,
            "freeze_utc": utc_iso_from_ms(FORWARD_FREEZE_MS),
            "latest_due_signal_close_utc": utc_iso_from_ms(latest_due),
            "boundaries_scanned": len(boundaries),
            "regime_on_boundaries": regime_on_boundaries,
            "eligible_signal_count": eligible_signal_count,
            "inserted_signals": inserted_signals,
            "duplicate_signals": duplicate_signals,
            "inserted_resolutions": inserted_resolutions,
            "duplicate_resolutions": duplicate_resolutions,
            "evidence_backend": self.store.backend,
            "authenticated_exchange_api_used": False,
            "order_created": False,
            "exchange_mutation_performed": False,
        }

    def run_forever(self, *, interval_seconds: float = 300.0) -> None:
        if interval_seconds < 30:
            raise ValueError("TFG watcher interval must be >=30 seconds")
        while True:
            self.run_once()
            time.sleep(interval_seconds)
