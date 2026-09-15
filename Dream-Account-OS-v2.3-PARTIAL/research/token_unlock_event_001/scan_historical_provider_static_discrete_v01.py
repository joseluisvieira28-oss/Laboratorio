from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

LAB_ID = "TOKEN-UNLOCK-EVENT-001"
MVE_ID = "TUE-CLIFF-ADV30-001"

SNAPSHOTS = {
    "2023-03-17": {
        "repo": "0xnirmal/emissions-adapters",
        "commit": "539e7cf40a4cecc73953f3ae2b196b3fa66ae34a",
        "known_at_utc": "2023-03-17T16:43:59Z",
    },
    "2024-03-25": {
        "repo": "danaugrs/emissions-adapters",
        "commit": "ad6bcfa961d6f0bd9cd5d589656b8f78daf7be7a",
        "known_at_utc": "2024-03-25T22:11:28Z",
    },
}

PATTERNS = {
    "manualCliff_call": re.compile(r"\bmanualCliff\s*\("),
    "manualStep_call": re.compile(r"\bmanualStep\s*\("),
    "literal_cliff_type": re.compile(r"\btype\s*:\s*['\"]cliff['\"]"),
    "literal_step_type": re.compile(r"\btype\s*:\s*['\"]step['\"]"),
}


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: scanner.py SNAPSHOT_ROOT SNAPSHOT_ID OUT_JSON")
    root = Path(sys.argv[1]).resolve()
    snapshot_id = sys.argv[2]
    out = Path(sys.argv[3]).resolve()
    cfg = SNAPSHOTS.get(snapshot_id)
    if cfg is None:
        raise RuntimeError(f"unknown snapshot: {snapshot_id}")

    protocols = root / "protocols"
    if not protocols.is_dir():
        raise RuntimeError(f"missing protocols directory: {protocols}")

    candidates = []
    scanned = 0
    for p in sorted(protocols.glob("*.ts")):
        scanned += 1
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        hits = {name: len(rx.findall(text)) for name, rx in PATTERNS.items()}
        total_hits = sum(hits.values())
        if total_hits == 0:
            continue
        candidates.append({
            "file": p.name,
            "path": f"protocols/{p.name}",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "pattern_hits": hits,
            "total_discrete_pattern_hits": total_hits,
        })

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "mode": "SOURCE_ONLY_STATIC_COVERAGE_SCAN",
        "snapshot": snapshot_id,
        "source_repo": cfg["repo"],
        "source_commit": cfg["commit"],
        "known_at_utc": cfg["known_at_utc"],
        "protocol_files_scanned": scanned,
        "candidate_files_count": len(candidates),
        "candidate_files": candidates,
        "guards": {
            "protocol_modules_executed": False,
            "schedule_rows_evaluated": False,
            "binance_accessed": False,
            "market_data_accessed": False,
            "price_data_accessed": False,
            "returns_computed": False,
            "pnl_computed": False,
            "profit_factor_computed": False,
            "year_2025_opened": False,
            "year_2026_opened": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
        "interpretation": "Coverage audit only. Candidate presence does not qualify a token/event and does not authorize Discovery.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
