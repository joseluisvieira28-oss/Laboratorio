#!/usr/bin/env python3
from __future__ import annotations

import json
from decimal import Decimal, getcontext
from pathlib import Path
from statistics import mean, pstdev

getcontext().prec = 60

HERE = Path("research/liquidation_convexity_oracle_distance_001")
INDEX = HERE / "LCOD_FORWARD_SERIES_INDEX_V0.1.json"
SNAPDIR = HERE / "forward_snapshots"
OUT = HERE / "LCOD_PREDICTOR_ONLY_VIABILITY_REVIEW_STATUS_V0.1.json"
ADJ = HERE / "LCOD_FORWARD_PROVENANCE_ADJUDICATION_001.json"

GRID = [0, 25, 50, 75, 100, 150, 200, 300, 500]

def load(path: Path):
    return json.loads(path.read_text())

def D(x) -> Decimal:
    return Decimal(str(x))

def dec_str(x: Decimal) -> str:
    return format(x, "f")

def stats_dec(values):
    vals = [D(v) for v in values]
    if not vals:
        raise ValueError("EMPTY_SERIES")
    mu = sum(vals) / D(len(vals))
    sd = D(0) if len(vals) == 1 else (sum((v - mu) ** 2 for v in vals) / D(len(vals))).sqrt()
    return {
        "min": dec_str(min(vals)),
        "max": dec_str(max(vals)),
        "mean": dec_str(mu),
        "population_stddev": dec_str(sd),
    }

def consecutive_abs(values):
    vals = [D(v) for v in values]
    return [abs(vals[i] - vals[i - 1]) for i in range(1, len(vals))]

def consecutive_abs_relative(values):
    vals = [D(v) for v in values]
    out = []
    for i in range(1, len(vals)):
        prev = vals[i - 1]
        if prev == 0:
            raise ValueError("ZERO_PREVIOUS_VALUE_FOR_RELATIVE_CHANGE")
        out.append(abs((vals[i] - prev) / prev))
    return out

def frac_to_decimal(obj):
    den = D(obj["denominator"])
    if den == 0:
        raise ValueError("ZERO_DENOMINATOR")
    return D(obj["numerator"]) / den

index = load(INDEX)
adjudication = load(ADJ) if ADJ.exists() else None

def resolved_scientific_identity(snapshot, fname):
    direct = snapshot.get("workflow", {}).get("scientific_code_sha")
    if direct not in (None, ""):
        return direct
    if not adjudication:
        return None
    target = adjudication.get("target_snapshot", {})
    if adjudication.get("classification") != "PROVENANCE_EQUIVALENCE_PASS":
        return None
    if target.get("file") != fname:
        return None
    if target.get("snapshot_sha256") != snapshot.get("snapshot_sha256"):
        return None
    if int(target.get("ethereum_block_number", -1)) != int(snapshot.get("ethereum_block_number", -2)):
        return None
    if adjudication.get("scientific_core_changed_between_observed_shas") is not False:
        return None
    for flag in ("outcome_data_opened", "market_returns_opened", "liquidation_outcomes_opened", "pnl_opened"):
        if adjudication.get(flag) is not False:
            return None
    if adjudication.get("snapshot_mutated") is not False:
        return None
    fp = adjudication.get("scientific_core_fingerprint_sha256")
    if not fp:
        return None
    return "ADJUDICATED_CORE_FINGERPRINT:" + fp

base = {
    "lab_id": "LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
    "stage": "PREDICTOR_ONLY_VIABILITY_REVIEW_V0.1",
    "required_observations": 30,
    "required_distinct_utc_days": 21,
    "canonical_successful_daily_observation_count": index.get("canonical_successful_daily_observation_count", 0),
    "distinct_utc_day_count": index.get("distinct_utc_day_count", 0),
    "boundary_violation_count": index.get("boundary_violation_count", 0),
    "duplicate_same_day_observation_count": index.get("duplicate_same_day_observation_count", 0),
    "market_returns_opened": False,
    "future_liquidation_outcomes_opened": False,
    "pnl_opened": False,
    "mutation": False,
    "promotion_credit": 0,
}

ready = (
    base["canonical_successful_daily_observation_count"] >= 30
    and base["distinct_utc_day_count"] >= 21
)

