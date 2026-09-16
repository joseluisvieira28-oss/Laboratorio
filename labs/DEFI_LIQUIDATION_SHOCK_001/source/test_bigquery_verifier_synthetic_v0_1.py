#!/usr/bin/env python3
"""Network-free tests for BigQuery -> raw RPC verifier V0.1."""

from __future__ import annotations

import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"FAILED_TO_LOAD {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


collector = load("collect_protocol_history_v0_1", "collect_protocol_history_v0_1.py")
verifier = load("verify_bigquery_candidates_v0_1", "verify_bigquery_candidates_v0_1.py")


def b58encode(blob: bytes) -> str:
    n = int.from_bytes(blob, "big")
    out = ""
    while n:
        n, rem = divmod(n, 58)
        out = collector.BASE58_ALPHABET[rem] + out
    leading = len(blob) - len(blob.lstrip(b"\x00"))
    return "1" * leading + out


def test_timestamp_parse() -> None:
    a = verifier.timestamp_unix("2024-01-01 00:00:00 UTC")
    b = verifier.timestamp_unix("2024-01-01T00:00:00Z")
    assert a == b == 1704067200


def test_outer_reconciliation() -> None:
    program = "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
    tx = {
        "transaction": {"message": {
            "accountKeys": ["payer", program, "acct"],
            "instructions": [{"programIdIndex": 1, "accounts": [2], "data": b58encode(b"\x11" + b"\0" * 8)}],
        }},
        "meta": {"err": None, "loadedAddresses": {"writable": [], "readonly": []}, "innerInstructions": []},
    }
    row = {"program_id": program, "parent_index": None, "instruction_index": 0, "tx_signature": "sig"}
    ix = verifier.find_instruction(tx, row)
    assert ix["location"] == "outer"
    assert ix["first_byte_hex"] == "11"


def test_inner_reconciliation() -> None:
    program = "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
    payload = bytes.fromhex("b1479acce2854a37") + b"\0" * 8
    tx = {
        "transaction": {"message": {
            "accountKeys": ["payer", "outer", "acct"],
            "instructions": [{"programIdIndex": 1, "accounts": [], "data": "1"}],
        }},
        "meta": {
            "err": None,
            "loadedAddresses": {"writable": [], "readonly": [program]},
            "innerInstructions": [{"index": 0, "instructions": [
                {"programIdIndex": 3, "accounts": [2], "data": b58encode(payload)}
            ]}],
        },
    }
    row = {"program_id": program, "parent_index": 0, "instruction_index": 0, "tx_signature": "sig"}
    ix = verifier.find_instruction(tx, row)
    assert ix["location"] == "inner"
    assert ix["prefix_8_hex"] == "b1479acce2854a37"


def main() -> int:
    tests = [test_timestamp_parse, test_outer_reconciliation, test_inner_reconciliation]
    for fn in tests:
        fn()
    print(f"PASS {len(tests)}/{len(tests)} synthetic BigQuery-verifier tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
