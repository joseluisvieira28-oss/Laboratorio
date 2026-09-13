#!/usr/bin/env python3
"""Static/synthetic pre-run review for ONCHAIN-CAPFLOW-001 V0.1A.

This script MUST NOT read the real raw dataset and MUST NOT compute any real market outcome.
It validates frozen hashes, offline-only posture, constants and deterministic metric mechanics.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DISCOVERY = ROOT / "discovery.py"
CONTRACT = ROOT / "DISCOVERY_CONTRACT.json"

EXPECTED_DISCOVERY_SHA256 = "9f271a74fca8ccdac52331b836b2ebf01a472362ace39a5175727cb878c87865"
EXPECTED_CONTRACT_SHA256 = "564110a73e013031e08f9b86af7c130e0b6247a5489cce9f540f7bc5b4c0a1c4"
EXPECTED_RAW_MANIFEST_SHA256 = "a45ceb4248c9438dfafc6580627fc399fccfafb0ec208cb87024412ca8f08794"
FORBIDDEN_IMPORT_ROOTS = {
    "urllib", "requests", "httpx", "aiohttp", "socket", "websocket",
    "websockets", "ftplib", "paramiko",
}


def sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def import_discovery():
    spec = importlib.util.spec_from_file_location("onchain_discovery_frozen", DISCOVERY)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load discovery.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_offline_only() -> None:
    source = DISCOVERY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(DISCOVERY))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = sorted(imported & FORBIDDEN_IMPORT_ROOTS)
    assert not forbidden, f"forbidden network import(s): {forbidden}"
    assert "urlopen(" not in source
    assert "http://" not in source
    assert "https://" not in source


def synthetic_metric_checks(d) -> None:
    history = [float(i) for i in range(52)]
    p38 = d.percentile_midrank(38.0, history)
    p39 = d.percentile_midrank(39.0, history)
    assert p38 < 0.75
    assert p39 >= 0.75
    assert d.classify(p38) == "FLAT"
    assert d.classify(p39) == "LONG"

    p12 = d.percentile_midrank(12.0, history)
    p13 = d.percentile_midrank(13.0, history)
    assert p12 <= 0.25
    assert p13 > 0.25
    assert d.classify(p12) == "SHORT"
    assert d.classify(p13) == "FLAT"

    date = __import__("datetime").date
    records = [
        {"state": "LONG", "btc_return": 0.03, "entry_monday": date(2021, 1, 4)},
        {"state": "LONG", "btc_return": 0.01, "entry_monday": date(2021, 1, 11)},
        {"state": "SHORT", "btc_return": -0.02, "entry_monday": date(2021, 1, 18)},
        {"state": "SHORT", "btc_return": 0.00, "entry_monday": date(2021, 1, 25)},
        {"state": "FLAT", "btc_return": 9.99, "entry_monday": date(2021, 2, 1)},
    ]
    gross = d.top_bottom_spread(records, "btc_return", 0.0)
    base = d.top_bottom_spread(records, "btc_return", 0.001)
    stress = d.top_bottom_spread(records, "btc_return", 0.002)
    assert math.isclose(gross, 0.03, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(base, 0.028, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(stress, 0.026, rel_tol=0, abs_tol=1e-12)

    active = d.directional_net_returns(records, "btc_return", 0.001)
    expected = [0.029, 0.009, 0.019, -0.001]
    assert len(active) == 4
    for (_, actual), exp in zip(active, expected):
        assert math.isclose(actual, exp, rel_tol=0, abs_tol=1e-12)

    assert d.NW_LAG == 4
    assert d.BOOTSTRAP_BLOCK == 4
    assert d.BOOTSTRAP_RESAMPLES == 10_000
    assert d.BOOTSTRAP_SEED == 20260913
    assert math.isclose(d.BASE_COST, 0.001)
    assert math.isclose(d.STRESS_COST, 0.002)
    assert math.isclose(d.YEAR_DOMINANCE_MAX, 0.60)
    assert math.isclose(d.SINGLE_WEEK_DOMINANCE_MAX, 0.25)
    assert math.isclose(d.STRESS_SPREAD_MIN, -0.001)


def main() -> int:
    checks = []

    discovery_hash = sha256_bytes(DISCOVERY)
    checks.append(("discovery_file_sha256", discovery_hash == EXPECTED_DISCOVERY_SHA256, discovery_hash))

    contract_hash = canonical_hash(CONTRACT)
    checks.append(("contract_canonical_sha256", contract_hash == EXPECTED_CONTRACT_SHA256, contract_hash))

    assert_offline_only()
    checks.append(("offline_only_ast", True, "no network-capable imports/URLs"))

    compile(DISCOVERY.read_text(encoding="utf-8"), str(DISCOVERY), "exec")
    checks.append(("python_compile", True, "PASS"))

    d = import_discovery()
    assert d.CONTRACT_SHA256 == EXPECTED_CONTRACT_SHA256
    assert d.RAW_MANIFEST_SHA256 == EXPECTED_RAW_MANIFEST_SHA256
    assert d.HOLDOUT_START.isoformat() == "2025-01-01"
    assert d.DISCOVERY_END.isoformat() == "2024-12-31"
    checks.append(("frozen_constants", True, "PASS"))

    synthetic_metric_checks(d)
    checks.append(("synthetic_metric_mechanics", True, "PASS"))

    failed = [name for name, ok, _ in checks if not ok]
    receipt = {
        "lab_id": "ONCHAIN-CAPFLOW-001",
        "version": "V0.1A",
        "stage": "PRE_RUN_STATIC_SYNTHETIC_REVIEW",
        "status": "PASS" if not failed else "FAIL",
        "checks": [
            {"name": name, "pass": ok, "detail": detail}
            for name, ok, detail in checks
        ],
        "real_raw_data_read": False,
        "real_outcome_metrics_computed": False,
        "holdout_2025_accessed": False,
        "locked_2026_accessed": False,
    }
    out = ROOT / "pre_run_review_receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
