#!/usr/bin/env python3
import io, json, os, sys, urllib.parse, urllib.request, zipfile
from pathlib import Path

import discovery_v03 as base

BINDING_ROUTE_ID = "BSD-SOURCE-BIND-REM-001"
SOURCE_URL = "https://api.blockchain.info/charts/n-transactions"
SOURCE_PARAMS = {
    "start": "2017-01-01",
    "timespan": "2921days",
    "format": "json",
    "sampled": "false",
}
MANIFEST_PATH = Path("research/btc_settlement_demand/frozen_source_v02/source_manifest.json")

def reacquire_canonical_source_zip():
    url = SOURCE_URL + "?" + urllib.parse.urlencode(SOURCE_PARAMS)
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "crypto-lab-bsd-bindfix/0.3",
    })
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
    except Exception as e:
        base.terminal(
            "TECHNICAL_FAILURE_PREOUTCOME",
            f"Canonical source reacquisition failed: {type(e).__name__}: {e}",
            {"source_binding_route": BINDING_ROUTE_ID},
            70,
        )
    got = base.sha256_bytes(raw)
    if got != base.SOURCE_RAW_SHA256:
        base.terminal(
            "PROVENANCE_FAILURE",
            "Reacquired Blockchain source bytes do not match canonical Source Gate raw SHA256",
            {"source_binding_route": BINDING_ROUTE_ID, "expected": base.SOURCE_RAW_SHA256, "got": got},
            71,
        )
    if not MANIFEST_PATH.exists():
        base.terminal("TECHNICAL_FAILURE_PREOUTCOME", "Embedded canonical source manifest missing", {"source_binding_route":BINDING_ROUTE_ID}, 72)
    manifest = MANIFEST_PATH.read_bytes()
    msha = base.sha256_bytes(manifest)
    if msha != base.SOURCE_MANIFEST_SHA256:
        base.terminal(
            "PROVENANCE_FAILURE",
            "Embedded canonical Source Gate manifest SHA256 mismatch",
            {"source_binding_route": BINDING_ROUTE_ID, "expected": base.SOURCE_MANIFEST_SHA256, "got": msha},
            73,
        )
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("raw_n_transactions.json", raw)
        z.writestr("source_manifest.json", manifest)
    return bio.getvalue()

def preflight_fix():
    base.verify_authority()
    synthetic_zip = reacquire_canonical_source_zip()
    tx = base.extract_bound_source(synthetic_zip)
    obj = {
        "family_id": base.FAMILY_ID,
        "mve_id": base.MVE_ID,
        "phase": "PREOUTCOME_PREFLIGHT",
        "status": "PREOUTCOME_PREFLIGHT_PASS",
        "authority_sha256": base.AUTHORITY_SHA256,
        "source_gate_id": base.SOURCE_GATE_ID,
        "source_artifact_id_lineage": base.SOURCE_ARTIFACT_ID,
        "source_artifact_zip_sha256_lineage": base.SOURCE_ARTIFACT_ZIP_SHA256,
        "source_binding_route": BINDING_ROUTE_ID,
        "source_binding_note": "Exact source call reacquired; raw bytes required to match canonical Source Gate SHA256 before any market outcomes.",
        "source_raw_sha256": base.SOURCE_RAW_SHA256,
        "source_manifest_sha256": base.SOURCE_MANIFEST_SHA256,
        "source_days": len(tx),
        "source_first": min(tx).isoformat(),
        "source_last": max(tx).isoformat(),
        "price_values_opened": False,
        "returns_computed": False,
        "pnl_computed": False,
        **base.FLAGS,
    }
    base.write_json(base.OUT / "preoutcome_preflight.json", obj)
    print(json.dumps(obj, indent=2, sort_keys=True))
    return tx

base.preflight = preflight_fix

def main():
    branch = os.environ.get("GITHUB_REF_NAME", "")
    if branch and branch != "btc-settlement-demand-v0.3-discovery-bindfix":
        base.terminal(
            "TECHNICAL_FAILURE_PREOUTCOME",
            "Wrong branch for technical source-binding remediation",
            {"branch": branch, "source_binding_route": BINDING_ROUTE_ID},
            74,
        )
    if "--preflight-only" in sys.argv:
        preflight_fix()
        return 0
    if "--discovery" in sys.argv:
        return base.discovery()
    print("Use --preflight-only or --discovery", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
