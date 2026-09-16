#!/usr/bin/env python3
"""Final PMD-001 V0.7 full-population source gate aggregation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_ROWS = 1012
MIN_ELIGIBLE = 1000
MIN_ELIGIBLE_DATES = 20


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    files = sorted(Path(args.input_root).rglob("source_rebuild_summary.jsonl"))
    rows: list[dict] = []
    malformed = 0
    for p in files:
        try:
            parts = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
            rows.extend(parts)
        except Exception:
            malformed += 1

    mints = [r.get("mint") for r in rows]
    outcomes_closed = all(r.get("outcomes_opened") is False for r in rows)
    stage_ok = all(r.get("stage") == "CHAIN_EXACT_SOURCE_REBUILD_V07" for r in rows)
    parser_ok = all(r.get("boundary_parser_version") == "V07_MIGRATE_AND_MIGRATE_V2" for r in rows)
    eligible_rows = [r for r in rows if bool(r.get("feature_source_eligible"))]
    eligible_dates = {str(r.get("t0"))[:10] for r in eligible_rows if r.get("t0")}
    source_complete = sum(bool(r.get("source_complete")) for r in rows)

    reconciliation_ok = (
        len(files) == 4 and len(rows) == EXPECTED_ROWS
        and len(mints) == EXPECTED_ROWS and None not in mints
        and len(set(mints)) == EXPECTED_ROWS
        and malformed == 0 and outcomes_closed and stage_ok and parser_ok
    )
    if not reconciliation_ok:
        verdict = "CHAIN_EXACT_SOURCE_GATE_V07_TECHNICAL_INCOMPLETE"
    elif len(eligible_rows) >= MIN_ELIGIBLE and len(eligible_dates) >= MIN_ELIGIBLE_DATES:
        verdict = "CHAIN_EXACT_SOURCE_GATE_V07_PASS"
    else:
        verdict = "CHAIN_EXACT_SOURCE_GATE_V07_INSUFFICIENT_SAMPLE"

    sorted_rows = sorted(rows, key=lambda r: (str(r.get("t0")), str(r.get("mint"))))
    canon = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in sorted_rows)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "chain_exact_source_gate_v07_rows.jsonl").write_text(canon, encoding="utf-8")
    receipt = {
        "lab": "PMD-001",
        "stage": "CHAIN_EXACT_SOURCE_GATE_V07",
        "economic_outcomes_opened": False,
        "expected_rows": EXPECTED_ROWS,
        "summary_files": len(files),
        "rows": len(rows),
        "unique_mints": len(set(mints)),
        "malformed_inputs": malformed,
        "outcome_wall_intact": outcomes_closed,
        "parser_version_ok": parser_ok,
        "source_complete_rows": source_complete,
        "feature_source_eligible_rows": len(eligible_rows),
        "minimum_eligible_rows": MIN_ELIGIBLE,
        "eligible_distinct_dates": len(eligible_dates),
        "minimum_eligible_dates": MIN_ELIGIBLE_DATES,
        "rows_sha256": hashlib.sha256(canon.encode()).hexdigest(),
        "verdict": verdict,
    }
    (out / "chain_exact_source_gate_v07_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if verdict == "CHAIN_EXACT_SOURCE_GATE_V07_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
