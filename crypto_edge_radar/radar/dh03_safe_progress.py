from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "DH03_SAFE_PROGRESS_V0.1"
STRATEGY_ID = "HTF-DH03-12H-STANDALONE-FORWARD-V1"
ALLOWED_COUNT_KEYS = (
    "signals",
    "price_exits",
    "final_resolutions",
    "funding_pending",
    "unresolved_price_paths",
    "overlap_skipped",
)


class DH03SafeProgressError(RuntimeError):
    pass


def _nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise DH03SafeProgressError(f"invalid boolean count:{name}")
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise DH03SafeProgressError(f"invalid count:{name}") from exc
    if out < 0:
        raise DH03SafeProgressError(f"negative count:{name}")
    return out


def sanitize_receipt(receipt: dict[str, Any], *, run_id: int) -> dict[str, Any]:
    if receipt.get("strategy_id") != STRATEGY_ID:
        raise DH03SafeProgressError("strategy identity mismatch")
    status = str(receipt.get("status") or "")
    if status not in {"OK", "WAITING_FIRST_ELIGIBLE_ARCHIVE_DAY", "WAITING_ARCHIVE_PUBLICATION"}:
        raise DH03SafeProgressError(f"collector status not safe for publication:{status}")

    totals = ((receipt.get("evaluation") or {}).get("totals") or {})
    if status == "OK":
        counts = {
            key: _nonnegative_int(totals.get(key), key)
            for key in ALLOWED_COUNT_KEYS
        }
    else:
        counts = {key: 0 for key in ALLOWED_COUNT_KEYS}

    return {
        "schema_version": SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "source_workflow_run_id": _nonnegative_int(run_id, "source_workflow_run_id"),
        "checked_at_utc": receipt.get("checked_at_utc"),
        "latest_archive_day": receipt.get("latest_archive_day"),
        "collector_status": status,
        "used_as_forward_evidence": bool(receipt.get("used_as_forward_evidence", False)),
        "counts": counts,
        "outcomes_included": False,
        "prices_included": False,
        "returns_included": False,
        "r_multiples_included": False,
        "profit_factor_included": False,
        "trade_rows_included": False,
        "symbol_breakdown_included": False,
        "science_changed": False,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }


def validate_safe_payload(payload: dict[str, Any], *, expected_run_id: int | None = None) -> dict[str, Any]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise DH03SafeProgressError("schema version mismatch")
    if payload.get("strategy_id") != STRATEGY_ID:
        raise DH03SafeProgressError("strategy identity mismatch")

    run_id = _nonnegative_int(payload.get("source_workflow_run_id"), "source_workflow_run_id")
    if expected_run_id is not None and run_id != int(expected_run_id):
        raise DH03SafeProgressError(
            f"workflow run mismatch:{run_id}:{int(expected_run_id)}"
        )

    for key in (
        "outcomes_included",
        "prices_included",
        "returns_included",
        "r_multiples_included",
        "profit_factor_included",
        "trade_rows_included",
        "symbol_breakdown_included",
        "science_changed",
        "authenticated_exchange_api_used",
        "orders_created",
        "exchange_mutation_performed",
        "live_capital_enabled",
    ):
        if payload.get(key) is not False:
            raise DH03SafeProgressError(f"firewall field not false:{key}")

    counts = payload.get("counts")
    if not isinstance(counts, dict):
        raise DH03SafeProgressError("counts missing")
    if set(counts) != set(ALLOWED_COUNT_KEYS):
        raise DH03SafeProgressError("count keys mismatch")
    normalized = {
        key: _nonnegative_int(counts.get(key), key)
        for key in ALLOWED_COUNT_KEYS
    }

    allowed_top = {
        "schema_version",
        "strategy_id",
        "source_workflow_run_id",
        "checked_at_utc",
        "latest_archive_day",
        "collector_status",
        "used_as_forward_evidence",
        "counts",
        "outcomes_included",
        "prices_included",
        "returns_included",
        "r_multiples_included",
        "profit_factor_included",
        "trade_rows_included",
        "symbol_breakdown_included",
        "science_changed",
        "authenticated_exchange_api_used",
        "orders_created",
        "exchange_mutation_performed",
        "live_capital_enabled",
    }
    extra = sorted(set(payload) - allowed_top)
    if extra:
        raise DH03SafeProgressError(f"unexpected top-level fields:{extra}")

    out = dict(payload)
    out["source_workflow_run_id"] = run_id
    out["counts"] = normalized
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    payload = sanitize_receipt(receipt, run_id=args.run_id)
    payload = validate_safe_payload(payload, expected_run_id=args.run_id)
    target = Path(args.output)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