if not ready:
    base["classification"] = "ACCUMULATION_GATE_NOT_READY"
    base["metrics_opened"] = False
    OUT.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")
    print(json.dumps(base, indent=2, sort_keys=True))
    raise SystemExit(0)

errors = []
if index.get("boundary_violation_count", 0) != 0:
    errors.append("INDEX_BOUNDARY_VIOLATION")
if index.get("classification") not in ("PREDICTOR_ONLY_VIABILITY_GATE_READY", "FORWARD_SERIES_ACCUMULATING"):
    errors.append("UNEXPECTED_INDEX_CLASSIFICATION")

obs = index.get("canonical_observations", [])
if len(obs) < 30:
    errors.append("INDEX_CANONICAL_OBSERVATION_LIST_TOO_SHORT")

snaps = []
resolved_scientific_identities = []
for row in obs:
    fname = row.get("file")
    if not fname:
        errors.append("MISSING_SNAPSHOT_FILENAME")
        continue
    p = SNAPDIR / fname
    if not p.exists():
        errors.append(f"MISSING_SNAPSHOT:{fname}")
        continue
    x = load(p)

    if x.get("classification") != "FORWARD_MECHANICAL_SNAPSHOT_PASS":
        errors.append(f"BAD_CLASSIFICATION:{fname}")
    if x.get("observation_role") != "FORWARD_OBSERVATION":
        errors.append(f"BAD_ROLE:{fname}")
    for flag in ("market_returns_opened", "future_liquidation_outcomes_opened", "pnl_opened", "mutation"):
        if x.get(flag) is not False:
            errors.append(f"BOUNDARY_FLAG:{fname}:{flag}")
    if x.get("curve", {}).get("frozen_stress_bps") != GRID:
        errors.append(f"GRID_MISMATCH:{fname}")
    if not x.get("curve", {}).get("curve_sha256"):
        errors.append(f"MISSING_CURVE_SHA:{fname}")
    resolved_identity = resolved_scientific_identity(x, fname)
    if resolved_identity is None:
        errors.append(f"MISSING_OR_UNRESOLVED_SCIENTIFIC_CODE_IDENTITY:{fname}")
    else:
        resolved_scientific_identities.append(resolved_identity)
    if x.get("population", {}).get("active_debt_pair_count") is None:
        errors.append(f"MISSING_ACTIVE_COUNT:{fname}")
    if x.get("components", {}).get("total_active_debt_value_ray") is None:
        errors.append(f"MISSING_TOTAL_ACTIVE_DEBT:{fname}")
    points = x.get("curve", {}).get("points", [])
    if [p.get("stress_bps") for p in points] != GRID:
        errors.append(f"POINT_GRID_MISMATCH:{fname}")
    if len(x.get("curve", {}).get("geometry", {}).get("interval_slopes_value_ray_per_percentage_point", [])) != 8:
        errors.append(f"SLOPE_COUNT_MISMATCH:{fname}")
    if len(x.get("curve", {}).get("geometry", {}).get("interior_curvatures_value_ray_per_percentage_point_squared", [])) != 7:
        errors.append(f"CURVATURE_COUNT_MISMATCH:{fname}")
    snaps.append(x)

if errors:
    out = dict(base)
    out.update({
        "classification": "PREDICTOR_ONLY_REVIEW_BLOCKED",
        "metrics_opened": False,
        "blockers": sorted(set(errors)),
    })
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    raise SystemExit(2)

# Preserve canonical order from the index.
active_counts = [x["population"]["active_debt_pair_count"] for x in snaps]
total_debts = [D(x["components"]["total_active_debt_value_ray"]) for x in snaps]

active_abs = consecutive_abs(active_counts)
debt_abs_rel = consecutive_abs_relative(total_debts)

population_variation = stats_dec(active_counts)
population_variation.update({
    "first_to_last_change": str(active_counts[-1] - active_counts[0]),
    "consecutive_absolute_change_mean": dec_str(sum(active_abs) / D(len(active_abs))) if active_abs else "0",
    "consecutive_absolute_change_max": dec_str(max(active_abs)) if active_abs else "0",
})

