from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError

from .ema6h_archive_recovery import BinanceOfficialKlineArchiveRecovery
from .ema6h_regime_watcher import EMA6HRegimeForwardWatcher
from .strategies.ema6h_50x200_regime_forward import (
    latest_certifiable_signal_close_ms,
    utc_iso,
)


class EMA6HArchiveRecoverySidecar:
    sidecar_id = "EMA6H-50X200-REGIME-ARCHIVE-RECOVERY-V0.1"

    def __init__(
        self,
        *,
        store: Any,
        timeout: int = 15,
        archive: BinanceOfficialKlineArchiveRecovery | None = None,
        watcher: EMA6HRegimeForwardWatcher | None = None,
    ) -> None:
        self.archive = archive or BinanceOfficialKlineArchiveRecovery(
            timeout=timeout
        )
        self.watcher = watcher or EMA6HRegimeForwardWatcher(
            store=store,
            feed=self.archive,
        )

    @staticmethod
    def _today_start_ms(now_ms: int) -> int:
        now = datetime.fromtimestamp(
            now_ms / 1000.0,
            tz=timezone.utc,
        )
        return int(
            datetime(
                now.year,
                now.month,
                now.day,
                tzinfo=timezone.utc,
            ).timestamp()
            * 1000
        )

    def run_once(
        self,
        *,
        now_ms: int,
    ) -> dict[str, Any]:
        today_start_ms = self._today_start_ms(now_ms)
        scientific_now_ms = today_start_ms - 1
        recovery_boundary_ms = latest_certifiable_signal_close_ms(
            scientific_now_ms
        )

        base = {
            "sidecar_id": self.sidecar_id,
            "mode": "PUBLIC_ARCHIVE_RECOVERY_T_PLUS_1",
            "provider": self.archive.provider,
            "availability_now_utc": utc_iso(now_ms),
            "scientific_cutoff_now_utc": utc_iso(scientific_now_ms),
            "recovery_cutoff_signal_close_utc": (
                utc_iso(recovery_boundary_ms)
                if recovery_boundary_ms is not None
                else None
            ),
            "same_day_recovery_allowed": False,
            "science_changed": False,
            "outcomes_changed": False,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }

        if recovery_boundary_ms is None:
            return {
                **base,
                "status": "WAITING_FIRST_ARCHIVE_ELIGIBLE_BOUNDARY",
                "evidence_advanced": False,
            }

        self.archive.availability_now_ms = now_ms
        try:
            result = self.watcher.run_once(
                now_ms=scientific_now_ms
            )
        except HTTPError as exc:
            if exc.code == 404:
                return {
                    **base,
                    "status": "WAITING_ARCHIVE_T_PLUS_1_PUBLICATION",
                    "http_status": 404,
                    "evidence_advanced": False,
                }
            return {
                **base,
                "status": "ARCHIVE_RECOVERY_FAIL_CLOSED",
                "error": f"{type(exc).__name__}:{exc}",
                "evidence_advanced": False,
            }
        except Exception as exc:
            return {
                **base,
                "status": "ARCHIVE_RECOVERY_FAIL_CLOSED",
                "error": f"{type(exc).__name__}:{exc}",
                "evidence_advanced": False,
            }

        advanced = bool(
            int(result.get("new_boundaries") or 0)
            or int(result.get("inserted_signals") or 0)
            or int(result.get("inserted_resolutions") or 0)
        )
        receipt_count = len(self.archive.last_receipts)
        return {
            **base,
            "status": (
                "ARCHIVE_RECOVERY_OK"
                if result.get("status") == "OK"
                else "ARCHIVE_RECOVERY_FAIL_CLOSED"
            ),
            "canonical_watcher_status": result.get("status"),
            "evidence_advanced": advanced,
            "new_boundaries": int(result.get("new_boundaries") or 0),
            "inserted_signals": int(result.get("inserted_signals") or 0),
            "inserted_resolutions": int(
                result.get("inserted_resolutions") or 0
            ),
            "missing_boundaries": int(
                result.get("missing_boundaries") or 0
            ),
            "archive_period_receipts": receipt_count,
            "archive_all_checksums_verified": (
                all(
                    receipt.checksum_verified
                    for receipt in self.archive.last_receipts
                )
                if receipt_count
                else None
            ),
        }
