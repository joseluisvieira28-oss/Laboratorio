from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any


SCHEMA_VERSION = "RADAR_META_T0_V1"


def _parse_utc(value: Any) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def _finite_or_unavailable(value: Any) -> float | str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "UNAVAILABLE_AT_T0"
    return number if math.isfinite(number) else "UNAVAILABLE_AT_T0"


def build_t0_snapshot(
    *,
    signal: dict[str, Any],
    captured_at_utc: str,
    market_snapshot: dict[str, Any] | None = None,
    public_context: dict[str, Any] | None = None,
    simultaneous_signals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a shadow-only T0 feature snapshot.

    The function deliberately has no order, sizing, arbitration or strategy
    mutation path. Caller-supplied context must already have been observable
    at or before captured_at_utc. Future-dated context is rejected rather than
    silently backfilled.
    """
    captured = _parse_utc(captured_at_utc)
    candidate_id = str(signal.get("candidate_id") or signal.get("strategy_id") or "")
    signal_key = str(signal.get("immutable_signal_key") or signal.get("signal_identity") or "")
    if not candidate_id or not signal_key:
        raise ValueError("candidate_id and immutable signal identity are required")

    market_snapshot = dict(market_snapshot or {})
    observed_at = market_snapshot.get("observed_at")
    if observed_at is not None and _parse_utc(observed_at) > captured:
        raise ValueError("market snapshot is future-dated relative to T0")

    ctx = dict(public_context or {})
    ctx_ts = ctx.pop("observed_at", None)
    if ctx_ts is not None and _parse_utc(ctx_ts) > captured:
        raise ValueError("public context is future-dated relative to T0")

    allowed_context = {
        "realized_volatility_bps",
        "volume_ratio",
        "funding_rate",
        "open_interest",
        "spot_perp_basis_bps",
        "btc_regime",
        "execution_friction_bps",
    }
    normalized_context = {
        key: (ctx.get(key) if key == "btc_regime" and ctx.get(key) is not None
              else _finite_or_unavailable(ctx.get(key)))
        for key in sorted(allowed_context)
    }

    market = {
        "symbol": market_snapshot.get("symbol", signal.get("symbol", "UNAVAILABLE_AT_T0")),
        "observed_at": observed_at or "UNAVAILABLE_AT_T0",
        "last_price": _finite_or_unavailable(market_snapshot.get("last_price")),
        "bid_price": _finite_or_unavailable(market_snapshot.get("bid_price")),
        "ask_price": _finite_or_unavailable(market_snapshot.get("ask_price")),
        "spread_bps": _finite_or_unavailable(market_snapshot.get("spread_bps")),
        "quote_volume_24h": _finite_or_unavailable(market_snapshot.get("quote_volume_24h")),
    }

    peers = []
    for item in simultaneous_signals or []:
        peer_id = str(item.get("candidate_id") or item.get("strategy_id") or "")
        peer_key = str(item.get("immutable_signal_key") or item.get("signal_identity") or "")
        if peer_id and peer_key:
            peers.append({
                "candidate_id": peer_id,
                "signal_identity": peer_key,
                "direction": item.get("direction", "UNAVAILABLE_AT_T0"),
            })
    peers.sort(key=lambda row: (row["candidate_id"], row["signal_identity"]))

    identity_material = "|".join([candidate_id, signal_key, captured_at_utc, SCHEMA_VERSION])
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "mode": "SHADOW_RESEARCH_ONLY",
        "candidate_id": candidate_id,
        "immutable_signal_key": signal_key,
        "captured_at_utc": captured_at_utc,
        "signal": {
            "symbol": signal.get("symbol", "UNAVAILABLE_AT_T0"),
            "direction": signal.get("direction", "UNAVAILABLE_AT_T0"),
            "entry_target_utc": signal.get("entry_target_utc", "UNAVAILABLE_AT_T0"),
        },
        "market": market,
        "public_context": normalized_context,
        "simultaneous_radar_signals": peers,
        "safety": {
            "creates_signal": False,
            "changes_parent_signal": False,
            "changes_sizing": False,
            "changes_arbitration": False,
            "orders_allowed": False,
            "exchange_mutation_allowed": False,
        },
    }
    snapshot["idempotency_key"] = hashlib.sha256(identity_material.encode("utf-8")).hexdigest()
    snapshot["payload_sha256"] = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return snapshot


def append_t0_snapshot(store: Any, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Append to the existing evidence backend without any execution side effect."""
    if snapshot.get("mode") != "SHADOW_RESEARCH_ONLY":
        raise ValueError("meta-layer snapshot must be shadow-only")
    safety = snapshot.get("safety") or {}
    if any(safety.get(k) is not False for k in (
        "creates_signal", "changes_parent_signal", "changes_sizing",
        "changes_arbitration", "orders_allowed", "exchange_mutation_allowed"
    )):
        raise ValueError("meta-layer safety contract violated")
    return store.append("RADAR_META_T0_SNAPSHOT", snapshot)


__all__ = ["SCHEMA_VERSION", "build_t0_snapshot", "append_t0_snapshot"]
