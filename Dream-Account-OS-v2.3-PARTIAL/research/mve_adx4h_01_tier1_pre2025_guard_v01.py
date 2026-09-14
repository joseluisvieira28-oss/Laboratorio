#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FREEZE = Path(__file__).with_name("MVE_ADX4H_01_TIER1_CONFIRMATION_PRE2025_FREEZE_V01.json")
EXPECTED_UNIVERSE = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
EXPECTED_BLOBS = {
    "classic_indicators_gap_v01.py": "21398ba193d10d465c10b392e1dc8461270a0491",
    "CLASSIC_INDICATORS_GAP_LAB_V01_PROTOCOL.json": "0ac36b01d682064576b6d1279d26a1d7056c780f",
    "cigl_adx_01_action_v01.py": "bd8cd57e3ea7b25df1eab5a4c8c80fbe7fd5694c",
}


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    hdr = f"blob {len(data)}\0".encode()
    return hashlib.sha1(hdr + data).hexdigest()


def validate_pre2025_guard(research_dir: Path) -> dict:
    cfg = json.loads(FREEZE.read_text(encoding="utf-8"))
    errors: list[str] = []
    if cfg.get("status") != "FROZEN_PRE_2025_NO_DATA_ACCESS":
        errors.append("freeze status drift")
    if cfg.get("rule", {}).get("universe") != EXPECTED_UNIVERSE:
        errors.append("universe drift")
    if cfg.get("confirmatory_window", {}).get("data_access_authorized") is not False:
        errors.append("2025 data access unexpectedly authorized")
    if cfg.get("confirmatory_window", {}).get("open_2026") is not False:
        errors.append("2026 lock drift")
    if cfg.get("locks", {}).get("live_trading") is not False:
        errors.append("live trading lock drift")
    if cfg.get("locks", {}).get("exchange_mutation") is not False:
        errors.append("exchange mutation lock drift")
    if cfg.get("sample_policy", {}).get("minimum_resolved_trades") != 1000:
        errors.append("sample threshold drift")
    for name, expected in EXPECTED_BLOBS.items():
        path = research_dir / name
        if not path.exists():
            errors.append(f"missing frozen authority file: {name}")
            continue
        actual = git_blob_sha1(path)
        if actual != expected:
            errors.append(f"frozen authority byte mismatch: {name} {actual} != {expected}")
    return {
        "status": "PASS_PRE2025_GUARD" if not errors else "BLOCKED_PRE2025_GUARD",
        "errors": errors,
        "2025_market_data_access": False,
        "2026_market_data_access": False,
        "network_acquisition": False,
        "live_trading": False,
        "exchange_mutation": False,
    }


def main() -> int:
    research_dir = Path(__file__).resolve().parent
    out = validate_pre2025_guard(research_dir)
    print(json.dumps(out, sort_keys=True))
    return 0 if out["status"] == "PASS_PRE2025_GUARD" else 2


if __name__ == "__main__":
    raise SystemExit(main())
