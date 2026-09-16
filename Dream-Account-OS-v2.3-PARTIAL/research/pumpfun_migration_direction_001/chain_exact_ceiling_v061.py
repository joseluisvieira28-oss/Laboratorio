#!/usr/bin/env python3
"""PMD-001 chain-exact ceiling V0.6.1 transport optimization.

Semantics are identical to chain_exact_ceiling_v06.py. This wrapper memoizes
getBlock results inside one process so same-slot ordering checks reuse the
already retrieved finalized boundary block instead of re-requesting it once per
signature. No population, threshold, boundary rule, window or outcome rule is
changed.
"""
from __future__ import annotations

import chain_exact_ceiling_v06 as base

_original = base.get_blocks_batched
_cache = {}


def cached_get_blocks_batched(rpc, slots, batch_size):
    missing=[]; out={}
    for slot in slots:
        key=(id(rpc), int(slot))
        if key in _cache:
            out[int(slot)] = _cache[key]
        else:
            missing.append(int(slot))
    if missing:
        fresh=_original(rpc, missing, batch_size)
        for slot,rec in fresh.items():
            _cache[(id(rpc),int(slot))]=rec
            out[int(slot)]=rec
    return out


base.get_blocks_batched = cached_get_blocks_batched

if __name__ == '__main__':
    raise SystemExit(base.main())
