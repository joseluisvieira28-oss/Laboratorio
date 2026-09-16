#!/usr/bin/env python3
"""PMD-001 source-rebuild coverage/integrity gate.

Consumes only the outcome-blind source manifest and archival collection summaries.
It MUST NOT read post-migration prices, returns, PnL, direction labels or outcome files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MIN_TOTAL = 1000
MIN_VALIDATION = 200
MIN_HOLDOUT = 200
MIN_DATES = 20
EXPECTED_CEILING = 1012


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--receipt", default="pmd_source_rebuild_coverage_gate_v01.json")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    summary_path = Path(args.summary)
    manifest = read_jsonl(manifest_path)
    summaries = read_jsonl(summary_path)

    manifest_by = {}
    duplicate_manifest = []
    for r in manifest:
        m = r["mint"]
        if m in manifest_by:
            duplicate_manifest.append(m)
        manifest_by[m] = r

    summary_by = {}
    duplicate_summary = []
    for r in summaries:
        m = r["mint"]
        if m in summary_by:
            duplicate_summary.append(m)
        summary_by[m] = r

    extra = sorted(set(summary_by) - set(manifest_by))
    missing = sorted(set(manifest_by) - set(summary_by))

    eligible = []
    incomplete = []
    zero_target = []
    errors = []
    for mint, base in manifest_by.items():
        s = summary_by.get(mint)
        if not s:
            continue
        if s.get("collector_error"):
            errors.append(mint)
            continue
        if not s.get("source_complete"):
            incomplete.append(mint)
            continue
        # Preserve the prior final-window raw-evidence eligibility rule. A complete
        # archive with no qualifying Pump mint/PDA transaction is recorded but does
        # not silently become an observed zero-demand token for this V0.1 population.
        if int(s.get("valid_target_pump_transactions") or 0) < 1:
            zero_target.append(mint)
            continue
        eligible.append(base)

    eligible.sort(key=lambda x: (str(x["t0"]), x["mint"]))
    dates = sorted({str(r["t0"])[:10] for r in eligible})
    n = len(eligible)
    discovery = int(n * 0.60)
    validation = int(n * 0.20)
    holdout = n - discovery - validation

    structural_ok = (
        not duplicate_manifest
        and not duplicate_summary
        and not extra
        and len(manifest) == EXPECTED_CEILING
    )
    sample_ok = (
        n >= MIN_TOTAL
        and validation >= MIN_VALIDATION
        and holdout >= MIN_HOLDOUT
        and len(dates) >= MIN_DATES
    )

    receipt = {
        "lab": "PMD-001",
        "stage": "SOURCE_REBUILD_COVERAGE_GATE_V01",
        "outcomes_opened": False,
        "manifest_sha256": sha256_file(manifest_path),
        "summary_sha256": sha256_file(summary_path),
        "manifest_rows": len(manifest),
        "expected_pre_feature_ceiling": EXPECTED_CEILING,
        "summary_unique_mints": len(summary_by),
        "missing_summary_mints": len(missing),
        "extra_summary_mints": len(extra),
        "duplicate_manifest_mints": len(duplicate_manifest),
        "duplicate_summary_mints": len(duplicate_summary),
        "collector_error_mints": len(errors),
        "source_incomplete_mints": len(incomplete),
        "complete_but_zero_target_pump_tx_mints": len(zero_target),
        "eligible_rebuilt_mints": n,
        "eligible_distinct_dates": len(dates),
        "prospective_frozen_count_split_sizes": {
            "discovery": discovery,
            "validation": validation,
            "holdout": holdout,
        },
        "thresholds": {
            "total": MIN_TOTAL,
            "validation": MIN_VALIDATION,
            "holdout": MIN_HOLDOUT,
            "distinct_dates": MIN_DATES,
        },
        "structural_integrity_pass": structural_ok,
        "sample_gate_pass": sample_ok,
        "verdict": "SOURCE_REBUILD_GATE_PASS" if structural_ok and sample_ok else "SOURCE_REBUILD_GATE_FAIL_CLOSED",
        "next_authorized_stage": "FEATURE_FORMULA_FREEZE_V01" if structural_ok and sample_ok else None,
    }

    Path(args.receipt).write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["verdict"] == "SOURCE_REBUILD_GATE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
