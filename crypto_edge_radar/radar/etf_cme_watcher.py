from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .evidence import EvidenceStore, PostgresEvidenceStore
from .strategies.etf_cme_source import (
    fetch_latest_two,
    operational_signal_receipt_from_observations,
)


Store = EvidenceStore | PostgresEvidenceStore
STRATEGY_ID = "ETF-CME-INSTFLOW-001"
WATCHER_ID = "ETF-CME-INSTFLOW-001-CFTC-PUBLIC-FORWARD-WATCHER"
SOURCE_EVENT = "ETF_CME_CFTC_SOURCE_OBSERVATION"
SIGNAL_EVENT = "ETF_CME_FORWARD_SIGNAL_OBSERVATION"
MISSED_EVENT = "ETF_CME_MISSED_EXPECTED_OBSERVATION"


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _key(as_of_date: str) -> str:
    return f"{STRATEGY_ID}:133741:{as_of_date}"


class ETFCMEPublicSignalWatcher:
    """Public, replay-safe observer of the exact frozen CFTC signal.

    A late runtime may record that an observation was missed, but it must never
    reconstruct that observation as prospective forward signal evidence.
    """

    def __init__(
        self,
        *,
        store: Store,
        source: Callable[..., tuple[Any, Any]] = fetch_latest_two,
        timeout: int = 15,
    ) -> None:
        self.store = store
        self.source = source
        self.timeout = timeout

    def _payloads(self, event_type: str) -> list[dict[str, Any]]:
        return self.store.read_payloads(event_type)

    def run_once(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        attempted = _iso(now_ms)
        try:
            previous, current = self.source(timeout=self.timeout)
        except Exception as exc:
            return {
                "watcher_id": WATCHER_ID,
                "strategy_id": STRATEGY_ID,
                "status": "FAIL_CLOSED",
                "source_status": "SOURCE_UNAVAILABLE",
                "last_source_attempt_utc": attempted,
                "error": f"{type(exc).__name__}:{exc}",
                "authenticated_exchange_api_used": False,
                "order_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            }

        now = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc)
        receipt = operational_signal_receipt_from_observations(previous, current, now)
        key = _key(current.as_of_date)
        source_payload = {
            **receipt,
            "watcher_id": WATCHER_ID,
            "event_key": key,
            "source_dataset": "CFTC_LEGACY_FUTURES_ONLY_6DCA_AQWW",
            "source_contract_code": "133741",
            "source_attempt_utc": attempted,
            "source_success_utc": attempted,
            "used_as_forward_signal_evidence": False,
            "authenticated_exchange_api_used": False,
            "order_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        source_append = self.store.append_once(SOURCE_EVENT, key, source_payload)

        signal_inserted = False
        missed_inserted = False
        if receipt["state"] == "OPERATIONAL_ENTRY_DUE":
            signal_payload = {
                **source_payload,
                "observed_at_utc": attempted,
                "used_as_forward_signal_evidence": True,
                "prospective_observation": True,
            }
            signal_inserted = self.store.append_once(SIGNAL_EVENT, key, signal_payload)["inserted"]
            status = "SIGNAL_OBSERVED"
        elif receipt["state"] == "ENTRY_WINDOW_PASSED_DO_NOT_CHASE":
            observed = any(p.get("event_key") == key for p in self._payloads(SIGNAL_EVENT))
            if not observed:
                missed_payload = {
                    **source_payload,
                    "missed_at_utc": attempted,
                    "reason": "RUNTIME_OR_SOURCE_NOT_PRESENT_INSIDE_FROZEN_OPERATIONAL_WINDOW",
                    "late_reconstruction_forbidden": True,
                    "used_as_forward_signal_evidence": False,
                }
                missed_inserted = self.store.append_once(MISSED_EVENT, key, missed_payload)["inserted"]
                status = "MISSED_EXPECTED_OBSERVATION_NO_CHASE"
            else:
                status = "OBSERVATION_ALREADY_PERSISTED"
        else:
            status = receipt["state"]

        signals = self._payloads(SIGNAL_EVENT)
        missed = self._payloads(MISSED_EVENT)
        duplicates = (0 if source_append["inserted"] else 1)
        return {
            "watcher_id": WATCHER_ID,
            "strategy_id": STRATEGY_ID,
            "status": status,
            "source_status": "OK",
            "last_source_attempt_utc": attempted,
            "last_source_success_utc": attempted,
            "last_signal_observation_utc": max(
                (str(p.get("observed_at_utc")) for p in signals if p.get("observed_at_utc")),
                default=None,
            ),
            "next_expected_source_window": receipt["information_safe_time_utc"],
            "source_delay_seconds": max(
                0.0,
                (now - datetime.fromisoformat(receipt["information_safe_time_utc"].replace("Z", "+00:00"))).total_seconds(),
            ),
            "signal_direction": receipt["direction"],
            "immutable_signal_key": key,
            "duplicate_count": duplicates,
            "missed_expected_observation_count": len(missed),
            "evidence_persisted": source_append["inserted"] or signal_inserted or missed_inserted,
            "signal_evidence_inserted": signal_inserted,
            "missed_evidence_inserted": missed_inserted,
            "evidence_backend": self.store.backend,
            "authenticated_exchange_api_used": False,
            "order_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
