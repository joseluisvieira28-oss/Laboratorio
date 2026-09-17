from __future__ import annotations

import os
import sys

from radar.__main__ import main


def run() -> int:
    os.environ.setdefault("RADAR_PROVIDER", "mexc_futures_public")
    os.environ.setdefault("RADAR_UNIVERSE_MODE", "core5")
    os.environ.setdefault("RADAR_DB", os.path.join("data", "radar_evidence.sqlite3"))
    os.environ.setdefault("RADAR_STATUS", os.path.join("data", "radar_status.json"))
    os.environ.setdefault("RADAR_NOTIFICATIONS", os.path.join("data", "radar_notifications.jsonl"))
    os.makedirs("data", exist_ok=True)
    return main(["local-node", "--port", "8787", "--interval", "30"])


if __name__ == "__main__":
    sys.exit(run())
