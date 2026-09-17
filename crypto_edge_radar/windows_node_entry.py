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


def run() -> int:
    os.environ.setdefault("RADAR_PROVIDER", "mexc_futures_public")
    os.environ.setdefault("RADAR_UNIVERSE_MODE", "core5")
    os.environ.setdefault("RADAR_DB", os.path.join("data", "radar_evidence.sqlite3"))
    os.environ.setdefault("RADAR_STATUS", os.path.join("data", "radar_status.json"))
    os.environ.setdefault("RADAR_NOTIFICATIONS", os.path.join("data", "radar_notifications.jsonl"))
    os.makedirs("data", exist_ok=True)

    registry_path = _resource_path("deployment_registry_v1.json")
    if not os.path.isfile(registry_path):
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "error": "bundled deployment registry missing",
                    "expected_path": registry_path,
                },
                sort_keys=True,
            )
        )
        return 2

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
