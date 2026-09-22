from __future__ import annotations

import base64
import csv
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

from .evidence import EvidenceStore, PostgresEvidenceStore
from .ced1d_render_shadow_collector_v03 import FIRST_SIGNAL_DAY

Store = EvidenceStore | PostgresEvidenceStore

EXPECTED_RUNNER_SHA256 = "df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958"
RECEIPT_EVENT = "CED1D_RENDER_SHADOW_V03_RECEIPT"
LEDGER_EVENT = "CED1D_RENDER_SHADOW_V03_EVENT"
FAILURE_EVENT = "CED1D_RENDER_SHADOW_V03_FAILURE"
FIRST_SIGNAL_COMPLETION_UTC = "2026-09-23T00:00:00Z"
FIRST_REFERENCE_ENTRY_UTC = "2026-09-23T00:01:00Z"


class CED1DRenderShadowRuntimeError(RuntimeError):
    pass


def latest_mature_signal_day(today_utc: date) -> date | None:
    through = today_utc - timedelta(days=3)
    return through if through >= FIRST_SIGNAL_DAY else None


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _decode_runner_asset(target: Path) -> str:
    source = _root() / "assets" / "CED-1D-V1-RUNNER-FREEZE-V0.3.zip.b64"
    compact = "".join(source.read_text(encoding="utf-8").split())
    raw = base64.b64decode(compact, validate=True)
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_RUNNER_SHA256:
        raise CED1DRenderShadowRuntimeError(
            f"V03_RUNNER_ASSET_SHA_MISMATCH:{sha}:{EXPECTED_RUNNER_SHA256}"
        )
    target.write_bytes(raw)
    return sha