debt_variation = stats_dec(total_debts)
debt_variation.update({
    "first_to_last_relative_change": dec_str((total_debts[-1] - total_debts[0]) / total_debts[0]),
    "consecutive_absolute_relative_change_mean": dec_str(sum(debt_abs_rel) / D(len(debt_abs_rel))) if debt_abs_rel else "0",
    "consecutive_absolute_relative_change_max": dec_str(max(debt_abs_rel)) if debt_abs_rel else "0",
})

curve_by_stress = []
fraction_vectors = []
for x in snaps:
    total = D(x["components"]["total_active_debt_value_ray"])
    vec = []
    for p in x["curve"]["points"]:
        debt = D(p["cumulative_new_debt_value_ray"])
        vec.append(debt / total if total != 0 else D(0))
    fraction_vectors.append(vec)

for j, stress in enumerate(GRID):
    counts = [x["curve"]["points"][j]["cumulative_new_count"] for x in snaps]
    debts = [D(x["curve"]["points"][j]["cumulative_new_debt_value_ray"]) for x in snaps]
    fracs = [fraction_vectors[i][j] for i in range(len(snaps))]
    curve_by_stress.append({
        "stress_bps": stress,
        "cumulative_new_count": stats_dec(counts),
        "cumulative_new_debt_value_ray": stats_dec(debts),
        "cumulative_new_debt_fraction_of_total_active": stats_dec(fracs),
    })

l1s, l2s, linfs = [], [], []
for i in range(1, len(fraction_vectors)):
    diffs = [abs(a - b) for a, b in zip(fraction_vectors[i], fraction_vectors[i - 1])]
    l1s.append(sum(diffs))
    l2s.append((sum(d * d for d in diffs)).sqrt())
    linfs.append(max(diffs))

vector_movement = {
    "l1_distance": stats_dec(l1s),
    "l2_distance": stats_dec(l2s),
    "max_absolute_coordinate_movement": stats_dec(linfs),
}

slope_series = [[] for _ in range(8)]
curv_series = [[] for _ in range(7)]
for x in snaps:
    geom = x["curve"]["geometry"]
    for j, obj in enumerate(geom["interval_slopes_value_ray_per_percentage_point"]):
        slope_series[j].append(frac_to_decimal(obj))
    for j, obj in enumerate(geom["interior_curvatures_value_ray_per_percentage_point_squared"]):
        curv_series[j].append(frac_to_decimal(obj))

slope_variation = [
    {"interval_index": i, **stats_dec(vals)} for i, vals in enumerate(slope_series)
]
curvature_variation = [
    {"interior_index": i, **stats_dec(vals)} for i, vals in enumerate(curv_series)
]

full_component_coverage_count = sum(
    1 for x in snaps
    if D(x["components"].get("count_coverage", 0)) == 1
    and D(x["components"].get("debt_coverage", 0)) == 1
)
zero_source_error_count = sum(
    1 for x in snaps
    if x["population"].get("borrow_decode_error_count") == 0
    and x["population"].get("uad_error_count") == 0
)

out = dict(base)
out.update({
    "classification": "PREDICTOR_ONLY_REVIEW_COMPLETE",
    "metrics_opened": True,
    "source_provenance_stability": {
        "canonical_observation_count": len(snaps),
        "distinct_utc_day_count": index.get("distinct_utc_day_count"),
        "duplicate_count": index.get("duplicate_same_day_observation_count"),
        "boundary_violation_count": index.get("boundary_violation_count"),
        "diagnostic_or_noncanonical_file_count": index.get("diagnostic_or_noncanonical_file_count"),
        "unique_scientific_code_identities": sorted(set(resolved_scientific_identities)),
        "unique_workflow_event_names": sorted({x["workflow"].get("github_event_name") for x in snaps}),
        "full_component_coverage_snapshot_count": full_component_coverage_count,
        "zero_decode_and_uad_error_snapshot_count": zero_source_error_count,
    },
    "active_population_variation": population_variation,
    "total_active_debt_variation": debt_variation,
    "full_nine_point_curve_variation": curve_by_stress,
    "full_vector_consecutive_movement": vector_movement,
    "all_interval_slope_variation": slope_variation,
    "all_interior_curvature_variation": curvature_variation,
    "interpretation_boundary": "predictor/source stability only; no outcomes opened; no shock selected; zero trading-edge promotion credit",
})
OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, indent=2, sort_keys=True))
