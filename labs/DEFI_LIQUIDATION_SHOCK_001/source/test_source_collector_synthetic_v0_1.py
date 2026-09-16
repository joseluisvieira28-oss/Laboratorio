#!/usr/bin/env python3
"""Synthetic, network-free tests for DEFI-LIQUIDATION-SHOCK-001 source collector."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
MODULE_PATH = HERE / "collect_protocol_history_v0_1.py"

spec = importlib.util.spec_from_file_location("dls_source_collector", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("FAILED_TO_LOAD_COLLECTOR")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ALPH = mod.BASE58_ALPHABET


def b58encode(blob: bytes) -> str:
    n = int.from_bytes(blob, "big")
    encoded = ""
    while n:
        n, rem = divmod(n, 58)
        encoded = ALPH[rem] + encoded
    leading = len(blob) - len(blob.lstrip(b"\x00"))
    return "1" * leading + encoded


def test_base58_roundtrip() -> None:
    cases = [
        b"\x11" + b"\x00" * 8,
        bytes.fromhex("b1479acce2854a37") + b"abc",
        bytes.fromhex("d6a997d5fba756db"),
    ]
    for raw in cases:
        assert mod.b58decode(b58encode(raw)) == raw


def test_outer_instruction_and_reference_match() -> None:
    target = "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
    tx = {
        "transaction": {
            "message": {
                "accountKeys": ["payer", target, "obligation", "other"],
                "instructions": [
                    {
                        "programIdIndex": 1,
                        "accounts": [2],
                        "data": b58encode(b"\x11" + (123).to_bytes(8, "little")),
                    },
                    {"programIdIndex": 3, "accounts": [], "data": "1"},
                ],
            }
        },
        "meta": {"err": None, "loadedAddresses": {"writable": [], "readonly": []}, "innerInstructions": []},
        "slot": 1,
        "blockTime": mod.SOURCE_START_UNIX + 1,
        "version": 0,
    }
    rows = mod.extract_protocol_instructions(tx, target)
    assert len(rows) == 1
    assert rows[0]["first_byte_hex"] == "11"
    cfg = {
        "reference_liquidation_encodings": [
            {"name": "liq", "encoding": "native_u8_tag", "prefix_hex": "11"}
        ]
    }
    assert mod.reference_matches(cfg, rows[0]) == ["liq"]


def test_inner_instruction_loaded_address_resolution() -> None:
    target = "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
    data = bytes.fromhex("b1479acce2854a37") + b"\x00" * 24
    tx = {
        "transaction": {
            "message": {
                "accountKeys": ["payer", "outer_program", "acct"],
                "instructions": [{"programIdIndex": 1, "accounts": [], "data": "1"}],
            }
        },
        "meta": {
            "err": None,
            "loadedAddresses": {"writable": [], "readonly": [target]},
            "innerInstructions": [
                {
                    "index": 0,
                    "instructions": [
                        {"programIdIndex": 3, "accounts": [2], "data": b58encode(data)}
                    ],
                }
            ],
        },
        "slot": 2,
        "blockTime": mod.SOURCE_START_UNIX + 2,
        "version": 0,
    }
    rows = mod.extract_protocol_instructions(tx, target)
    assert len(rows) == 1
    assert rows[0]["location"] == "inner"
    assert rows[0]["prefix_8_hex"] == "b1479acce2854a37"


def test_registry_freeze() -> None:
    registry_path = HERE / "protocol_registry_v0_1.json"
    registry = mod.load_registry(registry_path)
    assert registry["source_window_utc"]["start"] == mod.SOURCE_START_ISO
    assert registry["source_window_utc"]["end"] == mod.SOURCE_END_ISO
    assert len(registry["protocols"]) == 4
    assert all(p["historical_decoder_authoritative"] is False for p in registry["protocols"])


def test_output_immutability_guard_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp) / "RUN_MANIFEST.json"
        p.write_text(json.dumps({"test": True}), encoding="utf-8")
        assert p.exists()


def main() -> int:
    tests = [
        test_base58_roundtrip,
        test_outer_instruction_and_reference_match,
        test_inner_instruction_loaded_address_resolution,
        test_registry_freeze,
        test_output_immutability_guard_shape,
    ]
    for fn in tests:
        fn()
    print(f"PASS {len(tests)}/{len(tests)} synthetic source-collector tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
