from __future__ import annotations

from datetime import date, datetime, timezone
import math
import time
from typing import Any

from .evidence import EvidenceStore, PostgresEvidenceStore
from .market import MEXCFuturesPublicFeed, MarketDataError
from .mexc_spot import MEXCSpotPublicFeed, MEXCSpotPublicError

Store = EvidenceStore | PostgresEvidenceStore

AUTHORITY_ID = "OPTIONS-SPOTPERP-001-V2.1-PUBLIC-EXECUTION-SHADOW-V0.1"
FIRST_ELIGIBLE_ENTRY_DAY = date(2026, 9, 26)
PARENT_ENTRY_EVENT = "OPTIONS_V21_FORWARD_ENTRY"
OBSERVATION_EVENT = "OPTIONS_V21_PUBLIC_EXECUTION_OBSERVATION_V01"
MISSED_EVENT = "OPTIONS_V21_PUBLIC_EXECUTION_MISSED_V01"

RESEARCH_NOTIONAL_USDT = 100.0
SCIENTIFIC_BASE_COST_BPS = 10.0
SCIENTIFIC_STRESS_COST_BPS = 20.0
SPOT_TAKER_ONE_WAY_FRACTION = 0.0005
FUTURES_TAKER_ONE_WAY_FRACTION = 0.0008
OPERATIONAL_SAMPLE_MIN = 10


class OptionsV21ExecutionShadowError(RuntimeError):
    pass


