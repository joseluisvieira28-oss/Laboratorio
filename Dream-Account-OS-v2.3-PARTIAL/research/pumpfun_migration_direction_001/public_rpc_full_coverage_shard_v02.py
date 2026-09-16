#!/usr/bin/env python3
"""PMD-001 V0.2 full-population public-RPC coverage census shard.

PRE-OUTCOME / SOURCE-ONLY.

This census does NOT fetch post-migration prices or outcomes. It reconstructs the
already-frozen 1,012 source-executable manifest from metadata/nullness only, then
applies the frozen V0.2A redundant lookup hierarchy uniformly:

1) bonding-curve history first;
2) traverse far enough to cross T0-300s;
3) if curve coverage is unresolved or has no successful signature in
   [T0-300s,T0), query mint history as a redundant transaction index;
4) anchor mint history before the nearest curve-index transaction at/after T0
   when such an anchor is available;
5) union/deduplicate signatures;
6) only successful signatures with blockTime < T0 can enter source counts.

A missing observation is never treated as zero demand unless at least one index
establishes a bounded complete source window. Outcomes remain sealed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import exact_population_public_rpc_probe_v02 as core  # noqa: E402


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    return core.write_jsonl(path, rows)


def query_history(address: str, t0: int, max_pages: int, before: str | None = None) -> tuple[list[dict[str, Any]], bool, str | None, int]:
    out: list[dict[str, Any]] = []
    pages = 0
    error: str | None = None
    boundary_resolved = False
    cursor = before
    while pages < max_pages:
        cfg: dict[str, Any] = {"commitment": "finalized", "limit": core.SIG_LIMIT}
        if cursor:
            cfg["before"] = cursor
        try:
            obj = core.rpc("getSignaturesForAddress", [address, cfg])
        except Exception as exc:
            error = repr(exc)
            break
        pages += 1
        batch = obj.get("result") or []
        if not isinstance(batch, list):
            error = "SIGNATURE_RESULT_SHAPE_FAILURE"
            break
        out.extend(batch)
        if not batch:
            boundary_resolved = True
            break
        times = [int(x["blockTime"]) for x in batch if isinstance(x, dict) and x.get("blockTime") is not None]
        if times and min(times) < t0 - 300:
            boundary_resolved = True
            break
        cursor = batch[-1].get("signature") if isinstance(batch[-1], dict) else None
        if not cursor:
            boundary_resolved = True
            break
        time.sleep(0.18)
    return out, boundary_resolved, error, pages


def successful_pre(sigs: list[dict[str, Any]], t0: int, seconds: int) -> set[str]:
    return {
        str(x["signature"])
        for x in sigs
        if isinstance(x, dict)
        and x.get("signature")
        and x.get("err") is None
        and x.get("blockTime") is not None
        and t0 - seconds <= int(x["blockTime"]) < t0
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-index", type=int, required=True)
    ap.add_argument("--shard-count", type=int, required=True)
    ap.add_argument("--max-pages", type=int, default=20)
    args = ap.parse_args()
    if not (0 <= args.shard_index < args.shard_count):
        raise SystemExit("invalid shard index")

    root = Path(f"artifacts/pmd001_public_rpc_full_coverage_v02/shard_{args.shard_index:02d}")
    data_dir = root / "source_data"
    root.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        paths = core.download_and_verify(data_dir)
        manifest = core.build_exact_manifest(paths)
    except Exception as exc:
        receipt = {
            "lab": "PMD-001", "stage": "PUBLIC_RPC_FULL_COVERAGE_SHARD_V02A",
            "shard_index": args.shard_index, "shard_count": args.shard_count,
            "classification": "FULL_CENSUS_MANIFEST_BUILD_FAILURE", "detail": repr(exc),
            "outcomes_opened": False, "forbidden_outcome_file_acquired": False,
        }
        core.write_json(root / "receipt.json", receipt)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 2

    targets = [(idx, row) for idx, row in enumerate(manifest) if idx % args.shard_count == args.shard_index]
    audit: list[dict[str, Any]] = []
    provider_errors = 0
    pagination_caps = 0
    missing_curve_keys = 0
    fallback_queries = 0
    fallback_recovered_zero_curve_cases = 0

    for local_rank, (manifest_index, row) in enumerate(targets, 1):
        curve = row.get("bonding_curve_key")
        mint = row.get("mint")
        t0 = int(row["t0_epoch"])
        if not curve:
            missing_curve_keys += 1
            audit.append({
                "manifest_index": manifest_index, "mint": mint, "migration_date": row.get("migration_date"), "t0_epoch": t0,
                "n300": None, "n60": None, "n30": None,
                "curve_pages": 0, "mint_pages": 0, "need_mint_fallback": False,
                "curve_boundary_resolved": False, "mint_boundary_resolved": False, "history_boundary_resolved": False,
                "classification": "MISSING_BONDING_CURVE_KEY", "error": "MISSING_BONDING_CURVE_KEY",
            })
            continue

        curve_sigs, curve_boundary, curve_error, curve_pages = query_history(curve, t0, args.max_pages)
        if curve_error:
            provider_errors += 1
        curve300 = successful_pre(curve_sigs, t0, 300) if curve_boundary else set()
        need_fallback = (not curve_boundary) or (not curve300)

        mint_sigs: list[dict[str, Any]] = []
        mint_boundary = False
        mint_error: str | None = None
        mint_pages = 0
        anchor: str | None = None
        if need_fallback:
            fallback_queries += 1
            at_or_after = [
                x for x in curve_sigs
                if isinstance(x, dict) and x.get("signature") and x.get("blockTime") is not None and int(x["blockTime"]) >= t0
            ]
            if at_or_after:
                at_or_after.sort(key=lambda x: (int(x["blockTime"]), str(x["signature"])))
                anchor = str(at_or_after[0]["signature"])
            if mint:
                mint_sigs, mint_boundary, mint_error, mint_pages = query_history(str(mint), t0, args.max_pages, anchor)
                if mint_error:
                    provider_errors += 1

        resolved = curve_boundary or mint_boundary
        if not curve_boundary and curve_error is None:
            pagination_caps += 1
        if need_fallback and mint and not mint_boundary and mint_error is None:
            pagination_caps += 1

        if resolved:
            curve300_all = successful_pre(curve_sigs, t0, 300)
            mint300_all = successful_pre(mint_sigs, t0, 300)
            curve60_all = successful_pre(curve_sigs, t0, 60)
            mint60_all = successful_pre(mint_sigs, t0, 60)
            curve30_all = successful_pre(curve_sigs, t0, 30)
            mint30_all = successful_pre(mint_sigs, t0, 30)
            union300 = curve300_all | mint300_all
            union60 = curve60_all | mint60_all
            union30 = curve30_all | mint30_all
            if need_fallback and not curve300_all and union300:
                fallback_recovered_zero_curve_cases += 1
            n300, n60, n30 = len(union300), len(union60), len(union30)
        else:
            n300 = n60 = n30 = None

        error_parts = [x for x in (curve_error, mint_error) if x]
        audit.append({
            "manifest_index": manifest_index, "mint": mint, "migration_date": row.get("migration_date"),
            "t0_epoch": t0, "bonding_curve_key": curve,
            "need_mint_fallback": need_fallback, "migration_anchor_signature": anchor,
            "curve_pages": curve_pages, "mint_pages": mint_pages,
            "curve_boundary_resolved": curve_boundary, "mint_boundary_resolved": mint_boundary,
            "history_boundary_resolved": resolved,
            "curve_n300": len(successful_pre(curve_sigs, t0, 300)) if curve_boundary else None,
            "mint_n300": len(successful_pre(mint_sigs, t0, 300)) if mint_boundary else None,
            "n300": n300, "n60": n60, "n30": n30,
            "classification": "RESOLVED" if resolved else "UNRESOLVED",
            "error": " | ".join(error_parts) if error_parts else None,
        })

        if local_rank % 25 == 0:
            print(f"shard={args.shard_index} progress={local_rank}/{len(targets)}")
        time.sleep(0.18)

    audit_sha = write_jsonl(root / "coverage_audit.jsonl", audit)
    resolved_rows = [r for r in audit if r.get("classification") == "RESOLVED"]
    receipt = {
        "lab": "PMD-001", "stage": "PUBLIC_RPC_FULL_COVERAGE_SHARD_V02A",
        "shard_index": args.shard_index, "shard_count": args.shard_count,
        "exact_executable_population": len(manifest), "target_rows": len(targets),
        "resolved_rows": len(resolved_rows), "unresolved_rows": len(audit) - len(resolved_rows),
        "rows_with_any_300": sum((r.get("n300") or 0) > 0 for r in resolved_rows),
        "rows_with_any_60": sum((r.get("n60") or 0) > 0 for r in resolved_rows),
        "rows_with_any_30": sum((r.get("n30") or 0) > 0 for r in resolved_rows),
        "fallback_queries": fallback_queries,
        "fallback_recovered_zero_curve_cases": fallback_recovered_zero_curve_cases,
        "provider_errors": provider_errors, "pagination_caps": pagination_caps,
        "missing_curve_keys": missing_curve_keys, "audit_sha256": audit_sha,
        "classification": "CENSUS_SHARD_COMPLETE" if (len(resolved_rows) == len(audit) and missing_curve_keys == 0) else "CENSUS_SHARD_COMPLETE_WITH_UNRESOLVED_SOURCE",
        "outcomes_opened": False, "forbidden_outcome_file_acquired": False,
    }
    core.write_json(root / "receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
