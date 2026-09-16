#!/usr/bin/env python3
"""MSEL-002 source/prevalence collector V0.2 technical transport wrapper.

READ-ONLY / RESEARCH-ONLY / ECONOMIC OUTCOMES LOCKED.

This wrapper preserves the frozen scientific collector V0.1 unchanged and only
adds retry/backoff for JSON-RPC item-level HTTP-like 429 responses returned
inside otherwise-successful batch responses. No scientific parameter, source
window, identity rule, sample gate, outcome rule, or feature definition changes.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, List, Tuple

import collect_onchain_identity_prevalence_v01 as v1


def resilient_batch(self: v1.Rpc, calls: List[Tuple[str, list]], label: str) -> List[Any]:
    payload = []
    ids = []
    for method, params in calls:
        self.request_id += 1
        ids.append(self.request_id)
        payload.append({"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params})

    max_item_retries = int(os.environ.get("MSEL_ITEM_RETRIES", "12"))
    backoff = float(os.environ.get("MSEL_ITEM_BACKOFF_START", "2.0"))
    backoff_cap = float(os.environ.get("MSEL_ITEM_BACKOFF_CAP", "30.0"))

    for attempt in range(max_item_retries + 1):
        blob = self._post(payload, f"{label}_itemtry{attempt:02d}")
        obj = json.loads(blob)
        if not isinstance(obj, list):
            raise RuntimeError(f"BATCH_RESPONSE_NOT_LIST {label}")
        by_id = {int(x.get("id")): x for x in obj if isinstance(x, dict) and x.get("id") is not None}
        missing = [rid for rid in ids if rid not in by_id]
        if missing:
            raise RuntimeError(f"BATCH_MISSING_ID {missing[0]} {label}")

        errors = [(rid, by_id[rid].get("error")) for rid in ids if by_id[rid].get("error") is not None]
        if not errors:
            return [by_id[rid].get("result") for rid in ids]

        retryable = all(isinstance(err, dict) and int(err.get("code", 0)) == 429 for _, err in errors)
        if not retryable or attempt >= max_item_retries:
            rid, err = errors[0]
            raise RuntimeError(f"BATCH_RPC_ERROR id={rid} error={err}")

        print(f"item-level 429 retry label={label} attempt={attempt+1}/{max_item_retries} affected={len(errors)} sleep={backoff:.1f}s")
        time.sleep(backoff)
        backoff = min(backoff * 2.0, backoff_cap)

    raise RuntimeError(f"BATCH_ITEM_RETRY_EXHAUSTED {label}")


v1.Rpc.batch = resilient_batch


if __name__ == "__main__":
    try:
        raise SystemExit(v1.main())
    except Exception as exc:
        print(f"FAIL-CLOSED V0.2: {type(exc).__name__}: {exc}")
        raise