def _f(value: Any, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise OptionsV21ExecutionShadowError(f"invalid numeric field {name}") from exc
    if not math.isfinite(out):
        raise OptionsV21ExecutionShadowError(f"non-finite numeric field {name}")
    return out


def _entry_boundary_ms(entry_day: date) -> int:
    return int(datetime(
        entry_day.year,
        entry_day.month,
        entry_day.day,
        tzinfo=timezone.utc,
    ).timestamp() * 1000)


def _spot_depth_capacity_usdt(depth: dict[str, Any]) -> float:
    total = 0.0
    for row in depth.get("asks") or []:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        price = _f(row[0], "spot ask price")
        qty = _f(row[1], "spot ask qty")
        if price > 0 and qty > 0:
            total += price * qty
    return total


def _futures_short_depth_capacity_usdt(
    depth: dict[str, Any],
    *,
    contract_size: float,
) -> float:
    total = 0.0
    for row in depth.get("bids") or []:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        price = _f(row[0], "futures bid price")
        contracts = _f(row[1], "futures bid contracts")
        if price > 0 and contracts > 0:
            total += price * contracts * contract_size
    return total


def _clock_receipt(feed: MEXCFuturesPublicFeed) -> dict[str, float]:
    before = time.time_ns() / 1_000_000.0
    server = float(feed.server_time_ms())
    after = time.time_ns() / 1_000_000.0
    midpoint = (before + after) / 2.0
    return {
        "server_time_ms": server,
        "request_rtt_ms": after - before,
        "estimated_server_minus_local_ms": server - midpoint,
    }


def _spot_long_observation(
    *,
    spot: MEXCSpotPublicFeed,
) -> dict[str, Any]:
    symbols = spot.default_symbols()
    if "BTCUSDT" not in symbols:
        raise OptionsV21ExecutionShadowError("BTCUSDT absent from MEXC spot defaultSymbols")
    book = spot.book_ticker("BTCUSDT")
    depth = spot.depth("BTCUSDT", limit=20)
    bid = _f(book.get("bidPrice"), "spot bid")
    ask = _f(book.get("askPrice"), "spot ask")
    if bid <= 0 or ask <= 0 or ask < bid:
        raise OptionsV21ExecutionShadowError("invalid MEXC spot top of book")
    mid = (bid + ask) / 2.0
    spread_bps = (ask - bid) / mid * 10_000.0
    fee_rt_bps = 2.0 * SPOT_TAKER_ONE_WAY_FRACTION * 10_000.0
    proxy = fee_rt_bps + spread_bps
    capacity = _spot_depth_capacity_usdt(depth)
    return {
        "route": "MEXC_SPOT_LONG",
        "market": "MEXC_SPOT",
        "symbol": "BTCUSDT",
        "provider": spot.provider,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_bps": spread_bps,
        "visible_entry_side_depth_capacity_usdt": capacity,
        "capacity_covers_100usdt": capacity >= RESEARCH_NOTIONAL_USDT,
        "public_taker_one_way_bps_reference": SPOT_TAKER_ONE_WAY_FRACTION * 10_000.0,
        "public_taker_round_trip_bps_reference": fee_rt_bps,
        "observable_nonfunding_round_trip_proxy_bps": proxy,
        "base10_headroom_after_observable_nonfunding_proxy_bps": SCIENTIFIC_BASE_COST_BPS - proxy,
        "stress20_headroom_after_observable_nonfunding_proxy_bps": SCIENTIFIC_STRESS_COST_BPS - proxy,
        "funding_applies": False,
    }


def _perp_short_observation(
    *,
    futures: MEXCFuturesPublicFeed,
) -> dict[str, Any]:
    snapshots = futures.all_market_snapshots()
    snap = snapshots.get("BTCUSDT")
    if snap is None:
        raise OptionsV21ExecutionShadowError("BTCUSDT futures snapshot missing")
    bid = _f(snap.bid_price, "futures bid")
    ask = _f(snap.ask_price, "futures ask")
    if bid <= 0 or ask <= 0 or ask < bid:
        raise OptionsV21ExecutionShadowError("invalid MEXC futures top of book")
    mid = (bid + ask) / 2.0
    spread_bps = (ask - bid) / mid * 10_000.0

    contract = futures.contract_row("BTC_USDT")
    if contract.get("apiAllowed") is False:
        raise OptionsV21ExecutionShadowError("BTC_USDT public contract reports apiAllowed=false")
    contract_size = _f(contract.get("contractSize"), "contractSize")
    if contract_size <= 0:
        raise OptionsV21ExecutionShadowError("contractSize must be positive")
    depth = futures.order_book_depth("BTC_USDT", limit=20)
    capacity = _futures_short_depth_capacity_usdt(
        depth,
        contract_size=contract_size,
    )

    funding = futures.funding_rate("BTC_USDT")
    rate = _f(funding.get("fundingRate"), "fundingRate")
    cycle_hours = int(_f(funding.get("collectCycle"), "collectCycle"))
    if cycle_hours <= 0:
        raise OptionsV21ExecutionShadowError("collectCycle must be positive")
    settlements_24h = 24.0 / float(cycle_hours)
    short_burden_scenario = -rate * settlements_24h * 10_000.0

    fee_rt_bps = 2.0 * FUTURES_TAKER_ONE_WAY_FRACTION * 10_000.0
    proxy = fee_rt_bps + spread_bps
    return {
        "route": "MEXC_USDT_PERP_SHORT",
        "market": "MEXC_USDT_PERPETUAL",
        "symbol": "BTC_USDT",
        "provider": futures.provider,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_bps": spread_bps,
        "contract_size_btc": contract_size,
        "min_vol_contracts": contract.get("minVol"),
        "vol_unit_contracts": contract.get("volUnit"),
        "visible_entry_side_depth_capacity_usdt": capacity,
        "capacity_covers_100usdt": capacity >= RESEARCH_NOTIONAL_USDT,
        "public_taker_one_way_bps_reference": FUTURES_TAKER_ONE_WAY_FRACTION * 10_000.0,
        "public_taker_round_trip_bps_reference": fee_rt_bps,
        "observable_nonfunding_round_trip_proxy_bps": proxy,
        "base10_headroom_after_observable_nonfunding_proxy_bps": SCIENTIFIC_BASE_COST_BPS - proxy,
        "stress20_headroom_after_observable_nonfunding_proxy_bps": SCIENTIFIC_STRESS_COST_BPS - proxy,
        "funding_applies": True,
        "current_funding_rate": rate,
        "funding_collect_cycle_hours": cycle_hours,
        "constant_current_rate_24h_short_burden_bps_scenario": short_burden_scenario,
        "funding_scenario_is_not_forecast": True,
    }


def evaluate_options_v21_execution_shadow(store: Store) -> dict[str, Any]:
    observations = sorted(
        store.read_payloads(OBSERVATION_EVENT),
        key=lambda x: (str(x.get("entry_date") or ""), str(x.get("event_key") or "")),
    )
    missed = store.read_payloads(MISSED_EVENT)
    long_obs = [x for x in observations if int(x.get("position") or 0) > 0]
    short_obs = [x for x in observations if int(x.get("position") or 0) < 0]
    proxies = [
        float((x.get("public_execution") or {}).get("observable_nonfunding_round_trip_proxy_bps"))
        for x in observations
        if (x.get("public_execution") or {}).get("observable_nonfunding_round_trip_proxy_bps") is not None
    ]
    capacities = [
        bool((x.get("public_execution") or {}).get("capacity_covers_100usdt"))
        for x in observations
    ]
    complete = len(observations)
    return {
        "authority_id": AUTHORITY_ID,
        "status": (
            "PUBLIC_EXECUTION_SAMPLE_READY_FOR_AUDIT"
            if complete >= OPERATIONAL_SAMPLE_MIN
            else "PUBLIC_EXECUTION_EVIDENCE_ACCUMULATING"
        ),
        "first_eligible_entry_day": FIRST_ELIGIBLE_ENTRY_DAY.isoformat(),
        "complete_execution_observations": complete,
        "minimum_execution_observations": OPERATIONAL_SAMPLE_MIN,
        "long_observations": len(long_obs),
        "short_observations": len(short_obs),
        "missed_operational_observations": len(missed),
        "operational_sample_integrity_clean": len(missed) == 0,
        "mean_observable_nonfunding_round_trip_proxy_bps": (
            sum(proxies) / len(proxies) if proxies else None
        ),
        "capacity_100usdt_coverage": (
            sum(1 for x in capacities if x) / len(capacities)
            if capacities else None
        ),
        "automatic_tier1_promotion": False,
        "automatic_micro_live_authorization": False,
        "live_capital_enabled": False,
    }


class OptionsV21PublicExecutionShadow:
    def __init__(
        self,
        *,
        store: Store,
        spot: MEXCSpotPublicFeed | None = None,
        futures: MEXCFuturesPublicFeed | None = None,
    ) -> None:
        self.store = store
        self.spot = spot or MEXCSpotPublicFeed(timeout=10)
        self.futures = futures or MEXCFuturesPublicFeed(timeout=10)

    def _keys(self, event_type: str) -> set[str]:
        return {
            str(x.get("event_key"))
            for x in self.store.read_payloads(event_type)
            if x.get("event_key")
        }

    def run_once(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        now = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc)
        today = now.date()

        entries = sorted(
            self.store.read_payloads(PARENT_ENTRY_EVENT),
            key=lambda x: (str(x.get("entry_date") or ""), str(x.get("event_key") or "")),
        )
        observed = self._keys(OBSERVATION_EVENT)
        missed = self._keys(MISSED_EVENT)

        inserted = 0
        inserted_missed = 0
        transient_failures = 0
        waiting_future = 0

        for entry in entries:
            key = str(entry.get("event_key") or "")
            if not key or key in observed or key in missed:
                continue
            entry_date_raw = entry.get("entry_date")
            if not isinstance(entry_date_raw, str):
                continue
            entry_day = date.fromisoformat(entry_date_raw)
            if entry_day < FIRST_ELIGIBLE_ENTRY_DAY:
                continue
            if entry_day > today:
                waiting_future += 1
                continue
            if entry_day < today:
                payload = {
                    "authority_id": AUTHORITY_ID,
                    "event_key": key,
                    "signal_date": entry.get("signal_date"),
                    "entry_date": entry_date_raw,
                    "reason": "NO_SAME_DAY_PUBLIC_EXECUTION_OBSERVATION__NO_BACKFILL",
                    "used_to_modify_parent_science": False,
                    "authenticated_exchange_api_used": False,
                    "orders_created": False,
                    "exchange_mutation_performed": False,
                    "live_capital_enabled": False,
                }
                result = self.store.append_once(MISSED_EVENT, key, payload)
                if result["inserted"]:
                    inserted_missed += 1
                continue

            position = int(entry.get("position") or 0)
            if position not in (-1, 1):
                continue

            try:
                clock = _clock_receipt(self.futures)
                if position > 0:
                    public_execution = _spot_long_observation(spot=self.spot)
                else:
                    public_execution = _perp_short_observation(futures=self.futures)
            except (OptionsV21ExecutionShadowError, MEXCSpotPublicError, MarketDataError):
                transient_failures += 1
                continue

            payload = {
                "authority_id": AUTHORITY_ID,
                "strategy_id": "OPTIONS-SPOTPERP-001-V2.1",
                "event_key": key,
                "signal_date": entry.get("signal_date"),
                "entry_date": entry_date_raw,
                "position": position,
                "weight": float(entry.get("weight") or 0.0),
                "research_notional_usdt": RESEARCH_NOTIONAL_USDT,
                "scientific_costs_bps": {
                    "base": SCIENTIFIC_BASE_COST_BPS,
                    "stress": SCIENTIFIC_STRESS_COST_BPS,
                    "changed_by_observation": False,
                },
                "capture": {
                    "checked_at_utc": now.isoformat().replace("+00:00", "Z"),
                    "intended_entry_boundary_ms": _entry_boundary_ms(entry_day),
                    "capture_lag_from_intended_entry_ms": max(
                        0,
                        now_ms - _entry_boundary_ms(entry_day),
                    ),
                    "mexc_public_clock": clock,
                },
                "public_execution": public_execution,
                "used_to_modify_parent_science": False,
                "authenticated_exchange_api_used": False,
                "orders_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            }
            result = self.store.append_once(OBSERVATION_EVENT, key, payload)
            if result["inserted"]:
                inserted += 1
                observed.add(key)

        metrics = evaluate_options_v21_execution_shadow(self.store)
        return {
            "strategy_id": "OPTIONS-SPOTPERP-001-V2.1",
            "status": "OK",
            "authority_id": AUTHORITY_ID,
            "inserted_execution_observations": inserted,
            "inserted_missed_observations": inserted_missed,
            "transient_public_source_failures": transient_failures,
            "waiting_future_parent_entries": waiting_future,
            "metrics": metrics,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
