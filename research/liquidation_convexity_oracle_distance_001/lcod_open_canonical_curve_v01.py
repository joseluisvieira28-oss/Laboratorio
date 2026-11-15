#!/usr/bin/env python3
"""Open the frozen LCOD canonical mechanical stress curve after component PASS.

No RPC. No future outcomes. No PnL. Fails closed on provenance mismatch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from canonical_stress_curve import Borrower, canonical_curve, exact_geometry

HERE = Path(__file__).resolve().parent
COMP = HERE / "LCOD_FULL_SAME_BLOCK_COMPONENT_RECONSTRUCTION_RECEIPT.json"
POP = HERE / "LCOD_BLOCK_PINNED_ACTIVE_POPULATION_RECEIPT.json"
OUT = HERE / "LCOD_CANONICAL_COLLATERAL_STRESS_CURVE_RECEIPT.json"


def sha_obj(x) -> str:
    raw = json.dumps(x, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


comp = json.loads(COMP.read_text())
pop = json.loads(POP.read_text())

if comp.get("classification") != "FULL_SAME_BLOCK_COMPONENT_PASS":
    raise SystemExit("COMPONENT_GATE_NOT_PASS")
if pop.get("classification") != "BLOCK_PINNED_ACTIVE_POPULATION_PASS":
    raise SystemExit("ACTIVE_POPULATION_NOT_PASS")
if comp.get("ethereum_block_number") != pop.get("ethereum_block_number"):
    raise SystemExit("BLOCK_NUMBER_MISMATCH")
if str(comp.get("ethereum_block_hash", "")).lower() != str(pop.get("ethereum_block_hash", "")).lower():
    raise SystemExit("BLOCK_HASH_MISMATCH")
if comp.get("canonical_active_pair_set_sha256") != pop.get("canonical_active_pair_set_sha256"):
    raise SystemExit("POPULATION_SHA_MISMATCH")
if not comp.get("active_set_match"):
    raise SystemExit("ACTIVE_SET_REPRODUCTION_NOT_PASS")
if float(comp.get("count_coverage", 0)) < 0.90:
    raise SystemExit("COUNT_COVERAGE_BELOW_FROZEN_GATE")
if float(comp.get("debt_coverage", 0)) < 0.90:
    raise SystemExit("DEBT_COVERAGE_BELOW_FROZEN_GATE")

included = [r for r in comp.get("rows", []) if r.get("status") == "INCLUDED"]
if len(included) != int(comp.get("included_pair_count", -1)):
    raise SystemExit("INCLUDED_ROW_COUNT_MISMATCH")

borrowers = [
    Borrower(
        pair_hash=str(r["pair_sha256"]),
        official_hf_wad=int(r["official_health_factor_wad"]),
        reconstructed_hf_wad=int(r["reconstructed_health_factor_wad"]),
        debt_value_ray=int(r["official_total_debt_value_ray"]),
        weighted_collateral_bps_value=int(r["weighted_collateral_bps_value"]),
    )
    for r in included
]

try:
    points, meta = canonical_curve(borrowers)
    geometry = exact_geometry(points)
except ValueError as exc:
    receipt = {
        "lab_id": "LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
        "stage": "CANONICAL_COLLATERAL_STRESS_CURVE_V0.1",
        "classification": "CANONICAL_CURVE_SOURCE_BLOCKED",
        "reason": str(exc),
        "ethereum_block_number": comp.get("ethereum_block_number"),
        "ethereum_block_hash": comp.get("ethereum_block_hash"),
        "component_receipt_sha256": sha_obj(comp),
        "market_returns_opened": False,
        "future_liquidation_outcomes_opened": False,
        "pnl_opened": False,
        "mutation": False,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2))
    raise SystemExit(2)

point_rows = [
    {
        "stress_bps": p.stress_bps,
        "newly_eligible_count": p.newly_count,
        "newly_eligible_debt_value_ray": str(p.newly_debt_value_ray),
        "cumulative_new_count": p.cumulative_new_count,
        "cumulative_new_debt_value_ray": str(p.cumulative_new_debt_value_ray),
        "total_eligible_count": p.total_eligible_count,
        "total_eligible_debt_value_ray": str(p.total_eligible_debt_value_ray),
    }
    for p in points
]

receipt = {
    "lab_id": "LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
    "stage": "CANONICAL_COLLATERAL_STRESS_CURVE_V0.1",
    "classification": "CANONICAL_MECHANICAL_CURVE_PASS",
    "ethereum_block_number": comp["ethereum_block_number"],
    "ethereum_block_hash": comp["ethereum_block_hash"],
    "canonical_active_pair_set_sha256": comp["canonical_active_pair_set_sha256"],
    "component_receipt_sha256": sha_obj(comp),
    "included_pair_count": len(included),
    "component_count_coverage": comp["count_coverage"],
    "component_debt_coverage": comp["debt_coverage"],
    "baseline": {
        "underwater_count": meta["baseline_underwater_count"],
        "underwater_debt_value_ray": str(meta["baseline_underwater_debt_value_ray"]),
        "healthy_count": meta["healthy_baseline_count"],
        "threshold_side_disagreement_count": meta["threshold_side_disagreement_count"],
    },
    "points": point_rows,
    "geometry": geometry,
    "curve_sha256": sha_obj({"points": point_rows, "geometry": geometry, "baseline": meta}),
    "interpretation_boundary": "mechanical solvency curve only; zero predictive/promotion credit",
    "market_returns_opened": False,
    "future_liquidation_outcomes_opened": False,
    "pnl_opened": False,
    "live_trading": False,
    "mutation": False,
}

OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, indent=2))
