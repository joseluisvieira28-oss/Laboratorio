from __future__ import annotations

from datetime import datetime, timezone
import json
import threading
import time
from typing import Any, Callable

from .etf_cme_watcher import ETFCMEPublicSignalWatcher
from .strategies.etf_cme_source import operational_signal_receipt_from_observations
from .timing import ExactTimingPolicy, TimingState


PREARM_EVENT = "ETF_CME_EXACT_RUNTIME_PREARM"
BOUNDARY_AS_OF_DATE = "2026-09-15"
DEFAULT_REFRESH_SECONDS = 300.0
FINAL_WAIT_SLICE_SECONDS = 0.25


def _utc_ms(value: datetime) -> int:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return int(value.astimezone(timezone.utc).timestamp() * 1000)


def _iso_ms(ms: int) -> str:
    return (
        datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_ms(value: str) -> int:
    return _utc_ms(datetime.fromisoformat(value.replace("Z", "+00:00")))


class ETFCMEExactRuntimeScheduler:
    """Dedicated exact-time scheduler for the frozen ETF-CME forward observer.

    Scientific timing is not changed. This scheduler only removes the coarse
    30-second general-loop cadence from the exact 00:00 UTC observation path.
    """

    def __init__(
        self,
        *,
        watcher: ETFCMEPublicSignalWatcher,
        policy: ExactTimingPolicy | None = None,
        refresh_seconds: float = DEFAULT_REFRESH_SECONDS,
        now_fn: Callable[[], datetime] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.watcher = watcher
        self.store = watcher.store
        self.policy = policy or ExactTimingPolicy()
        self.refresh_seconds = float(refresh_seconds)
        if self.refresh_seconds <= 0:
            raise ValueError("refresh_seconds must be > 0")
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self._sleep_fn = sleep_fn or time.sleep
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "status": "STARTING",
            "strategy_id": "ETF-CME-INSTFLOW-001",
            "boundary_as_of_date": BOUNDARY_AS_OF_DATE,
            "arm_lead_seconds": self.policy.arm_lead_seconds,
            "max_late_seconds": self.policy.max_late_seconds,
            "historical_backfill": False,
            "late_chase_allowed": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }

    def state(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

    def _set_state(self, **updates: Any) -> dict[str, Any]:
        with self._lock:
            self._state = {**self._state, **updates}
            return json.loads(json.dumps(self._state))

    def discover(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = _utc_ms(self._now_fn())
        now = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc)
        previous, current = self.watcher.source(timeout=self.watcher.timeout)
        receipt = operational_signal_receipt_from_observations(
            previous,
            current,
            now,
            timing_policy=self.policy,
        )
        target_ms = _parse_ms(receipt["information_safe_time_utc"])
        return {
            "previous": previous,
            "current": current,
            "receipt": receipt,
            "target_ms": target_ms,
            "target_utc": receipt["information_safe_time_utc"],
            "current_as_of_date": current.as_of_date,
        }

    def prearm(self, discovery: dict[str, Any], *, observed_ms: int | None = None) -> dict[str, Any]:
        if observed_ms is None:
            observed_ms = _utc_ms(self._now_fn())
        current = discovery["current"]
        if current.as_of_date <= BOUNDARY_AS_OF_DATE:
            return self._set_state(
                status="WAITING_NEW_CFTC_AS_OF_AFTER_BOUNDARY",
                current_as_of_date=current.as_of_date,
                target_utc=discovery["target_utc"],
            )

        receipt = discovery["receipt"]
        target_ms = int(discovery["target_ms"])
        timing = self.policy.receipt(
            now=datetime.fromtimestamp(observed_ms / 1000.0, tz=timezone.utc),
            target=datetime.fromtimestamp(target_ms / 1000.0, tz=timezone.utc),
        )
        state = TimingState(timing["timing_state"])
        if state not in (TimingState.ARMED, TimingState.DUE):
            return self._set_state(
                status="PREARM_NOT_IN_ARM_WINDOW",
                current_as_of_date=current.as_of_date,
                target_utc=discovery["target_utc"],
                timing_state=state.value,
            )

        key = f"ETF-CME-INSTFLOW-001:133741:{current.as_of_date}:{discovery['target_utc']}"
        payload = {
            "strategy_id": "ETF-CME-INSTFLOW-001",
            "watcher_id": "ETF-CME-INSTFLOW-001-CFTC-PUBLIC-FORWARD-WATCHER",
            "current_as_of_date": current.as_of_date,
            "target_utc": discovery["target_utc"],
            "prearmed_at_utc": _iso_ms(observed_ms),
            "direction": receipt["direction"],
            "signal_value": receipt["signal_value"],
            "source_dataset": "CFTC_LEGACY_FUTURES_ONLY_6DCA_AQWW",
            "source_contract_code": "133741",
            "used_as_forward_signal_evidence": False,
            "scientific_target_unchanged": True,
            "arm_lead_seconds": self.policy.arm_lead_seconds,
            "max_late_seconds": self.policy.max_late_seconds,
            "historical_backfill": False,
            "late_chase_allowed": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        appended = self.store.append_once(PREARM_EVENT, key, payload)
        return self._set_state(
            status="PREARMED_FOR_EXACT_TARGET",
            current_as_of_date=current.as_of_date,
            target_utc=discovery["target_utc"],
            prearm_evidence_inserted=bool(appended["inserted"]),
            timing_state=state.value,
        )

    def attempt_exact(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = _utc_ms(self._now_fn())
        result = self.watcher.run_once(now_ms=now_ms)
        return self._set_state(
            status="EXACT_ATTEMPT_COMPLETED",
            attempted_at_utc=_iso_ms(now_ms),
            watcher_status=result.get("status"),
            watcher_source_status=result.get("source_status"),
            signal_evidence_inserted=bool(result.get("signal_evidence_inserted")),
            missed_evidence_inserted=bool(result.get("missed_evidence_inserted")),
        )

    def run_loop(self) -> None:
        while True:
            try:
                now_ms = _utc_ms(self._now_fn())
                discovery = self.discover(now_ms=now_ms)
                current_as_of = discovery["current_as_of_date"]
                target_ms = int(discovery["target_ms"])

                if current_as_of <= BOUNDARY_AS_OF_DATE:
                    self._set_state(
                        status="WAITING_NEW_CFTC_AS_OF_AFTER_BOUNDARY",
                        current_as_of_date=current_as_of,
                        target_utc=discovery["target_utc"],
                    )
                    self._sleep_fn(self.refresh_seconds)
                    continue

                arm_at_ms = target_ms - int(self.policy.arm_lead_seconds * 1000)
                expires_ms = target_ms + int(self.policy.max_late_seconds * 1000)

                if now_ms < arm_at_ms:
                    self._set_state(
                        status="WAITING_EXACT_TARGET",
                        current_as_of_date=current_as_of,
                        target_utc=discovery["target_utc"],
                        arm_at_utc=_iso_ms(arm_at_ms),
                    )
                    sleep_seconds = min(
                        self.refresh_seconds,
                        max(0.05, (arm_at_ms - now_ms) / 1000.0),
                    )
                    self._sleep_fn(sleep_seconds)
                    continue

                if now_ms <= expires_ms:
                    self.prearm(discovery, observed_ms=now_ms)
                    while True:
                        actual_ms = _utc_ms(self._now_fn())
                        if actual_ms >= target_ms:
                            break
                        self._sleep_fn(
                            max(
                                0.01,
                                min(
                                    FINAL_WAIT_SLICE_SECONDS,
                                    (target_ms - actual_ms) / 1000.0,
                                ),
                            )
                        )
                    self.attempt_exact(now_ms=_utc_ms(self._now_fn()))
                    self._sleep_fn(self.refresh_seconds)
                    continue

                # A target that is already outside the immutable lateness budget
                # is never reconstructed by this scheduler.
                self._set_state(
                    status="TARGET_MISSED_DO_NOT_CHASE",
                    current_as_of_date=current_as_of,
                    target_utc=discovery["target_utc"],
                    observed_at_utc=_iso_ms(now_ms),
                    late_chase_allowed=False,
                )
                # Record the miss through the existing watcher exactly once.
                self.attempt_exact(now_ms=now_ms)
                self._sleep_fn(self.refresh_seconds)
            except Exception as exc:
                self._set_state(
                    status="FAIL_CLOSED",
                    error=f"{type(exc).__name__}:{exc}",
                    orders_created=False,
                    exchange_mutation_performed=False,
                    live_capital_enabled=False,
                )
                self._sleep_fn(self.refresh_seconds)
