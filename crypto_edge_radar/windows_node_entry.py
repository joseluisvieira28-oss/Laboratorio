from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import threading
import traceback

from radar.__main__ import main
from radar.dh03_12h_local import DH03LocalCollector, default_paths, require_dh03_clock_preflight
from radar.local_forward import LocalForwardSupervisor
from radar.render_sentinel import RenderSentinel


BUILD_ID = "v0.14.3.2-win-live-state-reconciliation"


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
    ced1d = "CED1D-0031"
    if ced1d not in ids:
        raise RuntimeError(f"deployment registry missing external CED1D strategy: {ced1d}")
    ema6h = "EMA6H-50X200-REGIME-DEPENDENCY-001"
    if ema6h not in ids:
        raise RuntimeError(f"deployment registry missing EMA6H regime forward strategy: {ema6h}")
    state = {
        "status": "PASS",
        "build_id": BUILD_ID,
        "registry_version": payload.get("registry_version"),
        "candidate_count": len(candidates),
        "required_strategy_present": True,
        "dh03_strategy_present": True,
        "ced1d_strategy_present": True,
        "ema6h_strategy_present": True,
    }
    return payload, state


def _verify_standing_authority_file(authority_path: str) -> dict:
    if not os.path.isfile(authority_path):
        raise RuntimeError(f"standing MEXC authority missing: {authority_path}")
    payload = json.loads(Path(authority_path).read_text(encoding="utf-8"))
    if payload.get("authority_id") != "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1":
        raise RuntimeError("standing MEXC authority id mismatch")
    if payload.get("status") != "ACTIVE_STANDING_OPERATOR_AUTHORIZATION":
        raise RuntimeError("standing MEXC authority is not active")
    scope = payload.get("scope") or {}
    if scope.get("exchange") != "MEXC" or scope.get("product") != "USDT_PERPETUAL_FUTURES":
        raise RuntimeError("standing MEXC authority scope mismatch")
    if scope.get("micro_live_only") is not True:
        raise RuntimeError("standing MEXC authority scope is not micro-live only")
    if scope.get("per_trade_reconfirmation_required") is not False:
        raise RuntimeError("standing MEXC authority per-trade reconfirmation flag invalid")
    return {
        "standing_authority_present": True,
        "standing_authority_id": payload.get("authority_id"),
        "standing_authority_status": payload.get("status"),
    }


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


def _run_forward_background() -> None:
    status_path = Path("data") / "forward_local_supervisor_status.json"
    try:
        supervisor = LocalForwardSupervisor(root="data")
        _write_json_atomic(status_path, {
            "status": "RUNNING",
            "build_id": BUILD_ID,
            "engines": [
                "BNB-LAUNCHPOOL-DEMAND-001",
                "TFG-DONCHIAN-REGIME-ADAPTATION-V1",
                "OPTIONS-SPOTPERP-001-V2.1",
                "ETF-CME-INSTFLOW-001",
                "EMA6H-50X200-REGIME-DEPENDENCY-001",
            ],
            "poll_interval_seconds": 30.0,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        })
        supervisor.run_forever()
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
        })


def _start_forward_thread() -> threading.Thread:
    thread = threading.Thread(
        target=_run_forward_background,
        name="Five-Engine-Local-Forward-Shadow",
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


def _run_render_sentinel_background() -> None:
    status_path = Path("data") / "render_sentinel_supervisor_status.json"
    try:
        sentinel = RenderSentinel(root="data")
        _write_json_atomic(status_path, {
            "status": "RUNNING",
            "build_id": BUILD_ID,
            "interval_seconds": sentinel.interval_seconds,
            "base_url": sentinel.base_url,
            "mode": "READ_ONLY_KEEPALIVE_AND_RECONCILIATION",
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        })
        sentinel.run_forever()
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
        })


def _start_render_sentinel_thread() -> threading.Thread:
    thread = threading.Thread(
        target=_run_render_sentinel_background,
        name="Render-Public-Shadow-Sentinel",
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
        authority_state = _verify_standing_authority_file(
            _resource_path("MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json")
        )
        package_state.update(authority_state)
        runtime_registry = _materialize_registry(payload)
        _, runtime_state = _verify_registry_file(runtime_registry)
        package_state["runtime_registry_materialized"] = True
        package_state["runtime_candidate_count"] = runtime_state["candidate_count"]
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "build_id": BUILD_ID, "error": str(exc)}, sort_keys=True))
        return 2

    if os.getenv("RADAR_PACKAGING_SELFTEST") == "1":
        package_state["dh03_collector_importable"] = True
        package_state["local_forward_supervisor_importable"] = True
        package_state["render_sentinel_importable"] = True
        package_state["resilient_control_plane_bootstrap"] = True
        print(json.dumps(package_state, sort_keys=True))
        return 0

    # Materialize a control-plane status before any network gate. The local
    # dashboard must always come up so an individual motor can fail closed
    # without blacking out diagnostics for the other motors.
    _write_json_atomic(Path("data") / "radar_status.json", {
        "health": "OK",
        "provider": "MULTI_SOURCE_PUBLIC_CONTROL_PLANE",
        "cycle": 0,
        "universe": [],
        "build_id": BUILD_ID,
        "mode": "PUBLIC_SHADOW_CONTROL_PLANE",
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    })

    # DH03 activation_ms is a prospective scientific boundary. Validate the
    # Binance public clock before the collector can persist that boundary.
    # Failure blocks DH03 only; it must not prevent the seven-motor cockpit,
    # forward supervisor, or Render sentinel from starting.
    dh03_clock_ok = False
    try:
        dh03_clock = require_dh03_clock_preflight()
        _write_json_atomic(Path("data") / "dh03_clock_preflight.json", dh03_clock)
        dh03_clock_ok = True
    except Exception as exc:
        failure = {
            "status": "FAIL_CLOSED",
            "build_id": BUILD_ID,
            "component": "DH03_CLOCK_ARMING_GUARD",
            "error": f"{type(exc).__name__}:{exc}",
            "orders_created": False,
            "live_capital_enabled": False,
        }
        _write_json_atomic(Path("data") / "dh03_clock_preflight.json", failure)
        _write_json_atomic(Path("data") / "dh03_local_status.json", {
            **failure,
            "status": "FAIL_CLOSED",
            "reason": "DH03_NOT_STARTED_CLOCK_PREFLIGHT_FAILED",
        })
        print(json.dumps(failure, sort_keys=True), flush=True)

    if dh03_clock_ok:
        _start_dh03_thread()
    _start_forward_thread()
    _start_render_sentinel_thread()

    # V0.14.1 intentionally serves the multi-motor cockpit directly instead
    # of invoking the legacy MEXC single-provider local-node preflight. Each
    # research motor already has its own public-source fail-closed gate.
    return main(
        [
            "dashboard",
            "--port",
            "8787",
            "--registry",
            runtime_registry,
        ]
    )


if __name__ == "__main__":
    sys.exit(run())
