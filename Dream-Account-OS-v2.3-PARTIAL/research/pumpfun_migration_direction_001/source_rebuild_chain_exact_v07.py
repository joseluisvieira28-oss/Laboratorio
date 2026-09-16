#!/usr/bin/env python3
"""PMD-001 chain-exact source rebuild V0.7.

Reuses the frozen V0.6 transport/storage implementation but replaces migration
instruction parsing with the V0.7 authority that recognizes both Pump `migrate`
and `migrate_v2`. No economic outcome is read.
"""
from __future__ import annotations

import source_rebuild_chain_exact_v06 as base
from chain_boundary_semantics_v07 import (
    MIGRATE_V1_DISC,
    MIGRATE_V2_DISC,
    exact_migrate_outer_v07,
    is_actual_pool_creation_migration_v07,
)

# Freeze the parser semantics used by all V0.6 collection functions at runtime.
base.exact_migrate_outer = exact_migrate_outer_v07
base.is_actual_pool_creation_migration = is_actual_pool_creation_migration_v07

_original_collect_one = base.collect_one


def collect_one_v07(*args, **kwargs):
    rec = _original_collect_one(*args, **kwargs)
    rec = dict(rec)
    rec["stage"] = "CHAIN_EXACT_SOURCE_REBUILD_V07"
    rec["boundary_parser_version"] = "V07_MIGRATE_AND_MIGRATE_V2"
    rec["supported_migration_discriminators"] = [
        list(MIGRATE_V1_DISC),
        list(MIGRATE_V2_DISC),
    ]
    return rec


base.collect_one = collect_one_v07


if __name__ == "__main__":
    raise SystemExit(base.main())
