#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
RAY = 10**27
EXPECTED_RESERVES = 37
EXPECTED_SHARDS = 8
EXPECTED_SNAPSHOTS = 334
START = date(2023, 2, 1)
END = date(2023, 12, 31)


def load_classified(root: str, wanted: str) -> dict:
    matches = []
    for p in Path(root).rglob("*.json"):
        try:
            x = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if x.get("classification") == wanted:
            matches.append((p, x))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {wanted} under {root}, got {len(matches)}")
    return matches[0][1]


def ray_mul(a: int, b: int) -> int:
    return (a * b + RAY // 2) // RAY


def percent_mul(value: int, bps: int) -> int:
    return (value * bps + 5000) // 10000


def latent(weighted_liq_collateral: int, debt: int, stress_bps: int) -> bool:
    if debt <= 0:
        return False
    if weighted_liq_collateral <= debt:
        return False
    return weighted_liq_collateral * (10000 - stress_bps) <= debt * 10000


def daterange() -> list[str]:
    out = []
    d = START
    while d <= END:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def main() -> int:
    outdir = Path("aave_discovery_d0_preflight_output")
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / "AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_D0_PREFLIGHT_V0_1.json"
    receipt = {
        "lab_id": LAB_ID,
        "phase": "DISCOVERY_D0_PREFLIGHT_OUTCOME_BLIND",
        "classification": None,
        "failure": None,
        "safety": {
            "liquidation_outcomes_opened": False,
            "market_returns_opened": False,
            "pnl_opened": False,
            "accessed_2024_outcomes": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    try:
        r1 = load_classified("downloaded_r1_canonical", "RECONSTRUCTION_DATA_PASS")
        r0 = load_classified("downloaded_r0_bootstrap", "RECONSTRUCTION_R0_BOOTSTRAP_PASS")

        reserves = sorted(str(x).lower() for x in (r0.get("reserves") or {}).keys())
        if len(reserves) != EXPECTED_RESERVES or len(set(reserves)) != EXPECTED_RESERVES:
            raise RuntimeError(f"reserve universe mismatch: {len(reserves)}")

        shards = {str(i): [r for j, r in enumerate(reserves) if j % EXPECTED_SHARDS == i] for i in range(EXPECTED_SHARDS)}
        union = [r for i in range(EXPECTED_SHARDS) for r in shards[str(i)]]
        if sorted(union) != reserves or len(union) != EXPECTED_RESERVES:
            raise RuntimeError("8-shard reserve union mismatch")

        dates = daterange()
        if len(dates) != EXPECTED_SNAPSHOTS:
            raise RuntimeError(f"snapshot count mismatch: {len(dates)}")

        # Deterministic Aave-compatible arithmetic checks.
        if ray_mul(RAY, RAY) != RAY:
            raise RuntimeError("rayMul identity failed")
        if percent_mul(10_000, 8_000) != 8_000:
            raise RuntimeError("percentMul test failed")

        # Primary 10% latent boundary: 1 < HF <= 1/0.9.
        if not latent(110, 100, 1000):
            raise RuntimeError("10% latent positive control failed")
        if latent(120, 100, 1000):
            raise RuntimeError("10% latent upper-bound control failed")
        if latent(100, 100, 1000):
            raise RuntimeError("baseline-liquidatable exclusion failed")
        if not latent(105, 100, 500):
            raise RuntimeError("5% latent diagnostic control failed")
        if not latent(120, 100, 2000):
            raise RuntimeError("20% latent diagnostic control failed")

        r1_components = r1.get("component_status") or {}
        receipt.update({
            "classification": "D0_PREFLIGHT_PASS",
            "canonical_r1_component_status": r1_components,
            "reserve_count": len(reserves),
            "reserve_shard_count": EXPECTED_SHARDS,
            "reserve_shard_sizes": {k: len(v) for k, v in shards.items()},
            "reserve_universe_sha256": hashlib.sha256("\n".join(reserves).encode()).hexdigest(),
            "snapshot_start": dates[0],
            "snapshot_end": dates[-1],
            "snapshot_count": len(dates),
            "snapshot_calendar_sha256": hashlib.sha256("\n".join(dates).encode()).hexdigest(),
            "arithmetic": {
                "ray_mul": "PASS",
                "percent_mul_half_up": "PASS",
                "latent_5pct": "PASS",
                "latent_10pct": "PASS",
                "latent_20pct": "PASS",
            },
            "next_authorized_phase": "D0_GLOBAL_SOURCE_AND_SNAPSHOT_MAPPING_ONLY",
        })
    except Exception as exc:
        receipt["classification"] = "D0_PREFLIGHT_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {str(exc)[:1500]}"
        receipt["next_authorized_phase"] = None

    dst.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "reserve_count": receipt.get("reserve_count"),
        "snapshot_count": receipt.get("snapshot_count"),
        "liquidation_outcomes_opened": False,
        "market_returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if receipt["classification"] == "D0_PREFLIGHT_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
