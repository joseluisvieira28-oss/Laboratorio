from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from math import log
from typing import Any

from .evidence import EvidenceStore, PostgresEvidenceStore
from .options_v21_live import (
    FIRST_FULL_POST_FREEZE_SIGNAL_DAY,
    HISTORICAL_STATE_START,
    BinanceBTCUSDTDailyFeed,
    DeribitBTCOptionTradeFeed,
    OptionsV21SourceError,
    _utc_day_bounds,
    build_daily_skew,
    exact_daily_open_if_available,
    latest_complete_signal_day,
    rv20_and_weight,
)

Store = EvidenceStore | PostgresEvidenceStore
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0


def _key(day: date) -> str:
    return f"OPTIONS-SPOTPERP-001:V2.1:{day.isoformat()}"


def _parse_day(value: str) -> date:
    return date.fromisoformat(value)


class OptionsV21ForwardShadowWatcher:
    watcher_id = "OPTIONS-SPOTPERP-001-V2.1-FORWARD-SHADOW"

    def __init__(
        self,
        *,
        store: Store,
        options_feed: DeribitBTCOptionTradeFeed | None = None,
        btc_feed: BinanceBTCUSDTDailyFeed | None = None,
    ) -> None:
        self.store = store
        self.options_feed = options_feed or DeribitBTCOptionTradeFeed()
        self.btc_feed = btc_feed or BinanceBTCUSDTDailyFeed()

    def _existing_by_key(self, event_type: str) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for payload in self.store.read_payloads(event_type):
            key = payload.get("event_key")
            if isinstance(key, str) and key:
                out[key] = payload
        return out

    def run_once(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        latest = latest_complete_signal_day(now_ms)
        if latest is None:
            return {
                "watcher_id": self.watcher_id,
                "status": "WAITING_FIRST_FULL_POST_FREEZE_SIGNAL_DAY",
                "first_signal_day": FIRST_FULL_POST_FREEZE_SIGNAL_DAY.isoformat(),
                "authenticated_exchange_api_used": False,
                "order_created": False,
                "exchange_mutation_performed": False,
            }

        signal_days: list[date] = []
        cursor = FIRST_FULL_POST_FREEZE_SIGNAL_DAY
        while cursor <= latest:
            signal_days.append(cursor)
            cursor += timedelta(days=1)

        existing_days = self._existing_by_key("OPTIONS_V21_FORWARD_SIGNAL_DAY")
        existing_entries = self._existing_by_key("OPTIONS_V21_FORWARD_ENTRY")
        existing_resolutions = self._existing_by_key("OPTIONS_V21_FORWARD_RESOLUTION")

        needs_new_signal = [d for d in signal_days if _key(d) not in existing_days]
        btc_state_bars = None
        if needs_new_signal:
            btc_state_bars = self.btc_feed.daily(
                start_day=HISTORICAL_STATE_START,
                end_day_exclusive=latest + timedelta(days=1),
            )

        inserted_signal_days = 0
        duplicate_signal_days = 0
        inserted_entries = 0
        duplicate_entries = 0
        inserted_resolutions = 0
        duplicate_resolutions = 0
        valid_signal_days = 0
        directional_signal_days = 0

        for day in signal_days:
            key = _key(day)
            payload = existing_days.get(key)

            if payload is None:
                start_ms, end_ms = _utc_day_bounds(day)
                trades = self.options_feed.trades(start_ms=start_ms, end_ms=end_ms)
                signal = build_daily_skew(day, trades)
                if signal["valid"]:
                    if btc_state_bars is None:
                        raise OptionsV21SourceError("BTC causal state cache unavailable")
                    risk = rv20_and_weight(btc_state_bars, signal_day=day)
                else:
                    risk = {
                        "rv20": None,
                        "expanding_median_rv20": None,
                        "weight": 0.0,
                        "valid_rv20_history_count": None,
                    }

                payload = {
                    "watcher_id": self.watcher_id,
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "event_key": key,
                    "signal_date": day.isoformat(),
                    "source_provider": self.options_feed.provider,
                    "signal": signal,
                    "risk_scaling": risk,
                    "used_as_forward_evidence": True,
                    "pre_freeze_backfill": False,
                    "authenticated_exchange_api_used": False,
                    "order_created": False,
                    "exchange_mutation_performed": False,
                }
                receipt = self.store.append_once(
                    "OPTIONS_V21_FORWARD_SIGNAL_DAY", key, payload
                )
                if receipt["inserted"]:
                    inserted_signal_days += 1
                else:
                    duplicate_signal_days += 1
                existing_days[key] = payload
            else:
                duplicate_signal_days += 1

            signal = payload["signal"]
            if signal.get("valid"):
                valid_signal_days += 1
            position = int(signal.get("position") or 0)
            weight = float((payload.get("risk_scaling") or {}).get("weight") or 0.0)
            if not signal.get("valid") or position == 0 or weight <= 0:
                continue
            directional_signal_days += 1

            entry_day = day + timedelta(days=1)
            exit_day = day + timedelta(days=2)

            entry_payload = existing_entries.get(key)
            if entry_payload is None:
                entry_price = exact_daily_open_if_available(
                    self.btc_feed, day=entry_day, now_ms=now_ms
                )
                if entry_price is None:
                    continue
                entry_payload = {
                    "watcher_id": self.watcher_id,
                    "mode": "PUBLIC_SHADOW_ONLY",
                    "event_key": key,
                    "signal_date": day.isoformat(),
                    "entry_date": entry_day.isoformat(),
                    "entry_price": entry_price,
                    "position": position,
                    "weight": weight,
                    "authenticated_exchange_api_used": False,
                    "order_created": False,
                    "exchange_mutation_performed": False,
                }
                receipt = self.store.append_once(
                    "OPTIONS_V21_FORWARD_ENTRY", key, entry_payload
                )
                if receipt["inserted"]:
                    inserted_entries += 1
                else:
                    duplicate_entries += 1
                existing_entries[key] = entry_payload
            else:
                duplicate_entries += 1

            if key in existing_resolutions:
                duplicate_resolutions += 1
                continue

            exit_price = exact_daily_open_if_available(
                self.btc_feed, day=exit_day, now_ms=now_ms
            )
            if exit_price is None:
                continue

            entry_price = float(entry_payload["entry_price"])
            aligned_unscaled_gross_bps = (
                position * log(exit_price / entry_price) * 10_000.0
            )
            scaled_gross_bps = aligned_unscaled_gross_bps * weight
            base_net_bps = scaled_gross_bps - BASE_COST_BPS * weight
            stress_net_bps = scaled_gross_bps - STRESS_COST_BPS * weight

            resolution_payload = {
                "watcher_id": self.watcher_id,
                "mode": "PUBLIC_SHADOW_ONLY",
                "event_key": key,
                "signal_date": day.isoformat(),
                "entry_date": entry_day.isoformat(),
                "exit_date": exit_day.isoformat(),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "position": position,
                "weight": weight,
                "aligned_unscaled_gross_bps": aligned_unscaled_gross_bps,
                "scaled_gross_bps": scaled_gross_bps,
                "base_net_bps": base_net_bps,
                "stress_net_bps": stress_net_bps,
                "authenticated_exchange_api_used": False,
                "order_created": False,
                "exchange_mutation_performed": False,
            }
            receipt = self.store.append_once(
                "OPTIONS_V21_FORWARD_RESOLUTION", key, resolution_payload
            )
            if receipt["inserted"]:
                inserted_resolutions += 1
            else:
                duplicate_resolutions += 1
            existing_resolutions[key] = resolution_payload

        return {
            "watcher_id": self.watcher_id,
            "status": "OK",
            "mode": "PUBLIC_SHADOW_ONLY",
            "options_provider": self.options_feed.provider,
            "btc_provider": self.btc_feed.provider,
            "first_signal_day": FIRST_FULL_POST_FREEZE_SIGNAL_DAY.isoformat(),
            "latest_complete_signal_day": latest.isoformat(),
            "signal_days_scanned": len(signal_days),
            "valid_signal_days": valid_signal_days,
            "directional_signal_days": directional_signal_days,
            "inserted_signal_days": inserted_signal_days,
            "duplicate_signal_days": duplicate_signal_days,
            "inserted_entries": inserted_entries,
            "duplicate_entries": duplicate_entries,
            "inserted_resolutions": inserted_resolutions,
            "duplicate_resolutions": duplicate_resolutions,
            "evidence_backend": self.store.backend,
            "authenticated_exchange_api_used": False,
            "order_created": False,
            "exchange_mutation_performed": False,
        }
