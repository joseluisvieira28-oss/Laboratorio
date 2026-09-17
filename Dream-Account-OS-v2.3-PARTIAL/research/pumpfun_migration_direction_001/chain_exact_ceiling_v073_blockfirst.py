#!/usr/bin/env python3
"""PMD-001 V0.7.3 block-first transport remediation.

SOURCE-ONLY / OUTCOME-BLIND.
Scientific semantics are unchanged from V0.7: same frozen 1,012-row manifest,
same migrate+migrate_v2 boundary parser, same 300s feature window and same
>=1,000 ceiling threshold. This amendment changes only RPC transport:
boundary transaction bodies are recovered from finalized getBlock responses
for the already-discovered signature slots instead of relying on archival
getTransaction availability from the public RPC.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import chain_exact_ceiling_v07 as v07

engine = v07.engine
_OriginalRpc = engine.Rpc


class BlockFirstRpc(_OriginalRpc):
    """RPC shim that resolves requested transaction bodies from finalized blocks."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._signature_slots: dict[str, int] = {}

    def get_signatures(self, address: str, before: str | None = None):
        rows = super().get_signatures(address, before=before)
        for rec in rows or []:
            sig = rec.get("signature") if isinstance(rec, dict) else None
            slot = rec.get("slot") if isinstance(rec, dict) else None
            if sig and slot is not None:
                self._signature_slots[str(sig)] = int(slot)
        return rows

    def get_transactions(self, signatures: list[str]) -> dict[str, Any]:
        # Boundary search already discovered each signature and slot via
        # getSignaturesForAddress. Fetch the finalized blocks that contain
        # those signatures and recover exact transaction bodies.
        requested = [str(s) for s in signatures]
        by_slot: dict[int, set[str]] = {}
        for sig in requested:
            slot = self._signature_slots.get(sig)
            if slot is not None:
                by_slot.setdefault(int(slot), set()).add(sig)

        out: dict[str, Any] = {sig: {"_missing_batch_response": True} for sig in requested}
        if by_slot:
            records = engine.get_blocks_batched(self, sorted(by_slot), 4) or {}
            for slot, wanted in by_slot.items():
                rec = records.get(int(slot)) or {}
                block = rec.get("block") if isinstance(rec, dict) else None
                if not isinstance(block, dict) or block.get("_rpc_error"):
                    continue
                for item in block.get("transactions") or []:
                    if not isinstance(item, dict):
                        continue
                    sig = engine.tx_signature(item)
                    if sig in wanted:
                        out[str(sig)] = item
        return out


engine.Rpc = BlockFirstRpc

_original_collect = engine.collect_one


def collect_one_v073(*args, **kwargs):
    rec = dict(_original_collect(*args, **kwargs))
    rec["stage"] = "CHAIN_EXACT_CEILING_V073_BLOCKFIRST_SHARD"
    rec["transport_version"] = "V073_FINALIZED_BLOCK_FIRST"
    rec["boundary_parser_version"] = "V07_MIGRATE_AND_MIGRATE_V2"
    rec["economic_outcomes_opened"] = False
    rec["scientific_verdict_authority"] = False
    return rec


engine.collect_one = collect_one_v073


def cli_value(flag: str) -> str | None:
    try:
        i = sys.argv.index(flag)
        return sys.argv[i + 1]
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    rc = engine.main()
    out_dir = cli_value("--out-dir")
    if out_dir:
        p = Path(out_dir) / "chain_exact_ceiling_shard_receipt.json"
        if p.exists():
            r = json.loads(p.read_text(encoding="utf-8"))
            r["stage"] = "CHAIN_EXACT_CEILING_V073_BLOCKFIRST_SHARD"
            r["transport_version"] = "V073_FINALIZED_BLOCK_FIRST"
            r["boundary_parser_version"] = "V07_MIGRATE_AND_MIGRATE_V2"
            r["economic_outcomes_opened"] = False
            r["scientific_verdict_authority"] = False
            p.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(rc)
