#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import discovery_v01 as v

TRANSIENT_ITEM_CODES = {429, -32005, -32016}


def _is_transient_item_error(err: Any) -> bool:
    if not isinstance(err, dict):
        return False
    code = err.get("code")
    msg = str(err.get("message", "")).lower()
    if code in TRANSIENT_ITEM_CODES:
        return True
    return any(x in msg for x in (
        "rate limit",
        "rate-limit",
        "too many requests",
        "compute units",
        "throughput",
        "capacity exceeded",
        "request limit",
    ))


def rpc_batch_v011(endpoint: str, requests_: list[tuple[str, list[Any]]], stats):
    payload = [
        {"jsonrpc": "2.0", "id": i, "method": method, "params": params}
        for i, (method, params) in enumerate(requests_)
    ]
    last = None
    for attempt in range(8):
        out = v.rpc_json(endpoint, payload, stats)
        if not isinstance(out, list):
            raise RuntimeError("batch RPC non-list")
        byid = {x.get("id"): x for x in out if isinstance(x, dict)}
        vals = []
        transient = False
        for i in range(len(payload)):
            x = byid.get(i)
            if not x:
                raise RuntimeError(f"batch RPC item {i} missing")
            err = x.get("error")
            if err is not None:
                if _is_transient_item_error(err):
                    transient = True
                    last = err
                    break
                raise RuntimeError(f"batch RPC item {i} failed: {err}")
            vals.append(x.get("result"))
        if not transient:
            return vals
        stats["rpc_item_level_transient"] += 1
        if attempt >= 7:
            break
        stats["rpc_item_level_retries"] += 1
        time.sleep(min(30.0, 1.5 * (2 ** attempt)))
    raise RuntimeError(f"batch RPC transient retry budget exhausted: {last}")


def transport_self_test() -> None:
    original = v.rpc_json
    calls = {"n": 0}
    try:
        def fake_rpc_json(endpoint, payload, stats, retries=4):
            calls["n"] += 1
            if calls["n"] == 1:
                return [
                    {"jsonrpc": "2.0", "id": 0, "error": {"code": 429, "message": "compute units per second capacity"}}
                ]
            return [{"jsonrpc": "2.0", "id": 0, "result": "0x01"}]
        v.rpc_json = fake_rpc_json
        stats = v.Counter()
        vals = rpc_batch_v011("synthetic", [("eth_test", [])], stats)
        assert vals == ["0x01"]
        assert stats["rpc_item_level_transient"] == 1
        assert stats["rpc_item_level_retries"] == 1
        assert _is_transient_item_error({"code": 429, "message": "x"})
        assert not _is_transient_item_error({"code": -32602, "message": "invalid params"})
        print("STETH002_DISCOVERY_TRANSPORT_V011_SELF_TEST_PASS")
    finally:
        v.rpc_json = original


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        v.self_test()
        transport_self_test()
        return 0

    v.rpc_batch = rpc_batch_v011
    return v.run_discovery()


if __name__ == "__main__":
    sys.exit(main())
