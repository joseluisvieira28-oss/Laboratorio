#!/usr/bin/env python3
"""PMD-001 V0.8 user-authorized exploratory outcome audit.

Opens economic outcomes by explicit policy amendment. This script has no promotion authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
EXPECTED_SHA256 = {
    "migrations.parquet": "ef5d5141fd94acbcd121bed50e39e525cf7777d25338fc9852a67fd8a085105d",
    "tokens.parquet": "c005d86d424013e5c78701161b025f3d8c3d472afb61466e0ad6fd5afe9e8ea6",
    "postgard_snapshots.parquet": "34a63b8333a41b3cc84d05461febe725cf37842fa0e21d6ea00472dcdcfa1e72",
}
SENTINELS = {"synthetic_graduation_queue", "backfilled_from_pumpswap_trade"}
STRESS = 0.03
ENTRY_MIN_S = 15
ENTRY_MAX_S = 90
EXIT_TARGET_S = 300
EXIT_TOLERANCE_S = 120
FROZEN_BASELINE_EXPECTED_N = 1012


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(x: Any) -> Any:
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        if np.isnan(x):
            return None
        return float(x)
    if isinstance(x, pd.Timestamp):
        return x.isoformat()
    return x


def summarize(df: pd.DataFrame) -> dict[str, Any]:
    n = int(len(df))
    out: dict[str, Any] = {"n": n}
    if n == 0:
        return out
    g = df["gross_return_5m"].astype(float)
    net = df["net_return_5m"].astype(float)
    qs = [0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 1.0]
    out.update({
        "direction_counts": {str(k): int(v) for k, v in df["raw_direction"].value_counts(dropna=False).to_dict().items()},
        "economic_sign_counts": {str(k): int(v) for k, v in df["economic_sign"].value_counts(dropna=False).to_dict().items()},
        "gross_positive_rate": float((g > 0).mean()),
        "net_positive_rate": float((net > 0).mean()),
        "gross_return_mean": float(g.mean()),
        "gross_return_median": float(g.median()),
        "net_return_mean": float(net.mean()),
        "net_return_median": float(net.median()),
        "gross_return_quantiles": {str(q): float(g.quantile(q)) for q in qs},
        "net_return_quantiles": {str(q): float(net.quantile(q)) for q in qs},
        "isolated_total_gross_pnl_1sol_each": float(g.sum()),
        "isolated_total_net_pnl_1sol_each": float(net.sum()),
        "best_net_return": float(net.max()),
        "worst_net_return": float(net.min()),
    })
    return out


def load_boundaries(path: Path) -> pd.DataFrame:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    required = {
        "crossdate_manifest_index", "mint", "pool_address", "v07_boundary_block_time",
        "v07_boundary_variant", "parser_boundary_resolved", "v07_qualifying_boundaries"
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"boundary rows missing columns: {missing}")
    if len(df) != 20 or df["crossdate_manifest_index"].nunique() != 20 or df["mint"].nunique() != 20:
        raise RuntimeError("boundary manifest is not exact frozen 20-row set")
    if not bool(df["parser_boundary_resolved"].all()) or not bool((df["v07_qualifying_boundaries"] == 1).all()):
        raise RuntimeError("not all 20 rows have exactly one V0.7 boundary")
    df = df.sort_values("crossdate_manifest_index").reset_index(drop=True)
    df["boundary_ts"] = pd.to_datetime(df["v07_boundary_block_time"], unit="s", utc=True)
    return df


def build_snapshot_map(p: pd.DataFrame) -> dict[tuple[str, str], pd.DataFrame]:
    p = p.copy()
    p["snapshot_time"] = pd.to_datetime(p["snapshot_time"], utc=True)
    p["price_native"] = pd.to_numeric(p["price_native"], errors="coerce")
    p = p[(~p["incomplete_data"].fillna(True).astype(bool)) & p["price_native"].notna() & (p["price_native"] > 0)]
    p = p.sort_values(["mint", "pair_address", "snapshot_time", "price_native"], kind="mergesort")
    result: dict[tuple[str, str], pd.DataFrame] = {}
    for (mint, pair), g in p.groupby(["mint", "pair_address"], sort=False):
        result[(str(mint), str(pair))] = g[["snapshot_time", "price_native", "dex_id"]].reset_index(drop=True)
    return result


def evaluate_one(mint: str, pool: str, anchor: pd.Timestamp, snap_map: dict[tuple[str, str], pd.DataFrame]) -> dict[str, Any]:
    g = snap_map.get((str(mint), str(pool)))
    base = {
        "mint": str(mint), "pool_address": str(pool), "anchor_ts": anchor,
        "execution_available": False, "entry_ts": pd.NaT, "exit_ts": pd.NaT,
        "entry_price_native": np.nan, "exit_price_native": np.nan,
        "gross_return_5m": np.nan, "net_return_5m": np.nan,
        "raw_direction": "UNAVAILABLE", "economic_sign": "UNAVAILABLE",
        "unit_notional_net_pnl_1sol": np.nan,
    }
    if g is None or g.empty:
        return base
    lo = anchor + pd.Timedelta(seconds=ENTRY_MIN_S)
    hi = anchor + pd.Timedelta(seconds=ENTRY_MAX_S)
    entries = g[(g["snapshot_time"] >= lo) & (g["snapshot_time"] <= hi)]
    if entries.empty:
        return base
    entry_ts = entries.iloc[0]["snapshot_time"]
    same_entry = entries[entries["snapshot_time"] == entry_ts]
    if same_entry["price_native"].nunique(dropna=True) != 1:
        base["ambiguous_entry_price"] = True
        return base
    entry_px = float(same_entry.iloc[0]["price_native"])
    target = entry_ts + pd.Timedelta(seconds=EXIT_TARGET_S)
    latest = target + pd.Timedelta(seconds=EXIT_TOLERANCE_S)
    exits = g[(g["snapshot_time"] >= target) & (g["snapshot_time"] <= latest)]
    if exits.empty:
        return base
    exit_ts = exits.iloc[0]["snapshot_time"]
    same_exit = exits[exits["snapshot_time"] == exit_ts]
    if same_exit["price_native"].nunique(dropna=True) != 1:
        base["ambiguous_exit_price"] = True
        return base
    exit_px = float(same_exit.iloc[0]["price_native"])
    gross = exit_px / entry_px - 1.0
    net = gross - STRESS
    raw_direction = "UP" if gross > 0 else ("DOWN" if gross < 0 else "FLAT")
    econ = "NET_POSITIVE" if net > 0 else "NET_NONPOSITIVE"
    base.update({
        "execution_available": True,
        "entry_ts": entry_ts,
        "exit_ts": exit_ts,
        "entry_price_native": entry_px,
        "exit_price_native": exit_px,
        "gross_return_5m": gross,
        "net_return_5m": net,
        "raw_direction": raw_direction,
        "economic_sign": econ,
        "unit_notional_net_pnl_1sol": net,
    })
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundary-rows", required=True)
    ap.add_argument("--data-dir", default="pmd_v08_data")
    ap.add_argument("--out-dir", default="pmd_v08_outcomes")
    args = ap.parse_args()

    data_dir = Path(args.data_dir); data_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for name, expected in EXPECTED_SHA256.items():
        p = Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=name, local_dir=str(data_dir)))
        actual = sha256_file(p)
        paths[name] = p; hashes[name] = actual
        if actual != expected:
            receipt = {
                "lab": "PMD-001", "stage": "EXPLORATORY_OUTCOME_OPENING_V08",
                "outcomes_opened": False, "promotion_authority": False,
                "verdict": "V08_ABORT_SOURCE_HASH_MISMATCH",
                "file": name, "expected_sha256": expected, "actual_sha256": actual,
            }
            (out_dir / "v08_exploratory_outcome_summary.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            print(json.dumps(receipt, indent=2, sort_keys=True))
            return 2

    b20 = load_boundaries(Path(args.boundary_rows))

    m = pd.read_parquet(paths["migrations.parquet"], columns=["mint", "migrated_at", "pool_address"])
    t = pd.read_parquet(paths["tokens.parquet"], columns=["mint", "is_mayhem_mode"])
    p = pd.read_parquet(paths["postgard_snapshots.parquet"], columns=["mint", "snapshot_time", "pair_address", "dex_id", "incomplete_data", "price_native"])

    m["migrated_at"] = pd.to_datetime(m["migrated_at"], utc=True)
    base = m.merge(t, on="mint", how="inner", validate="many_to_one")
    base = base[base["pool_address"].notna() & ~base["pool_address"].astype(str).isin(SENTINELS)]
    base = base[~base["is_mayhem_mode"].fillna(False).astype(bool)]
    base = base[base["migrated_at"].dt.date.astype(str) != "2026-07-03"].copy()

    duplicate_mints = int(base["mint"].duplicated(keep=False).sum())
    if duplicate_mints:
        conflicting = base.groupby("mint").agg(n=("mint", "size"), pools=("pool_address", "nunique"), times=("migrated_at", "nunique"))
        conflicts = conflicting[(conflicting["pools"] > 1) | (conflicting["times"] > 1)]
        if len(conflicts):
            raise RuntimeError(f"conflicting duplicate migration rows for {len(conflicts)} mints")
        base = base.drop_duplicates(subset=["mint", "migrated_at", "pool_address"]).copy()

    relevant_mints = set(base["mint"].astype(str)) | set(b20["mint"].astype(str))
    p = p[p["mint"].astype(str).isin(relevant_mints)].copy()
    snap_map = build_snapshot_map(p)

    exact_rows = []
    for r in b20.itertuples(index=False):
        e = evaluate_one(r.mint, r.pool_address, r.boundary_ts, snap_map)
        e.update({
            "crossdate_manifest_index": int(r.crossdate_manifest_index),
            "boundary_variant": str(r.v07_boundary_variant),
            "chain_exact_boundary_ts": r.boundary_ts,
        })
        exact_rows.append(e)
    exact = pd.DataFrame(exact_rows).sort_values("crossdate_manifest_index")
    exact_exec = exact[exact["execution_available"]].copy()

    baseline_rows = []
    for r in base.itertuples(index=False):
        e = evaluate_one(r.mint, r.pool_address, r.migrated_at, snap_map)
        e["corpus_t0"] = r.migrated_at
        baseline_rows.append(e)
    baseline = pd.DataFrame(baseline_rows)
    baseline_exec = baseline[baseline["execution_available"]].copy()

    exact.to_csv(out_dir / "v08_chain_exact_crossdate20_outcomes.csv", index=False)
    baseline_exec.to_csv(out_dir / "v08_frozen_t0_baseline_outcomes.csv", index=False)

    exact_by_variant = {}
    for variant, g in exact_exec.groupby("boundary_variant"):
        exact_by_variant[str(variant)] = summarize(g)

    summary = {
        "lab": "PMD-001",
        "stage": "EXPLORATORY_OUTCOME_OPENING_V08",
        "verdict": "V08_EXPLORATORY_OUTCOMES_OPENED",
        "outcomes_opened": True,
        "promotion_authority": False,
        "confirmatory_status": False,
        "same_corpus_protected_holdout_status": "CONTAMINATED_FOR_POST_V08_FORMULA_SELECTION",
        "policy_authority": "EXPLORATORY_OUTCOME_OPENING_POLICY_AMENDMENT_V08.md",
        "source_sha256": hashes,
        "execution_rule": {
            "entry_min_seconds": ENTRY_MIN_S,
            "entry_max_seconds": ENTRY_MAX_S,
            "exit_target_seconds": EXIT_TARGET_S,
            "exit_tolerance_seconds": EXIT_TOLERANCE_S,
            "round_trip_stress_fraction": STRESS,
        },
        "chain_exact_crossdate20": {
            "frozen_rows": 20,
            "outcome_executable_rows": int(len(exact_exec)),
            "unavailable_rows": int(20 - len(exact_exec)),
            "metrics": summarize(exact_exec),
            "by_boundary_variant": exact_by_variant,
        },
        "frozen_t0_baseline": {
            "clean_pre_execution_population": int(len(base)),
            "expected_execution_available_rows": FROZEN_BASELINE_EXPECTED_N,
            "outcome_executable_rows": int(len(baseline_exec)),
            "matches_frozen_expected_count": bool(len(baseline_exec) == FROZEN_BASELINE_EXPECTED_N),
            "metrics": summarize(baseline_exec),
        },
        "interpretation_guardrails": [
            "isolated unit-notional PnL assumes 1 SOL independently allocated to every observation and is not a portfolio backtest",
            "no feature/outcome correlation or threshold optimization is performed by V0.8",
            "V0.8 cannot promote PMD-001; fresh unseen confirmation is required for any future edge claim",
        ],
    }
    (out_dir / "v08_exploratory_outcome_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=jsonable) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True, default=jsonable))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
