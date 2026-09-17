#!/usr/bin/env python3
"""Final aggregate for AAVE-LIQUIDATION-OVERHANG-001 reconstruction R0 preflight."""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"


def one(pattern: str) -> dict:
    paths = glob.glob(pattern, recursive=True)
    if len(paths) != 1:
        raise RuntimeError(f"expected one file for {pattern}, got {len(paths)}")
    with open(paths[0], "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    failure = None
    try:
        bootstrap = one("downloaded_reconstruction_parts/**/AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R0_BOOTSTRAP_V0_1.json")
        token = one("downloaded_reconstruction_parts/**/AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R0_TOKEN_V0_1.json")
        oracle = one("downloaded_reconstruction_parts/**/AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R0_ORACLE_V0_1.json")

        if bootstrap.get("classification") != "RECONSTRUCTION_R0_BOOTSTRAP_PASS":
            raise RuntimeError("bootstrap component did not pass")
        if token.get("classification") != "RECONSTRUCTION_R0_TOKEN_ROUTE_PASS":
            raise RuntimeError("token component did not pass")
        if oracle.get("classification") != "RECONSTRUCTION_R0_ORACLE_ROUTE_PASS":
            # Keep governance vocabulary fail-closed. Missing oracle bootstrap provenance
            # is a provenance failure, not a new ad-hoc terminal class.
            classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
        else:
            counts = bootstrap.get("config_provider_event_counts", {})
            required_config_ok = int(counts.get("ReserveInitialized", 0)) > 0 and int(counts.get("CollateralConfigurationChanged", 0)) > 0
            modes = {str(k): int(v) for k, v in (bootstrap.get("borrow_interest_rate_mode_counts") or {}).items()}
            mode_ok = int(bootstrap.get("borrow_event_count", 0)) > 0 and set(modes).issubset({"2"}) and int(modes.get("2", 0)) > 0
            t = token.get("result", {})
            te = t.get("event_counts", {})
            token_ok = (
                int(te.get("aToken_BalanceTransfer", 0)) > 0 and
                int(te.get("aToken_Mint", 0)) > 0 and
                int(te.get("aToken_Burn", 0)) > 0 and
                int(te.get("vDebt_Mint", 0)) > 0 and
                int(te.get("vDebt_Burn", 0)) > 0 and
                int(t.get("abi_shape_failures", 0)) == 0
            )
            if not required_config_ok or int(bootstrap.get("reserve_count", 0)) < 1:
                classification = "RECONSTRUCTION_INSUFFICIENT_COVERAGE"
            elif not mode_ok:
                classification = "RECONSTRUCTION_PROVENANCE_FAILURE"
            elif not token_ok:
                classification = "RECONSTRUCTION_RECONCILIATION_FAILURE"
            else:
                classification = "RECONSTRUCTION_R0_PREFLIGHT_PASS"
    except Exception as exc:
        bootstrap = {}; token = {}; oracle = {}
        classification = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:800]}"

    receipt = {
        "lab_id": LAB_ID,
        "phase": "RECONSTRUCTION_R0_PREFLIGHT_AGGREGATE_OUTCOME_BLIND",
        "classification": classification,
        "bootstrap": bootstrap,
        "token_component": token,
        "oracle_component": oracle,
        "failure": failure,
        "interpretation": "R0 preflight only; RECONSTRUCTION_DATA_PASS requires the separately frozen full replay/reconciliation gate.",
        "safety": {
            "source_values_decoded": True,
            "health_factor_computed": False,
            "overhang_computed": False,
            "future_liquidation_outcome_computed": False,
            "market_return_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    out = Path("reconstruction_output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_PREFLIGHT_RECEIPT_V0_1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "lab_id": LAB_ID,
        "classification": classification,
        "reserve_count": bootstrap.get("reserve_count"),
        "borrow_event_count": bootstrap.get("borrow_event_count"),
        "borrow_modes": bootstrap.get("borrow_interest_rate_mode_counts"),
        "token_event_counts": (token.get("result") or {}).get("event_counts", {}),
        "oracle_status": (oracle.get("result") or {}).get("status"),
        "health_factor_computed": False,
        "overhang_computed": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "RECONSTRUCTION_R0_PREFLIGHT_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
