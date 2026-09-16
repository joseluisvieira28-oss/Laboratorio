#!/usr/bin/env python3
"""PMD-001 chain-exact ceiling V0.7.

Reuses the frozen/memoized V0.6.1 ceiling transport and replaces only migration
instruction parsing with V0.7 `migrate` + `migrate_v2` semantics. Outcomes stay closed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import chain_exact_ceiling_v061 as opt
from chain_boundary_semantics_v07 import (
    MIGRATE_V1_DISC,
    MIGRATE_V2_DISC,
    is_actual_pool_creation_migration_v07,
)

engine = opt.base
engine.is_actual_pool_creation_migration = is_actual_pool_creation_migration_v07

_original_collect = engine.collect_one


def collect_one_v07(*args, **kwargs):
    rec = dict(_original_collect(*args, **kwargs))
    rec["stage"] = "CHAIN_EXACT_CEILING_V07_SHARD"
    rec["boundary_parser_version"] = "V07_MIGRATE_AND_MIGRATE_V2"
    rec["supported_migration_discriminators"] = [list(MIGRATE_V1_DISC), list(MIGRATE_V2_DISC)]
    return rec


engine.collect_one = collect_one_v07


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
            r["stage"] = "CHAIN_EXACT_CEILING_V07_SHARD"
            r["boundary_parser_version"] = "V07_MIGRATE_AND_MIGRATE_V2"
            r["supported_migration_discriminators"] = [list(MIGRATE_V1_DISC), list(MIGRATE_V2_DISC)]
            r["economic_outcomes_opened"] = False
            r["scientific_verdict_authority"] = False
            p.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(rc)
