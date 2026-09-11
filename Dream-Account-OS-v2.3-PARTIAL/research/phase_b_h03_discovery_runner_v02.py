from __future__ import annotations

"""H03 Discovery runner V0.2 binding the pre-outcome close-time amendment.

V0.2 delegates all corpus intake, adapter, evaluation, bootstrap, STRESS and classifier
logic to the already-tested V0.1 runner. Its only added responsibility is to verify the
prospectively frozen Binance close-time metadata amendment before delegation and bind
that amendment fingerprint into the final machine-readable receipt.
"""

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from research.phase_b_h03_discovery_runner_v01 import (
    DEFAULT_AUTHORIZATION_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RAW_ROOT,
    run_h03_discovery as run_h03_discovery_v01,
)


EXPECTED_CLOSE_TIME_AMENDMENT_FINGERPRINT = "338c67b4275143d06dcda887b939e5aff8a683ac03c32beb120584c8e70c5f71"
DEFAULT_AMENDMENT_PATH = Path(__file__).with_name("PHASE_B_H03_BINANCE_ADAPTER_CLOSE_TIME_AMENDMENT_V0.1.json")

NETWORK_ACCESS_PERFORMED_BY_RUNNER = False
EXCHANGE_MUTATION_PERFORMED = False
LIVE_TRADING_PERFORMED = False
MEXC_VALIDATION_2025_ACCESSED = False
HOLDOUT_2026_ACCESSED = False


def _canonical_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _load_and_validate_amendment(path: Path = DEFAULT_AMENDMENT_PATH) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    recomputed = _canonical_hash(unsigned)
    if supplied != EXPECTED_CLOSE_TIME_AMENDMENT_FINGERPRINT or recomputed != EXPECTED_CLOSE_TIME_AMENDMENT_FINGERPRINT:
        raise PermissionError("H03 close-time amendment fingerprint mismatch")
    if raw.get("status") != "FROZEN_PRE_OUTCOME_EVALUATION":
        raise PermissionError("H03 close-time amendment status mismatch")
    authority = raw.get("authority_basis") or {}
    if authority.get("first_outcome_evaluation_completed") is not False:
        raise PermissionError("H03 amendment was not frozen pre-outcome")
    if authority.get("performance_metrics_inspected") is not False:
        raise PermissionError("H03 amendment was not frozen pre-performance")
    mapping = raw.get("amended_mapping") or {}
    if mapping.get("canonical_close_time") != "open_time + 900000 - 1":
        raise PermissionError("H03 canonical close-time mapping mismatch")
    locks = raw.get("locks") or {}
    for key in (
        "mexc_2025_09_through_2025_12_authorized",
        "holdout_2026_authorized",
        "exchange_mutation_authorized",
        "live_trading_authorized",
        "main_merge_authorized",
        "render_deploy_authorized",
    ):
        if locks.get(key) is not False:
            raise PermissionError(f"H03 amendment lock mismatch: {key}")
    return raw


def _rewrite_bound_receipt(output_path: Path, receipt: dict[str, Any], amendment: dict[str, Any]) -> dict[str, Any]:
    bound = dict(receipt)
    bound.pop("fingerprint", None)
    bound["close_time_adapter_amendment_fingerprint"] = amendment["fingerprint"]
    bound["close_time_metadata_audit_rows"] = amendment["trigger"]["full_corpus_metadata_audit_rows"]
    bound["pre_outcome_close_time_anomalies_observed"] = amendment["trigger"]["close_time_violations"]
    bound["canonical_close_time_rule"] = amendment["amended_mapping"]["canonical_close_time"]
    bound["fingerprint"] = _canonical_hash(bound)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bound, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return bound


def run_h03_discovery(
    raw_root: Path = DEFAULT_RAW_ROOT,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    authorization_path: Path = DEFAULT_AUTHORIZATION_PATH,
    amendment_path: Path = DEFAULT_AMENDMENT_PATH,
) -> dict[str, Any]:
    amendment = _load_and_validate_amendment(amendment_path)
    receipt = run_h03_discovery_v01(raw_root, output_path, authorization_path)
    return _rewrite_bound_receipt(output_path, receipt, amendment)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    raw_root = Path(args[0]) if len(args) >= 1 else DEFAULT_RAW_ROOT
    output_path = Path(args[1]) if len(args) >= 2 else DEFAULT_OUTPUT_PATH
    authorization_path = Path(args[2]) if len(args) >= 3 else DEFAULT_AUTHORIZATION_PATH
    amendment_path = Path(args[3]) if len(args) >= 4 else DEFAULT_AMENDMENT_PATH
    try:
        receipt = run_h03_discovery(raw_root, output_path, authorization_path, amendment_path)
    except Exception as exc:
        print(f"H03_DISCOVERY_FATAL: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("status") == "H03_DISCOVERY_COMPLETE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
