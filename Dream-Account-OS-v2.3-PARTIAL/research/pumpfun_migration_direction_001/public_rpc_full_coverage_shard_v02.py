#!/usr/bin/env python3
"""PMD-001 V0.2 full-population public-RPC coverage census shard.

PRE-OUTCOME / SOURCE-ONLY.

This census does NOT fetch post-migration prices or outcomes. It reconstructs the
already-frozen 1,012 source-executable manifest from metadata/nullness only, then
asks whether the bonding-curve account has successful Solana signatures strictly
inside [T0-300s, T0), [T0-60s, T0), and [T0-30s, T0).

A missing observation is never treated as zero demand unless the address history
was traversed far enough to cross the lower time boundary. Provider failures and
pagination caps are classified as unresolved source coverage.
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
            "lab":"PMD-001","stage":"PUBLIC_RPC_FULL_COVERAGE_SHARD_V02",
            "shard_index":args.shard_index,"shard_count":args.shard_count,
            "classification":"FULL_CENSUS_MANIFEST_BUILD_FAILURE","detail":repr(exc),
            "outcomes_opened":False,"forbidden_outcome_file_acquired":False,
        }
        core.write_json(root/"receipt.json", receipt)
        print(json.dumps(receipt,indent=2,sort_keys=True)); return 2

    targets = [(idx,row) for idx,row in enumerate(manifest) if idx % args.shard_count == args.shard_index]
    audit: list[dict[str, Any]] = []
    provider_errors = 0
    pagination_caps = 0
    missing_curve_keys = 0

    for local_rank,(manifest_index,row) in enumerate(targets,1):
        curve = row.get("bonding_curve_key")
        if not curve:
            missing_curve_keys += 1
            audit.append({
                "manifest_index":manifest_index,"mint":row["mint"],"t0_epoch":row["t0_epoch"],
                "n300":None,"n60":None,"n30":None,"pages":0,"history_boundary_resolved":False,
                "classification":"MISSING_BONDING_CURVE_KEY",
            })
            continue

        before = None
        pages = 0
        all_sigs: list[dict[str, Any]] = []
        error: str | None = None
        boundary_resolved = False
        while pages < args.max_pages:
            cfg: dict[str, Any] = {"commitment":"finalized","limit":core.SIG_LIMIT}
            if before:
                cfg["before"] = before
            try:
                obj = core.rpc("getSignaturesForAddress", [curve, cfg])
            except Exception as exc:
                error = repr(exc); provider_errors += 1; break
            pages += 1
            batch = obj.get("result") or []
            if not isinstance(batch,list):
                error="SIGNATURE_RESULT_SHAPE_FAILURE"; provider_errors += 1; break
            all_sigs.extend(batch)
            if not batch:
                boundary_resolved = True
                break
            times = [int(x["blockTime"]) for x in batch if isinstance(x,dict) and x.get("blockTime") is not None]
            if times and min(times) < row["t0_epoch"] - 300:
                boundary_resolved = True
                break
            before = batch[-1].get("signature") if isinstance(batch[-1],dict) else None
            if not before:
                boundary_resolved = True
                break
            time.sleep(0.18)

        if not boundary_resolved and error is None:
            pagination_caps += 1
            error = "PAGINATION_CAP_BEFORE_T0_MINUS_300_BOUNDARY"

        good = [
            x for x in all_sigs
            if isinstance(x,dict) and x.get("signature") and x.get("err") is None
            and x.get("blockTime") is not None and int(x["blockTime"]) < row["t0_epoch"]
        ]
        n300 = sum(row["t0_epoch"]-300 <= int(x["blockTime"]) < row["t0_epoch"] for x in good) if boundary_resolved else None
        n60 = sum(row["t0_epoch"]-60 <= int(x["blockTime"]) < row["t0_epoch"] for x in good) if boundary_resolved else None
        n30 = sum(row["t0_epoch"]-30 <= int(x["blockTime"]) < row["t0_epoch"] for x in good) if boundary_resolved else None
        times_all = [int(x["blockTime"]) for x in all_sigs if isinstance(x,dict) and x.get("blockTime") is not None]
        audit.append({
            "manifest_index":manifest_index,"mint":row["mint"],"migration_date":row["migration_date"],
            "t0_epoch":row["t0_epoch"],"bonding_curve_key":curve,"pages":pages,
            "signatures_total_returned":len(all_sigs),"oldest_returned_block_time":min(times_all) if times_all else None,
            "history_boundary_resolved":boundary_resolved,"n300":n300,"n60":n60,"n30":n30,
            "classification":"RESOLVED" if boundary_resolved else "UNRESOLVED","error":error,
        })
        if local_rank % 25 == 0:
            print(f"shard={args.shard_index} progress={local_rank}/{len(targets)}")
        time.sleep(0.18)

    audit_sha = write_jsonl(root/"coverage_audit.jsonl", audit)
    resolved = [r for r in audit if r.get("classification") == "RESOLVED"]
    receipt = {
        "lab":"PMD-001","stage":"PUBLIC_RPC_FULL_COVERAGE_SHARD_V02",
        "shard_index":args.shard_index,"shard_count":args.shard_count,
        "exact_executable_population":len(manifest),"target_rows":len(targets),
        "resolved_rows":len(resolved),"unresolved_rows":len(audit)-len(resolved),
        "rows_with_any_300":sum((r.get("n300") or 0)>0 for r in resolved),
        "rows_with_any_60":sum((r.get("n60") or 0)>0 for r in resolved),
        "rows_with_any_30":sum((r.get("n30") or 0)>0 for r in resolved),
        "provider_errors":provider_errors,"pagination_caps":pagination_caps,
        "missing_curve_keys":missing_curve_keys,"audit_sha256":audit_sha,
        "classification":"CENSUS_SHARD_COMPLETE" if provider_errors==0 and pagination_caps==0 and missing_curve_keys==0 else "CENSUS_SHARD_COMPLETE_WITH_UNRESOLVED_SOURCE",
        "outcomes_opened":False,"forbidden_outcome_file_acquired":False,
    }
    core.write_json(root/"receipt.json",receipt)
    print(json.dumps(receipt,indent=2,sort_keys=True))
    # Provider/coverage incompleteness is scientific evidence, not a workflow crash.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
