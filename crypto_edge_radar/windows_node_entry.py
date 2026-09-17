from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from radar.__main__ import main


BUILD_ID = "v0.7-win-registry-materialize-v1"


def _resource_path(name: str) -> str:
    """Resolve a packaged resource in both source and PyInstaller onefile modes."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return str(Path(bundle_root) / name)
    return str(Path(__file__).resolve().parent / name)


def _verify_registry_file(registry_path: str) -> tuple[dict, dict]:
    if not os.path.isfile(registry_path):
        raise RuntimeError(f"deployment registry missing: {registry_path}")
    payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    candidates = payload.get("candidates") or []
    ids = {
        str(item.get("strategy_id"))
        for item in candidates
        if isinstance(item, dict) and item.get("strategy_id")
    }
    required = "ETF-CME-INSTFLOW-001"
    if required not in ids:
        raise RuntimeError(f"deployment registry missing required strategy: {required}")
    state = {
        "status": "PASS",
        "build_id": BUILD_ID,
        "registry_version": payload.get("registry_version"),
        "candidate_count": len(candidates),
        "required_strategy_present": True,
    }
    return payload, state


def _materialize_registry(payload: dict) -> str:
    """Write a stable runtime copy instead of depending on PyInstaller _MEIPASS."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    runtime_registry = data_dir / "deployment_registry_v1.json"
    tmp_path = runtime_registry.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(runtime_registry)
    return str(runtime_registry.resolve())


def run() -> int:
    os.environ.setdefault("RADAR_PROVIDER", "mexc_futures_public")
    os.environ.setdefault("RADAR_UNIVERSE_MODE", "core5")
    os.environ.setdefault("RADAR_DB", os.path.join("data", "radar_evidence.sqlite3"))
    os.environ.setdefault("RADAR_STATUS", os.path.join("data", "radar_status.json"))
    os.environ.setdefault("RADAR_NOTIFICATIONS", os.path.join("data", "radar_notifications.jsonl"))
    os.environ.setdefault("RADAR_BUILD_ID", BUILD_ID)
    os.makedirs("data", exist_ok=True)

    bundled_registry = _resource_path("deployment_registry_v1.json")
    try:
        payload, package_state = _verify_registry_file(bundled_registry)
        runtime_registry = _materialize_registry(payload)
        _, runtime_state = _verify_registry_file(runtime_registry)
        package_state["runtime_registry_materialized"] = True
        package_state["runtime_candidate_count"] = runtime_state["candidate_count"]
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "build_id": BUILD_ID, "error": str(exc)}, sort_keys=True))
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
            runtime_registry,
        ]
    )


if __name__ == "__main__":
    sys.exit(run())
