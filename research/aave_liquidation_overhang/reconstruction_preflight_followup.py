#!/usr/bin/env python3
"""AAVE reconstruction R0 follow-up components: token primitives or oracle provenance."""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

import reconstruction_preflight as rp

LAB_ID = rp.LAB_ID


def load_bootstrap() -> dict:
    paths = glob.glob("downloaded_reconstruction_bootstrap/**/AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R0_BOOTSTRAP_V0_1.json", recursive=True)
    if len(paths) != 1:
        raise RuntimeError(f"expected exactly one bootstrap receipt, got {len(paths)}")
    with open(paths[0], "r", encoding="utf-8") as f:
        obj = json.load(f)
    if obj.get("classification") != "RECONSTRUCTION_R0_BOOTSTRAP_PASS":
        raise RuntimeError("bootstrap did not pass")
    return obj


def main() -> int:
    mode = os.environ.get("RECON_MODE", "").strip().lower()
    if mode not in {"token", "oracle"}:
        raise SystemExit("RECON_MODE must be token or oracle")
    bootstrap = load_bootstrap()
    stats = Counter()
    failure = None
    try:
        if mode == "token":
            result = rp.probe_token_primitives(bootstrap["reserves"], stats)
            classification = "RECONSTRUCTION_R0_TOKEN_ROUTE_PASS"
        else:
            result = rp.probe_oracle_events(bootstrap.get("provider_transitions", {}), stats)
            classification = "RECONSTRUCTION_R0_ORACLE_ROUTE_PASS" if result.get("status") == "EVENT_ROUTE_RECOVERED" else "RECONSTRUCTION_PROVENANCE_FAILURE"
    except Exception as exc:
        classification = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        result = {}
        failure = f"{type(exc).__name__}: {str(exc)[:800]}"

    receipt = {
        "lab_id": LAB_ID,
        "phase": f"RECONSTRUCTION_R0_{mode.upper()}_OUTCOME_BLIND",
        "classification": classification,
        "component": mode,
        "result": result,
        "transport_stats": dict(stats),
        "failure": failure,
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
    out = Path("reconstruction_followup_output")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R0_{mode.upper()}_V0_1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "component": mode,
        "classification": classification,
        "event_counts": result.get("event_counts", {}),
        "status": result.get("status"),
        "health_factor_computed": False,
        "overhang_computed": False,
    }, sort_keys=True))
    return 0 if classification in {"RECONSTRUCTION_R0_TOKEN_ROUTE_PASS", "RECONSTRUCTION_R0_ORACLE_ROUTE_PASS"} else 2


if __name__ == "__main__":
    sys.exit(main())
