from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import threading
import traceback

from radar.__main__ import main
from radar.dh03_12h_local import DH03LocalCollector, default_paths
from radar.bnb_local import BNBLocalFastMonitor
from radar.bnb_launchpool_watcher import BNBLaunchpoolForwardShadowWatcher, BinanceOfficialLaunchpoolSource
from radar.strategies.bnb_launchpool_demand import BinanceSpotBNBBTCKlineFeed
from radar.evidence import EvidenceStore


BUILD_ID = "v0.11-win-five-engine-dh03-bnb-local"


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
    dh03 = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
    if dh03 not in ids:
        raise RuntimeError(f"deployment registry missing DH03 local collector strategy: {dh03}")
    state = {
        "status": "PASS",
        "build_id": BUILD_ID,
        "registry_version": payload.get("registry_version"),
        "candidate_count": len(candidates),
        "required_strategy_present": True,
        "dh03_strategy_present": True,
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




def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _run_dh03_background() -> None:
    status_path = Path("data") / "dh03_local_status.json"
    try:
        market_db, evidence_db = default_paths()
        collector = DH03LocalCollector(data_db=market_db, evidence_db=evidence_db)
        _write_json_atomic(status_path, {
            "status": "BOOTSTRAPPING",
            "build_id": BUILD_ID,
            "market_db": market_db,
            "evidence_db": evidence_db,
            "orders_created": False,
            "live_capital_enabled": False,
        })
        bootstrap = collector.bootstrap()
        _write_json_atomic(status_path, {
            "status": "COLLECTING",
            "build_id": BUILD_ID,
            "bootstrap": bootstrap,
            "market_db": market_db,
            "evidence_db": evidence_db,
            "orders_created": False,
            "live_capital_enabled": False,
        })
        collector.run_forever()
    except Exception as exc:
        _write_json_atomic(status_path, {
            "status": "FAIL_CLOSED",
            "build_id": BUILD_ID,
            "error": f"{type(exc).__name__}:{exc}",
            "traceback": traceback.format_exc(limit=8),
            "orders_created": False,
            "live_capital_enabled": False,
        })


def _run_bnb_background() -> None:
    status_path = Path("data") / "bnb_local_status.json"
    try:
        evidence_path = str((Path("data") / "bnb_local_evidence.sqlite3").resolve())
        watcher = BNBLaunchpoolForwardShadowWatcher(
            store=EvidenceStore(evidence_path),
            source=BinanceOfficialLaunchpoolSource(timeout=15),
            market=BinanceSpotBNBBTCKlineFeed(timeout=10),
        )
        monitor = BNBLocalFastMonitor(
            watcher=watcher,
            status_path=str(status_path.resolve()),
            interval_seconds=30.0,
        )
        monitor.run_forever()
    except Exception as exc:
        _write_json_atomic(status_path, {
            "status": "FAIL_CLOSED",
            "build_id": BUILD_ID,
            "error": f"{type(exc).__name__}:{exc}",
            "traceback": traceback.format_exc(limit=8),
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
            "micro_live_execution_enabled": False,
        })


def _start_bnb_thread() -> threading.Thread:
    thread = threading.Thread(
        target=_run_bnb_background,
        name="BNB-Launchpool-Fast-Shadow-Monitor",
        daemon=True,
    )
    thread.start()
    return thread


def _start_dh03_thread() -> threading.Thread:
    thread = threading.Thread(
        target=_run_dh03_background,
        name="DH03-12H-Shadow-Collector",
        daemon=True,
    )
    thread.start()
    return thread


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
        package_state["dh03_collector_importable"] = True
        package_state["bnb_local_monitor_importable"] = True
        print(json.dumps(package_state, sort_keys=True))
        return 0

    _start_dh03_thread()
    _start_bnb_thread()

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
