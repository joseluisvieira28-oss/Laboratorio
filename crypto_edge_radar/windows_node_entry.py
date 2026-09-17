from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from radar.__main__ import main


def _resource_path(name: str) -> str:
    """Resolve a packaged resource in both source and PyInstaller onefile modes."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return str(Path(bundle_root) / name)
    return str(Path(__file__).resolve().parent / name)


def _verify_bundled_registry(registry_path: str) -> dict:
    if not os.path.isfile(registry_path):
        raise RuntimeError(f"bundled deployment registry missing: {registry_path}")
    payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    candidates = payload.get("candidates") or []
    ids = {
        str(item.get("strategy_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("strategy_id")
    }
    required = "ETF-CME-INSTFLOW-001"
    if required not in ids:
        raise RuntimeError(f"bundled deployment registry missing required strategy: {required}")
    return {
        "status": "PASS",
        "registry_version": payload.get("registry_version"),
        "candidate_count": len(candidates),
        "required_strategy_present": True,
    }


def run() -> int:
    os.environ.setdefault("RADAR_PROVIDER", "mexc_futures_public")
    os.environ.setdefault("RADAR_UNIVERSE_MODE", "core5")
    os.environ.setdefault("RADAR_DB", os.path.join("data", "radar_evidence.sqlite3"))
    os.environ.setdefault("RADAR_STATUS", os.path.join("data", "radar_status.json"))
    os.environ.setdefault("RADAR_NOTIFICATIONS", os.path.join("data", "radar_notifications.jsonl"))
    os.makedirs("data", exist_ok=True)

    registry_path = _resource_path("deployment_registry_v1.json")
    try:
        package_state = _verify_bundled_registry(registry_path)
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2

    if os.getenv("RADAR_PACKAGING_SELFTEST") == "1":
        print(json.dumps(package_state, sort_keys=True))
        return 0

    return main(
        [
            "local-node",
            "--port",
            "8787",
            "--interval",
            "30",
            "--registry",
            registry_path,
        ]
    )


if __name__ == "__main__":
    sys.exit(run())
