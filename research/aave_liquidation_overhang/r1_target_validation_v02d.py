#!/usr/bin/env python3
"""AAVE R1 V0.2D — exact target-only archive RPC revalidation.

Loads the immutable failed V0.2A canonical receipt, verifies the exact frozen
77-target population and digest, then reruns only the frozen archive-RPC
scaledBalanceOf validation against the prospectively frozen three-provider set.

No borrower census, delta replay, health factor, overhang, market outcomes,
returns or PnL are computed here.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("base_audit", HERE / "r1_scaled_ledger_audit_v01.py")
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)

UPSTREAM_RUN_ID = 35375172202
UPSTREAM_ARTIFACT_ID = 10560482339
UPSTREAM_ARTIFACT_DIGEST = "sha256:172012d26dc6d4a6f0ea2a534f039f6ce2f73c2361e7975414067c25d6686f9b"
EXPECTED_TARGET_COUNT = 77
PROVIDERS = [
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]


def load_upstream() -> dict:
    files = list(Path("downloaded_v02a").rglob("AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2A.json"))
    if len(files) != 1:
        raise RuntimeError(f"expected exactly one V0.2A audit receipt, found {len(files)}")
    obj = json.loads(files[0].read_text(encoding="utf-8"))
    if obj.get("classification") != "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE":
        raise RuntimeError(f"unexpected upstream classification: {obj.get('classification')}")
    targets = obj.get("validation_targets")
    failures = obj.get("validation_failures")
    if not isinstance(targets, list) or len(targets) != EXPECTED_TARGET_COUNT:
        raise RuntimeError(f"expected {EXPECTED_TARGET_COUNT} frozen targets")
    if int(obj.get("validation_target_count", -1)) != EXPECTED_TARGET_COUNT:
        raise RuntimeError("upstream validation_target_count mismatch")
    if int(obj.get("validation_failure_count", -1)) != EXPECTED_TARGET_COUNT:
        raise RuntimeError("upstream validation_failure_count mismatch")
    if not isinstance(failures, list) or len(failures) != EXPECTED_TARGET_COUNT:
        raise RuntimeError("upstream failure rows are not complete")
    if any(x.get("failure") != "INSUFFICIENT_ARCHIVE_RPC_QUORUM" for x in failures):
        raise RuntimeError("upstream contains non-quorum target failure")

    recomputed = hashlib.sha256(
        "\n".join(
            f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}"
            for t in targets
        ).encode()
    ).hexdigest()
    if recomputed != obj.get("target_digest_sha256"):
        raise RuntimeError("upstream frozen target digest mismatch")
    return obj


def main() -> int:
    out_dir = Path("r1_v02d_output")
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = out_dir / "AAVE_LIQUIDATION_OVERHANG_001_R1_TARGET_VALIDATION_V0_2D.json"

    receipt = {
        "lab_id": "AAVE-LIQUIDATION-OVERHANG-001",
        "phase": "R1_TARGET_VALIDATION_PROVIDER_SET_V0_2D_OUTCOME_BLIND",
        "authority": "AAVE_LIQUIDATION_OVERHANG_001_R1_TARGET_VALIDATION_PROVIDER_SET_AMENDMENT_V0_2D",
        "upstream_run_id": UPSTREAM_RUN_ID,
        "upstream_artifact_id": UPSTREAM_ARTIFACT_ID,
        "upstream_artifact_digest": UPSTREAM_ARTIFACT_DIGEST,
        "provider_set": PROVIDERS,
        "provider_count": len(PROVIDERS),
        "quorum_required": 2,
        "classification": None,
        "failure": None,
        "safety": {
            "borrower_census_recomputed": False,
            "delta_replay_recomputed": False,
            "health_factor_computed": False,
            "overhang_computed": False,
            "market_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026_market_outcomes": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }

    try:
        upstream = load_upstream()
        targets = upstream["validation_targets"]
        receipt["validation_target_count"] = len(targets)
        receipt["target_digest_sha256"] = upstream["target_digest_sha256"]

        # Reuse the frozen V0.2A RPC batching, quorum and exact-equality logic.
        base.RPC_ENDPOINTS = list(PROVIDERS)
        classification, failures, endpoint_stats = base.validate_targets(targets)
        receipt["classification"] = classification
        receipt["validation_failure_count"] = len(failures)
        receipt["validated_target_count"] = len(targets) - len(failures)
        receipt["validation_failures"] = failures
        receipt["archive_rpc_stats"] = endpoint_stats
    except Exception as exc:
        receipt["classification"] = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {str(exc)[:1500]}"

    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "target_count": receipt.get("validation_target_count"),
        "validated_target_count": receipt.get("validated_target_count"),
        "validation_failure_count": receipt.get("validation_failure_count"),
        "provider_count": receipt["provider_count"],
        "quorum_required": receipt["quorum_required"],
        "health_factor_computed": False,
        "overhang_computed": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if receipt["classification"] == "R1_AUDIT_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
