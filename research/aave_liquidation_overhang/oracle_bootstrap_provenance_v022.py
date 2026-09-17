#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 oracle bootstrap provenance V0.2.2.

Transport-only correction to V0.2.1: paginate SQD by the last returned block,
instead of assuming one HTTP response exhausts a requested block window.
Scientific identities/event routes/gates are unchanged and outcome-blind.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import oracle_bootstrap_provenance_v021 as v


def paginated_query_logs(start: int, end: int, filters: list[dict[str, Any]], fields: dict[str, bool], stats):
    cursor = start
    while cursor <= end:
        request_to = min(end, cursor + v.WINDOW - 1)
        body = {
            "type":"evm","fromBlock":cursor,"toBlock":request_to,
            "fields":{"block":{"number":True,"timestamp":True},"log":fields},
            "logs":filters,
        }
        r = v.post(body, stats)
        last = None; rows = 0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj = json.loads(raw)
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(f"portal error: {obj['error']}")
                h = obj.get("header") or obj.get("block") or {}
                bn = int(h["number"]); ts = int(h["timestamp"])
                if not (cursor <= bn <= request_to):
                    raise RuntimeError("row outside requested window")
                if ts > v.MAX_TS:
                    raise RuntimeError("PROTECTED_PERIOD_TIMESTAMP_REJECTED")
                if last is not None and bn < last:
                    raise RuntimeError("non-monotonic SQD rows")
                last = bn; rows += 1
                yield obj
        finally:
            r.close()
        stats["portal_rows"] += rows
        stats["http_pages"] += 1
        if rows == 0 or last is None:
            stats["empty_pages"] += 1
            cursor = request_to + 1
        else:
            if last < cursor:
                raise RuntimeError("SQD pagination failed to advance")
            cursor = last + 1


def main() -> int:
    # Replace only the transport iterator used by the already-frozen V0.2.1 logic.
    v.query_logs = paginated_query_logs
    rc = v.main()
    src = Path("oracle_bootstrap_v021_output/AAVE_LIQUIDATION_OVERHANG_001_ORACLE_BOOTSTRAP_RECEIPT_V0_2_1.json")
    if not src.exists():
        return rc
    receipt = json.loads(src.read_text(encoding="utf-8"))
    receipt["phase"] = "ORACLE_BOOTSTRAP_PROVENANCE_V0_2_2_OUTCOME_BLIND"
    receipt["transport_pagination_fix_applied"] = True
    if receipt.get("classification") == "ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2_1":
        receipt["classification"] = "ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2_2"
    out = Path("oracle_bootstrap_v022_output"); out.mkdir(parents=True, exist_ok=True)
    dst = out / "AAVE_LIQUIDATION_OVERHANG_001_ORACLE_BOOTSTRAP_RECEIPT_V0_2_2.json"
    dst.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({
        "classification":receipt.get("classification"),
        "transition_count":len(receipt.get("provider_oracle_registry_transitions") or []),
        "active_oracle_at_activation":receipt.get("active_oracle_at_activation"),
        "oracle_bootstrap_event_counts":receipt.get("oracle_bootstrap_event_counts"),
        "transport_stats":receipt.get("transport_stats"),
        "health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False,
    }, sort_keys=True))
    return 0 if receipt.get("classification") == "ORACLE_BOOTSTRAP_PROVENANCE_PASS_V0_2_2" else 2

if __name__ == "__main__":
    sys.exit(main())
