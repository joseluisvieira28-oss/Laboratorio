from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any


class GlobalSlotReservationError(RuntimeError):
    pass


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_create(path: Path, payload: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return True


def _load(path: Path) -> dict[str, Any]:
    last: Exception | None = None
    # O_EXCL creates the file before the winning process finishes writing it.
    # Briefly retry that publication window; a persistently corrupt reservation
    # still fails closed and is never expired automatically.
    for _attempt in range(25):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise GlobalSlotReservationError("GLOBAL_SLOT_RESERVATION_NOT_OBJECT")
            required = ("candidate_id", "signal_identity", "external_oid", "reserved_at_utc")
            if any(not str(payload.get(key) or "") for key in required):
                raise GlobalSlotReservationError("GLOBAL_SLOT_RESERVATION_IDENTITY_INVALID")
            return payload
        except GlobalSlotReservationError:
            raise
        except Exception as exc:
            last = exc
            time.sleep(0.01)
    raise GlobalSlotReservationError(
        f"GLOBAL_SLOT_RESERVATION_UNREADABLE:{type(last).__name__ if last else 'UNKNOWN'}"
    ) from last


class GlobalSlotReservationV03:
    """Persistent, non-expiring, account-wide single-slot reservation.

    No TTL exists by design. Unknown exchange state must keep the slot reserved.
    Release is only allowed by the same signal identity after a terminal local
    reconciliation or a provable pre-submit abort.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def current(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return _load(self.path)

    def claim(
        self,
        *,
        candidate_id: str,
        signal_identity: str,
        external_oid: str,
    ) -> dict[str, Any]:
        candidate_id = str(candidate_id or "").strip()
        signal_identity = str(signal_identity or "").strip()
        external_oid = str(external_oid or "").strip()
        if not candidate_id or not signal_identity or not external_oid:
            raise GlobalSlotReservationError("GLOBAL_SLOT_CLAIM_IDENTITY_MISSING")

        payload = {
            "reservation_version": "GLOBAL_SLOT_RESERVATION_V0.3",
            "candidate_id": candidate_id,
            "signal_identity": signal_identity,
            "external_oid": external_oid,
            "reserved_at_utc": _iso_now(),
            "expires_automatically": False,
            "blind_resend_allowed": False,
        }
        if _atomic_create(self.path, payload):
            return {**payload, "claim_status": "CLAIMED"}

        existing = _load(self.path)
        if (
            str(existing.get("candidate_id")) == candidate_id
            and str(existing.get("signal_identity")) == signal_identity
            and str(existing.get("external_oid")) == external_oid
        ):
            return {**existing, "claim_status": "RECOVERED_EXISTING_OWNER"}

        return {
            "claim_status": "OCCUPIED_BY_OTHER_SIGNAL",
            "owner": existing,
        }

    def release(
        self,
        *,
        signal_identity: str,
        reason: str,
    ) -> dict[str, Any]:
        existing = self.current()
        if existing is None:
            return {"release_status": "ALREADY_FREE"}
        if str(existing.get("signal_identity")) != str(signal_identity):
            raise GlobalSlotReservationError("GLOBAL_SLOT_RELEASE_OWNER_MISMATCH")
        allowed = {
            "PRE_SUBMIT_ABORT_CONFIRMED",
            "ENTRY_TERMINAL_NO_FILL_CONFIRMED",
            "POST_TRADE_RECONCILIATION_CONFIRMED",
        }
        if reason not in allowed:
            raise GlobalSlotReservationError("GLOBAL_SLOT_RELEASE_REASON_NOT_TERMINAL")
        self.path.unlink()
        return {
            "release_status": "RELEASED",
            "signal_identity": signal_identity,
            "reason": reason,
            "released_at_utc": _iso_now(),
        }


__all__ = [
    "GlobalSlotReservationV03",
    "GlobalSlotReservationError",
]
