# PMD-001 — INTRABLOCK BOUNDARY TECHNICAL CORRECTION V0.5.1

Date: 2026-09-16
Status: PRE-OUTCOME / TECHNICAL CORRECTION ONLY

The first V0.5 workflow invocation terminated before any Solana RPC boundary test because `build_crossdate_probe20_manifest_v01.py` intentionally projects only `mint` and `t0` (plus probe metadata) and omits `pool_address`.

`INTRABLOCK_MIGRATION_BOUNDARY_AUTHORITY_V05.md` requires the already-frozen canonical PumpSwap pool identity to validate the exact Pump `migrate` instruction. The authoritative 1,012-row source manifest already contains that pool identity.

V0.5.1 therefore performs a deterministic metadata join:

`crossdate_probe_row.mint -> frozen_1012_manifest.mint -> pool_address`

No candidate is added, removed, replaced or reordered. The exact four frozen probe indices/mints remain unchanged. The 1,012-row manifest SHA remains required and no post-migration price value or economic outcome is read.

The failed first invocation is classified `TECHNICAL_NO_RECEIPT` and has no scientific verdict.
