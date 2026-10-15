"""RC3.3 broker-stop preflight: offline ONLY, no imports of local engine.

This read-only tool NEVER executes target source code and NEVER makes network calls.
Its verdict cannot certify any broker roundtrip. No API clients, POSTs, or keys.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Any

EXPECTED_ENGINE_SHA256 = "26b05a1f229f1884d0c15c802c98ecad71f30b108f68efe165d72f3e2ab2b714"
EXPECTED_TRANSPORT_SHA256 = "fac987781b281deacab576134148f1611559c2ddd2061dc86110319103263034"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_snapshot(path: Path, expected: str) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "sha256_matches_user_receipt": False, "syntax": "UNVERIFIED",
                "functions_present": [], "classes_present": []}
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    # Read/parse code as data; do not import, execute, eval or compile it.
    try:
        tree = ast.parse(raw.decode("utf-8-sig"), filename="<local-source>")
    except (UnicodeError, SyntaxError, ValueError):
        return {"exists": True, "sha256": digest,
                "sha256_matches_user_receipt": digest == expected, "syntax": "UNVERIFIED",
                "functions_present": [], "classes_present": []}
    methods = sorted({
        f.name for f in ast.walk(tree)
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
    })
    classes = sorted({
        x.name for x in ast.walk(tree)
        if isinstance(x, ast.ClassDef)
    })
    allowed = ("validated_stop", "matching_stop", "entry_recovery",
               "emergency_flatten_unprotected", "frozen_authority",
               "buy_with_initial_stop", "install_stop_only", "revise_stop_only",
               "stops", "positions", "order_by_external", "call")
    return {"exists": True, "sha256": digest,
            "sha256_matches_user_receipt": digest == expected, "syntax": "PARSEABLE_ONLY",
            "functions_present": [x for x in allowed if x in methods],
            "classes_present": [x for x in ("MexcFutures", "EngineBlocked") if x in classes]}


def offline_preflight(root: Path) -> dict[str, Any]:
    state = root / "state"
    engine = _source_snapshot(root / "app" / "engine.py", EXPECTED_ENGINE_SHA256)
    transport = _source_snapshot(root / "app" / "mexc_futures.py", EXPECTED_TRANSPORT_SHA256)
    kill = (state / "KILL_SWITCH").is_file()
    auth_absent = not (state / "LIVE_AUTHORITY.json").exists()
    mode, positions, pending = "UNVERIFIED", None, None
    status_file = state / "status.json"
    try:
        status = json.loads(status_file.read_text(encoding="utf-8"))
        mode = status.get("mode", "UNVERIFIED")
        positions = status.get("positions")
        pending = status.get("pending_entries")
    except (OSError, UnicodeError, ValueError, AttributeError):
        pass
    # Do not return any config values, file contents, directory paths or tokens.
    local_disarmed = (kill and auth_absent and mode == "OBSERVE_ONLY"
                      and type(positions) is int and positions == 0
                      and type(pending) is int and pending == 0)
    return {
        "schema": "RC33_STOP_OFFLINE_PREFLIGHT_V01",
        "engine": engine,
        "transport": transport,
        "kill_switch_present": kill,
        "live_authority_absent": auth_absent,
        "status_mode": mode,
        "local_positions_count": positions,
        "local_pending_entries_count": pending,
        "local_disarmed_snapshot": bool(local_disarmed),
        "broker_account": "NOT_QUERIED",
        "native_stop_roundtrip": "NOT_EXECUTED",
        "installation_certification": "NOT_CERTIFIED",
        "live_go": False,
        "mutation_performed": False,
        "reason": "BROKER_ATTACHED_SL_ROUNDTRIP_NOT_CERTIFIED",
    }


def main() -> int:
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "CryptoLab" / "ConvexRadarUnifiedRC33"
    result = offline_preflight(root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0  # Success means an inspection ran; NEVER a broker certification PASS.


if __name__ == "__main__":
    raise SystemExit(main())
