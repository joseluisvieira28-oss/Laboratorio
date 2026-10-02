from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .multi_slot_reservation_v04 import MultiSlotReservationV04, MultiSlotReservationError


class MultiSlotShadowLifecycleError(RuntimeError):
    pass


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _session_name(candidate_id: str, signal_identity: str) -> str:
    digest = hashlib.sha256(signal_identity.encode("utf-8")).hexdigest()[:18]
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in candidate_id).strip("-")
    return f"{safe[:28]}-{digest}"


class MultiSlotShadowLifecycleV04:
    """Synthetic/local lifecycle model for a capacity-3 operator.

    It intentionally has no exchange client and no mutation transport.
    The goal is to prove reservation, restart, unknown-ack and per-session
    reconciliation semantics before a live executor is allowed to exist.
    """

    def __init__(self, *, root: str | Path, capacity: int = 3) -> None:
        self.root = Path(root)
        self.sessions = self.root / "sessions"
        self.ledger = MultiSlotReservationV04(
            self.root / "MULTI_SLOT_LEDGER_V04.json",
            capacity=capacity,
        )
        self.capacity = capacity

    def _dir(self, candidate_id: str, signal_identity: str) -> Path:
        return self.sessions / _session_name(candidate_id, signal_identity)

    def reserve_intent(
        self,
        *,
        candidate_id: str,
        signal_identity: str,
        external_oid: str,
        symbol: str,
        leverage: int,
        max_notional_usdt: float,
        max_initial_margin_usdt: float,
    ) -> dict[str, Any]:
        claim = self.ledger.claim(
            candidate_id=candidate_id,
            signal_identity=signal_identity,
            external_oid=external_oid,
            symbol=symbol,
            leverage=leverage,
            max_notional_usdt=max_notional_usdt,
            max_initial_margin_usdt=max_initial_margin_usdt,
        )
        if claim.get("claim_status") not in {"CLAIMED", "RECOVERED_EXISTING_OWNER"}:
            return claim
        session = self._dir(candidate_id, signal_identity)
        intent = {
            "receipt_type": "SHADOW_ORDER_INTENT",
            "candidate_id": candidate_id,
            "signal_identity": signal_identity,
            "external_oid": external_oid,
            "symbol": symbol.upper(),
            "leverage": leverage,
            "max_notional_usdt": float(max_notional_usdt),
            "max_initial_margin_usdt": float(max_initial_margin_usdt),
            "reserved_at_utc": claim.get("reserved_at_utc"),
            "orders_created": False,
            "exchange_mutation_performed": False,
        }
        path = session / "SHADOW_ORDER_INTENT.json"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != intent:
                raise MultiSlotShadowLifecycleError("SHADOW_INTENT_IDENTITY_MISMATCH")
        else:
            _atomic_write(path, intent)
        return {**claim, "session_dir": str(session)}

    def mark_unknown_ack(
        self,
        *,
        candidate_id: str,
        signal_identity: str,
        detail: str = "synthetic unknown acknowledgement",
    ) -> dict[str, Any]:
        session = self._dir(candidate_id, signal_identity)
        if not (session / "SHADOW_ORDER_INTENT.json").exists():
            raise MultiSlotShadowLifecycleError("UNKNOWN_ACK_WITHOUT_INTENT")
        _atomic_write(session / "SHADOW_ACK_UNKNOWN.json", {
            "receipt_type": "SHADOW_ACK_UNKNOWN",
            "signal_identity": signal_identity,
            "detail": detail,
            "blind_resend_allowed": False,
            "reservation_must_remain": True,
            "recorded_at_utc": _iso_now(),
            "orders_created": False,
            "exchange_mutation_performed": False,
        })
        return {"status": "RECONCILIATION_REQUIRED", "signal_identity": signal_identity}

    def mark_filled(
        self,
        *,
        candidate_id: str,
        signal_identity: str,
        estimated_notional_usdt: float,
        estimated_initial_margin_usdt: float,
    ) -> dict[str, Any]:
        session = self._dir(candidate_id, signal_identity)
        intent_path = session / "SHADOW_ORDER_INTENT.json"
        if not intent_path.exists():
            raise MultiSlotShadowLifecycleError("FILL_WITHOUT_INTENT")
        intent = json.loads(intent_path.read_text(encoding="utf-8"))
        _atomic_write(session / "ACTIVE_TRADE_STATE.json", {
            "state": "EXIT_PENDING",
            "candidate_id": candidate_id,
            "signal_identity": signal_identity,
            "symbol": intent["symbol"],
            "external_oid": intent["external_oid"],
            "leverage": int(intent["leverage"]),
            "estimated_notional_usdt": float(estimated_notional_usdt),
            "estimated_initial_margin_usdt": float(estimated_initial_margin_usdt),
            "opened_at_utc": _iso_now(),
            "shadow_only": True,
            "orders_created": False,
            "exchange_mutation_performed": False,
        })
        return {"status": "SHADOW_FILLED_EXIT_PENDING", "signal_identity": signal_identity}

    def reconcile_close(
        self,
        *,
        candidate_id: str,
        signal_identity: str,
        realized_net_pnl_usdt: float = 0.0,
    ) -> dict[str, Any]:
        session = self._dir(candidate_id, signal_identity)
        active_path = session / "ACTIVE_TRADE_STATE.json"
        if not active_path.exists():
            raise MultiSlotShadowLifecycleError("CLOSE_WITHOUT_ACTIVE_STATE")
        active = json.loads(active_path.read_text(encoding="utf-8"))
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "candidate_id": candidate_id,
            "signal_identity": signal_identity,
            "symbol": active["symbol"],
            "closed_at_utc": _iso_now(),
            "realized_net_pnl_usdt": float(realized_net_pnl_usdt),
            "shadow_only": True,
            "orders_created": False,
            "exchange_mutation_performed": False,
        })
        release = self.ledger.release(
            signal_identity=signal_identity,
            reason="POST_TRADE_RECONCILIATION_CONFIRMED",
        )
        return {
            "status": "SHADOW_CLOSED_RECONCILED",
            "signal_identity": signal_identity,
            "release": release,
        }

    def recover(self) -> dict[str, Any]:
        ledger = self.ledger.current()
        reservations = {
            str(row["signal_identity"]): row
            for row in ledger["reservations"]
        }
        blockers: list[str] = []
        active: list[dict[str, Any]] = []
        unresolved: list[str] = []

        if self.sessions.exists():
            for session in sorted(self.sessions.iterdir()):
                if not session.is_dir():
                    continue
                intent_path = session / "SHADOW_ORDER_INTENT.json"
                active_path = session / "ACTIVE_TRADE_STATE.json"
                close_path = session / "POST_TRADE_RECONCILIATION.json"
                unknown_path = session / "SHADOW_ACK_UNKNOWN.json"

                if close_path.exists():
                    continue
                if not intent_path.exists():
                    blockers.append(f"SESSION_WITHOUT_INTENT:{session.name}")
                    continue
                try:
                    intent = json.loads(intent_path.read_text(encoding="utf-8"))
                    signal = str(intent["signal_identity"])
                except Exception as exc:
                    blockers.append(f"INTENT_INVALID:{session.name}:{type(exc).__name__}")
                    continue

                if signal not in reservations:
                    blockers.append(f"UNRESERVED_NONTERMINAL_SESSION:{signal}")
                    continue

                if unknown_path.exists():
                    unresolved.append(signal)

                if active_path.exists():
                    try:
                        row = json.loads(active_path.read_text(encoding="utf-8"))
                        if str(row.get("signal_identity")) != signal:
                            raise ValueError("identity mismatch")
                        active.append(row)
                    except Exception as exc:
                        blockers.append(f"ACTIVE_STATE_INVALID:{signal}:{type(exc).__name__}")

        session_signals = {
            str(row.get("signal_identity"))
            for row in active
        } | set(unresolved)
        # A reserved intent that has neither active state nor unknown ack is still
        # nonterminal and must keep capacity reserved until explicitly reconciled.
        for signal in reservations:
            session = next(
                (
                    p for p in self.sessions.iterdir()
                    if p.is_dir()
                    and (p / "SHADOW_ORDER_INTENT.json").exists()
                    and json.loads((p / "SHADOW_ORDER_INTENT.json").read_text(encoding="utf-8")).get("signal_identity") == signal
                ),
                None,
            ) if self.sessions.exists() else None
            if session is None:
                blockers.append(f"RESERVATION_WITHOUT_SESSION:{signal}")

        if len(reservations) > self.capacity:
            blockers.append("LEDGER_OVER_CAPACITY")

        blockers = list(dict.fromkeys(blockers))
        return {
            "status": "RECOVERY_PASS" if not blockers else "RECOVERY_FAIL_CLOSED",
            "blockers": blockers,
            "capacity": self.capacity,
            "reserved_count": len(reservations),
            "active_count": len(active),
            "unknown_ack_count": len(unresolved),
            "unknown_ack_signals": sorted(unresolved),
            "free_slots": self.capacity - len(reservations),
            "orders_created": False,
            "exchange_mutation_performed": False,
        }


__all__ = ["MultiSlotShadowLifecycleV04", "MultiSlotShadowLifecycleError"]