def _read_ledger(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _validate_complete_result(
    receipt: dict[str, Any],
    ledger: list[dict[str, str]],
    through: date,
) -> None:
    if receipt.get("status") != "SHADOW_COLLECTION_COMPLETE":
        raise CED1DRenderShadowRuntimeError(
            f"COLLECTOR_NOT_COMPLETE:{receipt.get('status')}:{receipt.get('error')}"
        )
    if receipt.get("candidate") != "CED1D-0031":
        raise CED1DRenderShadowRuntimeError("CANDIDATE_IDENTITY_MISMATCH")
    if receipt.get("first_eligible_signal_day") != FIRST_SIGNAL_DAY.isoformat():
        raise CED1DRenderShadowRuntimeError("FIRST_SIGNAL_DAY_MISMATCH")
    if receipt.get("first_eligible_signal_completion") != FIRST_SIGNAL_COMPLETION_UTC:
        raise CED1DRenderShadowRuntimeError("FIRST_SIGNAL_COMPLETION_MISMATCH")
    if receipt.get("through_signal_day") != through.isoformat():
        raise CED1DRenderShadowRuntimeError("THROUGH_SIGNAL_DAY_MISMATCH")
    gov = receipt.get("governance") or {}
    for key in (
        "pre_boundary_performance_backfill",
        "live_trading",
        "orders",
        "wallets",
        "exchange_mutation",
        "authenticated_trading_endpoints",
        "parameter_changes",
        "merge_main",
    ):
        if gov.get(key) is not False:
            raise CED1DRenderShadowRuntimeError(f"GOVERNANCE_FIREWALL_FAIL:{key}")
    for row in ledger:
        signal_day = row.get("signal_day")
        if not signal_day:
            raise CED1DRenderShadowRuntimeError("LEDGER_SIGNAL_DAY_MISSING")
        if date.fromisoformat(signal_day) < FIRST_SIGNAL_DAY:
            raise CED1DRenderShadowRuntimeError(
                f"PRE_MIGRATION_EVENT_FORBIDDEN:{signal_day}"
            )
        event_id = row.get("event_id")
        if not event_id or not event_id.startswith("CED1D-0031:"):
            raise CED1DRenderShadowRuntimeError("LEDGER_EVENT_IDENTITY_MISMATCH")


class CED1DRenderShadowRunner:
    """Runs the frozen V0.3 collector at most once per mature through-signal-day."""

    def __init__(self, *, store: Store, subprocess_timeout_seconds: int = 1800) -> None:
        self.store = store
        self.subprocess_timeout_seconds = int(subprocess_timeout_seconds)
        if self.subprocess_timeout_seconds < 60:
            raise ValueError("CED1D subprocess timeout must be >=60 seconds")

    def _existing(self, through: date) -> dict[str, Any] | None:
        target = through.isoformat()
        for payload in self.store.read_payloads(RECEIPT_EVENT):
            if payload.get("through_signal_day") == target:
                return payload
        return None

    def run_once(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        now = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc)
        through = latest_mature_signal_day(now.date())
        safety = {
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
            "retrospective_backfill": False,
        }
        if through is None:
            return {
                "strategy_id": "CED1D-0031",
                "status": "WAITING_SOURCE_READINESS",
                "migration_freeze_utc": "2026-09-22T07:25:00Z",
                "first_eligible_signal_day": FIRST_SIGNAL_DAY.isoformat(),
                "first_eligible_signal_completion": FIRST_SIGNAL_COMPLETION_UTC,
                "first_eligible_reference_entry": FIRST_REFERENCE_ENTRY_UTC,
                "latest_mature_signal_day": None,
                **safety,
            }

        existing = self._existing(through)
        if existing is not None:
            return {
                "strategy_id": "CED1D-0031",
                "status": "ALREADY_PERSISTED",
                "latest_mature_signal_day": through.isoformat(),
                "receipt_fingerprint": existing.get("fingerprint"),
                "metrics": existing.get("metrics"),
                **safety,
            }

        root = _root()
        activation = root / "authorities" / "CED1D_0031_RENDER_SHADOW_ACTIVATION_V0.3.json"
        collector = root / "radar" / "ced1d_render_shadow_collector_v03.py"
        if not activation.exists() or not collector.exists():
            raise CED1DRenderShadowRuntimeError("PINNED_MIGRATION_FILE_MISSING")

        try:
            with tempfile.TemporaryDirectory(prefix="ced1d_v03_") as td:
                temp = Path(td)
                runner_zip = temp / "CED-1D-V1-RUNNER-FREEZE-V0.3.zip"
                runner_sha = _decode_runner_asset(runner_zip)
                output = temp / "output"
                cmd = [
                    sys.executable,
                    str(collector),
                    "--activation", str(activation),
                    "--v03-runner-zip", str(runner_zip),
                    "--through-signal-day", through.isoformat(),
                    "--output", str(output),
                ]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.subprocess_timeout_seconds,
                    check=False,
                )
                receipt_path = output / "CED1D_0031_RENDER_SHADOW_RECEIPT_V0.3.json"
                if not receipt_path.exists():
                    raise CED1DRenderShadowRuntimeError(
                        f"COLLECTOR_RECEIPT_MISSING:returncode={proc.returncode}:"
                        f"stderr={proc.stderr[-500:]}"
                    )
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                if proc.returncode != 0:
                    failure = {
                        "strategy_id": "CED1D-0031",
                        "through_signal_day": through.isoformat(),
                        "receipt": receipt,
                        "returncode": proc.returncode,
                        "runner_sha256": runner_sha,
                        **safety,
                    }
                    self.store.append_once(
                        FAILURE_EVENT,
                        f"CED1D-0031:V0.3:FAIL:{through.isoformat()}",
                        failure,
                    )
                    raise CED1DRenderShadowRuntimeError(
                        f"COLLECTOR_FAIL_CLOSED:{receipt.get('error')}"
                    )

                ledger_path = output / "CED1D_0031_RENDER_SHADOW_LEDGER_V0.3.csv"
                ledger = _read_ledger(ledger_path)
                _validate_complete_result(receipt, ledger, through)

                inserted_events = 0
                duplicate_events = 0
                for row in ledger:
                    event_id = str(row["event_id"])
                    payload = {
                        "strategy_id": "CED1D-0031",
                        "migration_version": "V0.3",
                        "event": row,
                        **safety,
                    }
                    result = self.store.append_once(
                        LEDGER_EVENT,
                        f"CED1D-0031:V0.3:{event_id}",
                        payload,
                    )
                    if result["inserted"]:
                        inserted_events += 1
                    else:
                        duplicate_events += 1

                ledger_sha = (
                    hashlib.sha256(ledger_path.read_bytes()).hexdigest()
                    if ledger_path.exists()
                    else None
                )
                persisted = {
                    **receipt,
                    "migration_version": "V0.3",
                    "runtime": "RENDER_FRANKFURT_CANONICAL",
                    "runner_sha256": runner_sha,
                    "ledger_sha256": ledger_sha,
                    "ledger_rows": len(ledger),
                    "inserted_events": inserted_events,
                    "duplicate_events": duplicate_events,
                    **safety,
                }
                result = self.store.append_once(
                    RECEIPT_EVENT,
                    f"CED1D-0031:V0.3:{through.isoformat()}",
                    persisted,
                )
                if not result["inserted"]:
                    raise CED1DRenderShadowRuntimeError(
                        "RECEIPT_RACE_DUPLICATE_FAIL_CLOSED"
                    )
                return {
                    "strategy_id": "CED1D-0031",
                    "status": "SHADOW_COLLECTION_COMPLETE",
                    "latest_mature_signal_day": through.isoformat(),
                    "ledger_rows": len(ledger),
                    "inserted_events": inserted_events,
                    "duplicate_events": duplicate_events,
                    "receipt_fingerprint": receipt.get("fingerprint"),
                    "metrics": receipt.get("metrics"),
                    **safety,
                }
        except subprocess.TimeoutExpired as exc:
            raise CED1DRenderShadowRuntimeError(
                f"COLLECTOR_TIMEOUT:{self.subprocess_timeout_seconds}"
            ) from exc
