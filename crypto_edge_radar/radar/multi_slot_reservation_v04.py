from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any


class MultiSlotReservationError(RuntimeError):
    pass


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _load(path: Path, *, capacity: int) -> dict[str, Any]:
    if not path.exists():
        return {
            "ledger_version": "MULTI_SLOT_RESERVATION_V0.4",
            "capacity": capacity,
            "reservations": [],
            "updated_at_utc": _iso_now(),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise MultiSlotReservationError(
            f"MULTI_SLOT_LEDGER_UNREADABLE:{type(exc).__name__}"
        ) from exc
    if not isinstance(payload, dict):
        raise MultiSlotReservationError("MULTI_SLOT_LEDGER_NOT_OBJECT")
    if int(payload.get("capacity", -1)) != capacity:
        raise MultiSlotReservationError("MULTI_SLOT_LEDGER_CAPACITY_MISMATCH")
    rows = payload.get("reservations")
    if not isinstance(rows, list):
        raise MultiSlotReservationError("MULTI_SLOT_LEDGER_RESERVATIONS_INVALID")
    seen_signals: set[str] = set()
    seen_oids: set[str] = set()
    seen_symbols: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise MultiSlotReservationError("MULTI_SLOT_RESERVATION_NOT_OBJECT")
        required = (
            "candidate_id",
            "signal_identity",
            "external_oid",
            "symbol",
            "reserved_at_utc",
        )
        if any(not str(row.get(k) or "").strip() for k in required):
            raise MultiSlotReservationError("MULTI_SLOT_RESERVATION_IDENTITY_INVALID")
        sig = str(row["signal_identity"])
        oid = str(row["external_oid"])
        symbol = str(row["symbol"]).upper()
        if sig in seen_signals:
            raise MultiSlotReservationError("MULTI_SLOT_DUPLICATE_SIGNAL_IDENTITY")
        if oid in seen_oids:
            raise MultiSlotReservationError("MULTI_SLOT_DUPLICATE_EXTERNAL_OID")
        if symbol in seen_symbols:
            raise MultiSlotReservationError("MULTI_SLOT_DUPLICATE_ACTIVE_SYMBOL")
        seen_signals.add(sig)
        seen_oids.add(oid)
        seen_symbols.add(symbol)
    if len(rows) > capacity:
        raise MultiSlotReservationError("MULTI_SLOT_LEDGER_OVER_CAPACITY")
    return payload


class MultiSlotReservationV04:
    """Persistent capacity-N reservation ledger.

    A lock file serializes ledger mutation. The lock has no TTL: if a process
    dies while holding it, the system fails closed until an operator reconciles
    the lock rather than guessing that an exchange submission did not happen.
    """

    def __init__(self, path: str | Path, *, capacity: int = 3) -> None:
        if not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self.path = Path(path)
        self.capacity = capacity
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise MultiSlotReservationError(
                "MULTI_SLOT_LEDGER_LOCK_PRESENT_RECONCILIATION_REQUIRED"
            ) from exc
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(_iso_now() + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            yield
        finally:
            self.lock_path.unlink(missing_ok=True)

    def current(self) -> dict[str, Any]:
        return _load(self.path, capacity=self.capacity)

    def claim(
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
        candidate_id = str(candidate_id or "").strip()
        signal_identity = str(signal_identity or "").strip()
        external_oid = str(external_oid or "").strip()
        symbol = str(symbol or "").upper().strip()
        if not candidate_id or not signal_identity or not external_oid or not symbol:
            raise MultiSlotReservationError("MULTI_SLOT_CLAIM_IDENTITY_MISSING")
        if not isinstance(leverage, int) or leverage < 1:
            raise MultiSlotReservationError("MULTI_SLOT_CLAIM_LEVERAGE_INVALID")
        try:
            notional = float(max_notional_usdt)
            margin = float(max_initial_margin_usdt)
        except Exception as exc:
            raise MultiSlotReservationError("MULTI_SLOT_CLAIM_RISK_INVALID") from exc
        if not (notional > 0 and margin > 0):
            raise MultiSlotReservationError("MULTI_SLOT_CLAIM_RISK_INVALID")

        with self._locked():
            ledger = _load(self.path, capacity=self.capacity)
            rows = list(ledger["reservations"])

            for row in rows:
                if str(row["signal_identity"]) == signal_identity:
                    same = (
                        str(row["candidate_id"]) == candidate_id
                        and str(row["external_oid"]) == external_oid
                        and str(row["symbol"]).upper() == symbol
                    )
                    if not same:
                        raise MultiSlotReservationError(
                            "MULTI_SLOT_SIGNAL_IDENTITY_COLLISION"
                        )
                    return {**row, "claim_status": "RECOVERED_EXISTING_OWNER"}

            if any(str(row["external_oid"]) == external_oid for row in rows):
                raise MultiSlotReservationError("MULTI_SLOT_EXTERNAL_OID_COLLISION")
            owner = next(
                (row for row in rows if str(row["symbol"]).upper() == symbol),
                None,
            )
            if owner is not None:
                return {
                    "claim_status": "SYMBOL_OCCUPIED",
                    "owner": owner,
                }
            if len(rows) >= self.capacity:
                return {
                    "claim_status": "CAPACITY_FULL",
                    "capacity": self.capacity,
                    "occupancy": len(rows),
                    "owners": rows,
                }

            row = {
                "reservation_version": "MULTI_SLOT_RESERVATION_V0.4",
                "candidate_id": candidate_id,
                "signal_identity": signal_identity,
                "external_oid": external_oid,
                "symbol": symbol,
                "leverage": leverage,
                "max_notional_usdt": notional,
                "max_initial_margin_usdt": margin,
                "reserved_at_utc": _iso_now(),
                "expires_automatically": False,
                "blind_resend_allowed": False,
            }
            rows.append(row)
            out = {
                "ledger_version": "MULTI_SLOT_RESERVATION_V0.4",
                "capacity": self.capacity,
                "reservations": rows,
                "updated_at_utc": _iso_now(),
            }
            _atomic_write(self.path, out)
            return {
                **row,
                "claim_status": "CLAIMED",
                "slot_index": len(rows) - 1,
                "occupancy_after_claim": len(rows),
            }

    def release(self, *, signal_identity: str, reason: str) -> dict[str, Any]:
        allowed = {
            "PRE_SUBMIT_ABORT_CONFIRMED",
            "ENTRY_TERMINAL_NO_FILL_CONFIRMED",
            "POST_TRADE_RECONCILIATION_CONFIRMED",
        }
        if reason not in allowed:
            raise MultiSlotReservationError("MULTI_SLOT_RELEASE_REASON_NOT_TERMINAL")
        signal_identity = str(signal_identity or "").strip()
        if not signal_identity:
            raise MultiSlotReservationError("MULTI_SLOT_RELEASE_IDENTITY_MISSING")

        with self._locked():
            ledger = _load(self.path, capacity=self.capacity)
            rows = list(ledger["reservations"])
            match = [row for row in rows if str(row["signal_identity"]) == signal_identity]
            if not match:
                return {"release_status": "ALREADY_FREE", "signal_identity": signal_identity}
            if len(match) != 1:
                raise MultiSlotReservationError("MULTI_SLOT_RELEASE_AMBIGUOUS")
            remaining = [row for row in rows if str(row["signal_identity"]) != signal_identity]
            out = {
                "ledger_version": "MULTI_SLOT_RESERVATION_V0.4",
                "capacity": self.capacity,
                "reservations": remaining,
                "updated_at_utc": _iso_now(),
            }
            _atomic_write(self.path, out)
            return {
                "release_status": "RELEASED",
                "signal_identity": signal_identity,
                "reason": reason,
                "released_at_utc": _iso_now(),
                "occupancy_after_release": len(remaining),
            }


__all__ = ["MultiSlotReservationV04", "MultiSlotReservationError"]
