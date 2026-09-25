from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


AUTHORIZED_DISPATCH_STATE = "ELIGIBLE_LOCAL_ARMING"
READY_ADAPTER_STATE = "READY"


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload


def _candidate_id(signal: dict[str, Any]) -> str:
    value = signal.get("candidate_id") or signal.get("strategy_id")
    if not value:
        raise RuntimeError("SIGNAL_CANDIDATE_ID_MISSING")
    return str(value)


def _direction(signal: dict[str, Any]) -> str:
    value = signal.get("direction")
    if not value:
        raise RuntimeError("SIGNAL_DIRECTION_MISSING")
    return str(value).upper()


def build_dispatch_plan(
    manifest_path: str | Path,
    signal_path: str | Path,
) -> dict[str, Any]:
    registry = _load_json(manifest_path)
    signal = _load_json(signal_path)

    if registry.get("deny_by_default") is not True:
        return {
            "pass": False,
            "status": "FAIL_CLOSED",
            "blockers": ["MANIFEST_REGISTRY_NOT_DENY_BY_DEFAULT"],
        }

    candidate_id = _candidate_id(signal)
    direction = _direction(signal)
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        return {
            "pass": False,
            "status": "FAIL_CLOSED",
            "candidate_id": candidate_id,
            "direction": direction,
            "blockers": ["MANIFEST_CANDIDATE_LIST_INVALID"],
        }

    matches = [
        row for row in candidates
        if isinstance(row, dict) and str(row.get("candidate_id")) == candidate_id
    ]
    if len(matches) != 1:
        return {
            "pass": False,
            "status": "FAIL_CLOSED",
            "candidate_id": candidate_id,
            "direction": direction,
            "blockers": ["CANDIDATE_MANIFEST_NOT_UNIQUE_OR_MISSING"],
        }

    candidate = matches[0]
    state = str(candidate.get("execution_state") or "")
    if state != AUTHORIZED_DISPATCH_STATE:
        return {
            "pass": False,
            "status": "EXECUTION_LOCKED",
            "candidate_id": candidate_id,
            "direction": direction,
            "execution_state": state,
            "authority_requirement": candidate.get("authority_requirement"),
            "blockers": [f"CANDIDATE_EXECUTION_STATE_{state or 'MISSING'}"],
        }

    routes = candidate.get("routes")
    if not isinstance(routes, dict):
        return {
            "pass": False,
            "status": "FAIL_CLOSED",
            "candidate_id": candidate_id,
            "direction": direction,
            "blockers": ["CANDIDATE_ROUTES_INVALID"],
        }

    route = routes.get(direction)
    if route is None:
        route = routes.get("ANY")
    if not isinstance(route, dict):
        return {
            "pass": False,
            "status": "FAIL_CLOSED",
            "candidate_id": candidate_id,
            "direction": direction,
            "blockers": ["NO_ROUTE_FOR_SIGNAL_DIRECTION"],
        }

    adapter_status = str(route.get("adapter_status") or "")
    if adapter_status != READY_ADAPTER_STATE:
        return {
            "pass": False,
            "status": "EXECUTION_LOCKED",
            "candidate_id": candidate_id,
            "direction": direction,
            "execution_state": state,
            "adapter_status": adapter_status,
            "blockers": [
                str(route.get("blocker") or f"ADAPTER_STATE_{adapter_status or 'MISSING'}")
            ],
        }

    executor_script = route.get("executor_script")
    if not executor_script:
        return {
            "pass": False,
            "status": "FAIL_CLOSED",
            "candidate_id": candidate_id,
            "direction": direction,
            "blockers": ["READY_ROUTE_WITHOUT_EXECUTOR_SCRIPT"],
        }

    signal_key = signal.get("immutable_signal_key")
    if not signal_key:
        return {
            "pass": False,
            "status": "FAIL_CLOSED",
            "candidate_id": candidate_id,
            "direction": direction,
            "blockers": ["IMMUTABLE_SIGNAL_KEY_MISSING"],
        }

    return {
        "pass": True,
        "status": "READY_TO_DELEGATE_TO_VALIDATED_EXECUTOR",
        "candidate_id": candidate_id,
        "direction": direction,
        "immutable_signal_key": str(signal_key),
        "execution_state": state,
        "venue": route.get("venue"),
        "symbol": route.get("symbol"),
        "margin_mode": route.get("margin_mode"),
        "leverage": route.get("leverage"),
        "max_notional_usdt": route.get("max_notional_usdt"),
        "executor_script": str(executor_script),
        "authority_requirement": candidate.get("authority_requirement"),
    }


def _required_path(value: str | None, blocker: str) -> str:
    if not value:
        raise RuntimeError(blocker)
    path = Path(value)
    if not path.exists():
        raise RuntimeError(f"{blocker}:{path}")
    return str(path)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Deny-by-default universal dispatcher for Crypto Lab candidate executors."
    )
    ap.add_argument("--manifests", required=True)
    ap.add_argument("--signal", required=True)
    ap.add_argument("--authority")
    ap.add_argument("--preflight")
    ap.add_argument("--risk-state")
    ap.add_argument("--receipt-root", default="live_receipts")
    ap.add_argument("--duplicate-lock-root", default="live_state/duplicate_locks")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    try:
        plan = build_dispatch_plan(args.manifests, args.signal)
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "blockers": [f"DISPATCH_PLAN_ERROR:{type(exc).__name__}:{exc}"],
        }, indent=2))
        return 2

    if not plan["pass"]:
        print(json.dumps(plan, indent=2))
        return 2

    try:
        authority = _required_path(args.authority, "LOCAL_CANDIDATE_AUTHORITY_REQUIRED")
        preflight = _required_path(args.preflight, "FRESH_PREFLIGHT_REQUIRED")
        risk_state = _required_path(args.risk_state, "FRESH_RISK_STATE_REQUIRED")
    except RuntimeError as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "candidate_id": plan["candidate_id"],
            "direction": plan["direction"],
            "blockers": [str(exc)],
        }, indent=2))
        return 3

    repo_root = Path(__file__).resolve().parents[2]
    executor = (repo_root / plan["executor_script"]).resolve()
    if not executor.exists():
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "blockers": [f"EXECUTOR_SCRIPT_MISSING:{executor}"],
        }, indent=2))
        return 4

    command = [
        sys.executable,
        str(executor),
        "--authority", authority,
        "--preflight", preflight,
        "--signal", str(Path(args.signal).resolve()),
        "--risk-state", risk_state,
        "--receipt-root", args.receipt_root,
        "--duplicate-lock-root", args.duplicate_lock_root,
    ]
    if args.execute:
        command.append("--execute")

    if not args.execute:
        print(json.dumps({
            "status": "READY_TO_DELEGATE_NOT_EXECUTED",
            "plan": plan,
            "command_target": str(executor),
            "note": "Underlying validated executor retains all candidate-specific authority, risk, kill-switch and venue checks.",
        }, indent=2))
        return 0

    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
