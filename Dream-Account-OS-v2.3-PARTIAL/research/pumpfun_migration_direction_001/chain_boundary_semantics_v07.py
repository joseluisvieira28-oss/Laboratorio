#!/usr/bin/env python3
"""PMD-001 V0.7 migration-boundary parser semantics.

Outcome-blind. Adds Pump `migrate_v2` parser coverage while preserving the
same causal boundary definition: the unique successful Pump migration call
that actually invokes PumpSwap CreatePool for the frozen canonical pool.
"""
from __future__ import annotations

from typing import Any

from intrablock_boundary_probe_v05 import (
    PUMP_PROGRAM, PUMP_AMM, MIGRATE_DISC,
    account_keys, outer_instructions, resolve_program, resolve_ix_accounts, ix_data,
)

MIGRATE_V1_DISC = bytes(MIGRATE_DISC)
MIGRATE_V2_DISC = bytes([187, 203, 18, 31, 206, 237, 254, 41])
SUPPORTED_MIGRATION_DISCRIMINATORS = {
    MIGRATE_V1_DISC: "migrate",
    MIGRATE_V2_DISC: "migrate_v2",
}


def matching_migration_variants(item: dict[str, Any], mint: str, pda: str, pool: str) -> list[str]:
    """Return supported migration variants whose outer instruction matches all frozen accounts."""
    if (item.get("meta") or {}).get("err") is not None:
        return []
    keys = account_keys(item)
    out: list[str] = []
    for ix in outer_instructions(item):
        if resolve_program(ix, keys) != PUMP_PROGRAM:
            continue
        data = ix_data(ix)
        if len(data) < 8:
            continue
        variant = SUPPORTED_MIGRATION_DISCRIMINATORS.get(bytes(data[:8]))
        if variant is None:
            continue
        accounts = set(resolve_ix_accounts(ix, keys))
        if mint in accounts and pda in accounts and pool in accounts:
            out.append(variant)
    return out


def exact_migrate_outer_v07(item: dict[str, Any], mint: str, pda: str, pool: str) -> bool:
    return bool(matching_migration_variants(item, mint, pda, pool))


def migration_variant_v07(item: dict[str, Any], mint: str, pda: str, pool: str) -> str | None:
    variants = sorted(set(matching_migration_variants(item, mint, pda, pool)))
    return variants[0] if len(variants) == 1 else None


def is_actual_pool_creation_migration_v07(item: dict[str, Any], mint: str, pda: str, pool: str) -> bool:
    if not exact_migrate_outer_v07(item, mint, pda, pool):
        return False
    logs = (item.get("meta") or {}).get("logMessages") or []
    has_create_pool = any("Program log: Instruction: CreatePool" in str(x) for x in logs)
    has_pump_amm = any(f"Program {PUMP_AMM} invoke" in str(x) for x in logs)
    already_migrated = any("Bonding curve already migrated" in str(x) for x in logs)
    return bool(has_create_pool and has_pump_amm and not already_migrated)
