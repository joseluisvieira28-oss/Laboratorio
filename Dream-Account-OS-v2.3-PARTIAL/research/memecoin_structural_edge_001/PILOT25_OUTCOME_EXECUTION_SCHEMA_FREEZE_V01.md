# MSEL-001 — Pilot25 Outcome Schema Freeze V0.1

Status: PRE-OUTCOME / RESEARCH-ONLY / FROZEN
Date: 2026-09-15

Feature authority is already frozen by V11:
- matrix SHA-256: 226c64d9683702e81c5f2b2b871b4d8971e761914c999a0d2e6c257328005d72
- risk-order SHA-256: 5857267a7d0203fa0e8e70eeafc34017d225a84a7809c97accce8bbb76f7fb8e
- manifest SHA-256: ceec26d445a91c3a89721cd5ef3e7b774bbff5a620659c91486202e99134bae8

Decision time is launch time +300s. Future horizons are +15m, +1h, +6h and +24h from that decision time.

Historical schema authority is pump-fun/pump-public-docs commit e2b66e4fce2fc130955912315167dc41e56956ad. Pump program: 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P. PumpSwap program: pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA. Historical PumpSwap IDL git blob observed: 7a1cf37270f6015f5af53b9ce58d8a6890254020.

Primary entry reference: last valid observed BUY for the target token in the final 60 seconds at or before T+5, with quote notional >=0.01 SOL, excluding already-identified dust/no-delivery and atomic-roundtrip components. If absent, ENTRY_REFERENCE_UNAVAILABLE.

Primary future path uses valid observed SELL executions strictly after T+5. A valid future SELL must be source-reconciled on Pump or a cryptographically linked PumpSwap pool, quote notional >=0.01 SOL, and not dust/atomic-roundtrip. No price interpolation is allowed.

Observed execution price is quote_raw/token_raw. Primary exit return is exit_price/entry_price - 1. Fees are not guessed from field names; a frozen secondary 3.00% round-trip haircut is used only as sensitivity.

Migration continuity is allowed only when the PumpSwap pool is proven from on-chain migration/create-pool evidence under the historical schema. Unproven migration linkage is SOURCE_BLOCKED_MIGRATION_LINK.

Primary +24h catastrophe is TRUE if a valid observed SELL reaches <=-80%, or if source coverage is complete but no economically non-trivial SELL (>=0.01 SOL) exists in the full +24h window; the latter is separately CATASTROPHIC_LIQUIDITY_ABSENCE. Incomplete source coverage is OUTCOME_SOURCE_UNRESOLVED, never silently safe.

Primary +100% winner is TRUE only if a valid observed SELL reaches >=+100% relative to the frozen entry reference. BUY-only spikes do not count.

After collection, Pilot25 may report frozen-slice incidence and winner retention under V11. It may not alter V11 ranks/slices, thresholds, notional floor, entry freshness or outcome definitions. Pilot25 cannot by itself claim SURVIVES_MVE because the full gate requires multiple temporal OOS blocks.

Governance: research-only, fail-closed, no live trading, no exchange mutation, no merge to main, no post-outcome tuning or rescue.
