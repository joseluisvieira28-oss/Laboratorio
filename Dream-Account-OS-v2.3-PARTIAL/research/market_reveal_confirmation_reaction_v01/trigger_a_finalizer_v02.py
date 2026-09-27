"""One-shot Trigger-A finalizer for MRCR H02 V0.2.

Pipeline:
official live probe -> annual plan -> implementation manifest ->
final_binding_preflight_v02 -> target-locked protocol.

Hard stop:
This module does NOT create TARGET_OBSERVATION_OPEN authority, does NOT inspect
outcomes, and does NOT start market-data capture or trading.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

from annual_plan_builder_v02 import build_annual_plan_v02_from_live_status
from final_binding_preflight_v02 import run_final_binding_preflight_v02
from freeze_manifest import (
    build_implementation_manifest,
    canonical_json_bytes,
    verify_implementation_manifest,
)
from official_2027_calendar_live_probe import fetch_official_calendar_status


MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parents[1]

RULESET_PATH = MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json"
H02_AUTHORITY_PATH = MODULE_DIR / "H02_DESIGN_FREEZE_AUTHORITY_V01.json"
FILESET_PATH = MODULE_DIR / "IMPLEMENTATION_FREEZE_FILESET_V01.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )


def _parse_utc(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _utc_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_receipt(value: Mapping[str, Any]) -> str:
    clean = json.loads(json.dumps(value))
    clean["receipt_sha256"] = None
    return hashlib.sha256(canonical_json_bytes(clean)).hexdigest()


def run_trigger_a_finalizer_v02(
    *,
    implementation_head_sha: str,
    output_dir: Path,
    live_status: Mapping[str, Any] | None = None,
    protocol_frozen_at_utc: str | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    ruleset = _load_json(RULESET_PATH)
    h02_authority = _load_json(H02_AUTHORITY_PATH)
    fileset = _load_json(FILESET_PATH)

    if (
        not isinstance(implementation_head_sha, str)
        or len(implementation_head_sha) != 40
        or any(ch not in "0123456789abcdefABCDEF" for ch in implementation_head_sha)
    ):
        raise ValueError("implementation_head_sha must be a 40-character hex SHA")

    status = (
        dict(live_status)
        if live_status is not None
        else fetch_official_calendar_status()
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        output_dir / "MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01.json",
        status,
    )

    if (
        status.get("status") != "READY_FOR_V02_ANNUAL_PLAN"
        or status.get("annual_plan_trigger_ready_v02") is not True
    ):
        receipt = {
            "document_type": "MRCR_H02_TRIGGER_A_FINALIZER_V02",
            "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
            "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
            "status": "BLOCKED_OFFICIAL_ANNUAL_PLAN_NOT_READY",
            "implementation_head_sha": implementation_head_sha,
            "live_status_checked_at_utc": status.get("checked_at_utc"),
            "annual_plan_sha256": None,
            "implementation_manifest_sha256": None,
            "protocol_fingerprint_sha256": None,
            "target_observation_authorized": False,
            "outcomes_authorized": False,
            "orders_enabled": False,
            "promotion_credit": "NONE",
            "receipt_sha256": None,
        }
        receipt["receipt_sha256"] = _sha256_receipt(receipt)
        _write_json(
            output_dir / "MRCR_TRIGGER_A_FINALIZER_RECEIPT_V02.json",
            receipt,
        )
        return receipt

    annual_plan = build_annual_plan_v02_from_live_status(
        live_status=status,
        ruleset=ruleset,
    )

    relative_paths = fileset.get("files")
    if not isinstance(relative_paths, list) or not relative_paths:
        raise RuntimeError("canonical implementation fileset is empty")

    implementation_manifest = build_implementation_manifest(
        root=project_root,
        relative_paths=[str(path) for path in relative_paths],
        implementation_head_sha=implementation_head_sha.lower(),
    )
    if not verify_implementation_manifest(
        root=project_root,
        manifest=implementation_manifest,
    ):
        raise RuntimeError("implementation manifest self-verification failed")

    calendar_frozen_at_utc = str(status.get("checked_at_utc") or "")
    if not calendar_frozen_at_utc:
        raise RuntimeError("live status missing checked_at_utc")
    calendar_frozen = _parse_utc(calendar_frozen_at_utc)

    if protocol_frozen_at_utc is None:
        protocol_frozen = datetime.now(timezone.utc)
    else:
        protocol_frozen = _parse_utc(protocol_frozen_at_utc)
    if protocol_frozen < calendar_frozen:
        raise ValueError("protocol freeze cannot predate official calendar retrieval")

    preflight = run_final_binding_preflight_v02(
        ruleset=ruleset,
        annual_plan=annual_plan,
        implementation_manifest=implementation_manifest,
        h02_authority_receipt=h02_authority,
        calendar_frozen_at_utc=_utc_z(calendar_frozen),
        protocol_frozen_at_utc=_utc_z(protocol_frozen),
    )
    if not preflight.ready_for_target_open_authority or preflight.protocol is None:
        raise RuntimeError(
            "TRIGGER_A_FINAL_BINDING_PREFLIGHT_FAILED:"
            + ",".join(preflight.blockers)
        )

    protocol = preflight.protocol
    if protocol.get("status") != "FROZEN_PRETARGET_PROTOCOL__TARGET_LOCKED":
        raise RuntimeError("finalizer produced non-target-locked protocol")
    if protocol.get("governance", {}).get("target_observation_authorized") is not False:
        raise RuntimeError("finalizer must not authorize target observation")

    _write_json(
        output_dir / "MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json",
        annual_plan,
    )
    _write_json(
        output_dir / "MRCR_IMPLEMENTATION_MANIFEST_TRIGGER_A_V02.json",
        implementation_manifest,
    )
    _write_json(
        output_dir / "MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json",
        protocol,
    )

    receipt = {
        "document_type": "MRCR_H02_TRIGGER_A_FINALIZER_V02",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "status": "PASS_TARGET_LOCKED_PROTOCOL_FROZEN",
        "implementation_head_sha": implementation_head_sha.lower(),
        "live_status_checked_at_utc": calendar_frozen_at_utc,
        "calendar_frozen_at_utc": _utc_z(calendar_frozen),
        "protocol_frozen_at_utc": _utc_z(protocol_frozen),
        "annual_plan_sha256": annual_plan["annual_plan_sha256"],
        "implementation_manifest_sha256": implementation_manifest["manifest_sha256"],
        "protocol_fingerprint_sha256": protocol["freeze"]["protocol_fingerprint_sha256"],
        "ready_for_separate_target_open_authority": True,
        "target_observation_authorized": False,
        "outcomes_authorized": False,
        "orders_enabled": False,
        "live_trading_authorized": False,
        "main_merge_authorized": False,
        "promotion_credit": "NONE",
        "receipt_sha256": None,
    }
    receipt["receipt_sha256"] = _sha256_receipt(receipt)
    _write_json(
        output_dir / "MRCR_TRIGGER_A_FINALIZER_RECEIPT_V02.json",
        receipt,
    )
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--implementation-head-sha",
        default=os.environ.get("GITHUB_SHA"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--live-status", type=Path)
    parser.add_argument("--protocol-frozen-at-utc")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.implementation_head_sha:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "failure_reason": "IMPLEMENTATION_HEAD_SHA_REQUIRED",
        }))
        return 2

    try:
        live_status = (
            _load_json(args.live_status)
            if args.live_status is not None
            else None
        )
        receipt = run_trigger_a_finalizer_v02(
            implementation_head_sha=args.implementation_head_sha,
            output_dir=args.output_dir,
            live_status=live_status,
            protocol_frozen_at_utc=args.protocol_frozen_at_utc,
        )
    except Exception as exc:
        print(json.dumps({
            "document_type": "MRCR_H02_TRIGGER_A_FINALIZER_V02",
            "status": "FAIL_CLOSED",
            "error_class": type(exc).__name__,
            "failure_reason": str(exc),
            "target_observation_authorized": False,
            "outcomes_authorized": False,
            "orders_enabled": False,
        }, sort_keys=True))
        return 2

    print(json.dumps(receipt, sort_keys=True))
    return (
        0
        if receipt["status"] == "PASS_TARGET_LOCKED_PROTOCOL_FROZEN"
        else 3
    )


if __name__ == "__main__":
    sys.exit(main())
