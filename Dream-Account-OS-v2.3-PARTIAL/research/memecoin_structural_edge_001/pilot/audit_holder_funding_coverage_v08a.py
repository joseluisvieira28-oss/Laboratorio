#!/usr/bin/env python3
"""MSEL-001 V0.8A holder funding coverage lineage binder.

LOCAL-ONLY / READ-ONLY / OUTCOMES LOCKED.

Technical purpose only:
- bind the existing V0.8 holder-coverage audit to the corrected T+5 V0.2
  source manifest produced after the historical Pump BUY/SELL account-map fix;
- verify the source collector identifies itself as the V0.2 account-map collector;
- preserve every V0.8 holder/funding/clustering rule unchanged.

No feature threshold, cohort, horizon, funding rule, cluster rule, outcome, cost,
or trading logic is changed here.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import audit_holder_funding_coverage_v08 as base

EXPECTED_V02_SOURCE_MANIFEST_SHA256 = "11c296c98baa5a7005db5d0e72dd0151668799dafb007a02e68985841c9b3e48"
EXPECTED_V02_COLLECTOR = "MSEL_T5_FORENSIC_BLOCKSCAN_V02_ACCOUNTMAP"


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    manifest_path = here / "data" / "msel001_t5_forensics" / "source_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"MISSING_V02_SOURCE_MANIFEST {manifest_path}")

    actual = sha256_bytes(manifest_path.read_bytes())
    if actual != EXPECTED_V02_SOURCE_MANIFEST_SHA256:
        raise RuntimeError(
            f"V02_SOURCE_MANIFEST_HASH_MISMATCH expected={EXPECTED_V02_SOURCE_MANIFEST_SHA256} actual={actual}"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("collector") != EXPECTED_V02_COLLECTOR:
        raise RuntimeError(
            f"V02_COLLECTOR_ID_MISMATCH expected={EXPECTED_V02_COLLECTOR} actual={manifest.get('collector')}"
        )
    if manifest.get("outcomes_opened") is not False:
        raise RuntimeError("OUTCOME_LOCK_STATE_FAILURE")

    # V0.8's only stale lineage constant is the source-manifest hash. The holder
    # ledger itself is reconstructed by the unchanged base token-balance logic;
    # the V0.2 correction affects historical Pump trade wallet account mapping.
    base.EXPECTED_V01_SOURCE_MANIFEST_SHA256 = EXPECTED_V02_SOURCE_MANIFEST_SHA256
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
