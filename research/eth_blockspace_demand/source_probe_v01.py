#!/usr/bin/env python3
"""Source-only historical Ethereum block-header probe for ETH-BLOCKSPACE-DEMAND-001."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import requests

LAB_ID = "ETH-BLOCKSPACE-DEMAND-001"
BLOCKS = [13_000_000, 15_000_000, 18_000_000, 21_000_000]
END_TS_EXCLUSIVE = 1_735_689_600  # 2025-01-01T00:00:00Z
ENDPOINTS = [
    "https://ethereum-rpc.publicnode.com",
    "https://eth.drpc.org",
    "https://1rpc.io/eth",
]
REQUIRED_FIELDS = [
    "number", "hash", "parentHash", "timestamp", "gasLimit", "gasUsed", "baseFeePerGas"
]


def rpc(endpoint: str, method: str, params: list[Any]) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(
        endpoint,
        json=payload,
        headers={"Content-Type": "application/json", "User-Agent": f"{LAB_ID}/source-probe-v0.1"},
        timeout=(10, 30),
    )
    r.raise_for_status()
    obj = r.json()
    if obj.get("error") is not None:
        raise RuntimeError(f"rpc error {obj['error']}")
    return obj.get("result")


def qint(x: Any) -> int:
    if not isinstance(x, str) or not x.startswith("0x"):
        raise ValueError("expected JSON-RPC quantity")
    return int(x, 16)


def main() -> int:
    outdir = Path("eth_blockspace_source_probe")
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / "ETH_BLOCKSPACE_DEMAND_001_SOURCE_PROBE_V0_1.json"

    receipt: dict[str, Any] = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_ONLY_OUTCOME_BLIND",
        "classification": None,
        "failure": None,
        "frozen_blocks": BLOCKS,
        "provider_count": len(ENDPOINTS),
        "providers": {},
        "blocks": {},
        "safety": {
            "transaction_bodies_requested": False,
            "market_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "orders": False,
            "wallets": False,
            "exchange_mutation": False,
            "merge_main": False,
        },
    }

    technical = False
    provenance = False
    schema = False
    accepted_blocks = 0

    try:
        provider_chain = {}
        block_results: dict[int, dict[str, Any]] = {b: {} for b in BLOCKS}

        for ep in ENDPOINTS:
            pstat = {"chain_id_ok": False, "errors": []}
            try:
                cid = rpc(ep, "eth_chainId", [])
                pstat["chain_id_ok"] = cid == "0x1"
                if cid != "0x1":
                    provenance = True
                    pstat["errors"].append("CHAIN_ID_NOT_MAINNET")
            except Exception as exc:
                technical = True
                pstat["errors"].append(f"CHAIN_ID:{type(exc).__name__}")
            provider_chain[ep] = pstat

            for b in BLOCKS:
                try:
                    obj = rpc(ep, "eth_getBlockByNumber", [hex(b), False])
                    if not isinstance(obj, dict):
                        raise RuntimeError("null_or_nonobject_block")
                    missing = [f for f in REQUIRED_FIELDS if obj.get(f) is None]
                    if missing:
                        schema = True
                        raise RuntimeError("missing_fields:" + ",".join(missing))

                    number = qint(obj["number"])
                    timestamp = qint(obj["timestamp"])
                    gas_limit = qint(obj["gasLimit"])
                    gas_used = qint(obj["gasUsed"])
                    base_fee = qint(obj["baseFeePerGas"])
                    if number != b:
                        provenance = True
                        raise RuntimeError("block_number_identity_mismatch")
                    if timestamp >= END_TS_EXCLUSIVE:
                        provenance = True
                        receipt["safety"]["accessed_2025_or_2026"] = True
                        raise RuntimeError("protected_period_timestamp_breach")
                    if gas_limit <= 0 or gas_used <= 0 or gas_used > gas_limit or base_fee <= 0:
                        schema = True
                        raise RuntimeError("invalid_header_economic_field_sanity")

                    # Persist identity/provenance only; do not serialize economic field values.
                    block_results[b][ep] = {
                        "block_hash": str(obj["hash"]).lower(),
                        "parent_hash": str(obj["parentHash"]).lower(),
                        "timestamp": timestamp,
                        "required_fields_present": True,
                        "economic_fields_sanity_pass": True,
                    }
                except Exception as exc:
                    provider_chain[ep]["errors"].append(f"BLOCK_{b}:{type(exc).__name__}:{str(exc)[:120]}")

        receipt["providers"] = provider_chain

        for b in BLOCKS:
            vals = block_results[b]
            hashes = sorted({x["block_hash"] for x in vals.values()})
            timestamps = sorted({x["timestamp"] for x in vals.values()})
            quorum = len(vals)
            status = "PASS"
            if quorum < 2:
                technical = True
                status = "INSUFFICIENT_PROVIDER_QUORUM"
            elif len(hashes) != 1 or len(timestamps) != 1:
                provenance = True
                status = "PROVIDER_DISAGREEMENT"
            else:
                accepted_blocks += 1
            receipt["blocks"][str(b)] = {
                "provider_quorum": quorum,
                "identity_status": status,
                "canonical_block_hash": hashes[0] if len(hashes) == 1 else None,
                "canonical_timestamp": timestamps[0] if len(timestamps) == 1 else None,
                "required_fields": REQUIRED_FIELDS,
                "economic_values_persisted": False,
            }

        if receipt["safety"]["accessed_2025_or_2026"]:
            classification = "PROVENANCE_FAILURE"
        elif provenance:
            classification = "PROVENANCE_FAILURE"
        elif schema:
            classification = "SOURCE_SCHEMA_INSUFFICIENT"
        elif technical or accepted_blocks != len(BLOCKS):
            classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        else:
            classification = "SOURCE_SCHEMA_PASS"

        receipt["classification"] = classification
        canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        receipt["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()

    except Exception as exc:
        receipt["classification"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {str(exc)[:1000]}"

    dst.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "accepted_blocks": accepted_blocks,
        "frozen_blocks": len(BLOCKS),
        "economic_values_persisted": False,
        "market_prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
        "accessed_2025_or_2026": receipt["safety"]["accessed_2025_or_2026"],
    }, sort_keys=True))
    return 0 if receipt["classification"] == "SOURCE_SCHEMA_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
