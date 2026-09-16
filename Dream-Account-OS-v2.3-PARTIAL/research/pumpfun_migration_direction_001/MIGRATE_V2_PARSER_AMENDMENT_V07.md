# PMD-001 — MIGRATE V2 PARSER AMENDMENT V0.7

Status: PRE-OUTCOME / SOURCE-ONLY / FAIL-CLOSED
Date: 2026-09-16
Branch: `pumpfun-migration-direction-v0.1`

## Why this amendment exists

The frozen Chain-Exact Cross-Date V0.6 run reconciled all 20 mandatory date rows but resolved only 10 unique pool-creation migration boundaries.

The V0.6 parser recognized only the legacy Pump instruction discriminator for `migrate`:

`[155,234,231,146,236,158,162,30]`

Raw finalized block evidence from a mandatory V0.6 failure row showed that the actual canonical migration transaction was present and successful, but used Pump instruction `MigrateV2`, followed by the canonical PumpSwap `CreatePool` invocation. Therefore that row was a parser-coverage failure, not evidence that a migration did not occur.

The observed MigrateV2 discriminator is:

`[187,203,18,31,206,237,254,41]`

This equals the Anchor discriminator `sha256("global:migrate_v2")[:8]` and is independently consistent with public Pump parser references that decode `migrate_v2`.

No post-migration price value, return, PnL, direction label, feature/outcome correlation, Validation result or Protected Holdout result was opened in discovering this source-parser issue.

## Frozen V0.7 parser correction

V0.7 may recognize exactly two Pump migration instruction variants:

1. legacy `migrate` discriminator `[155,234,231,146,236,158,162,30]`;
2. `migrate_v2` discriminator `[187,203,18,31,206,237,254,41]`.

A transaction qualifies as the chain-exact migration boundary only if ALL of the following remain true:

- transaction succeeded (`meta.err == null`);
- the outer instruction program is the frozen Pump program `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`;
- the instruction discriminator is exactly one of the two frozen migration discriminators above;
- the instruction accounts contain the frozen mint;
- the instruction accounts contain the mint-specific bonding-curve PDA;
- the instruction accounts contain the frozen canonical PumpSwap pool address from the 1,012-row manifest;
- transaction logs contain PumpSwap `Instruction: CreatePool`;
- transaction logs contain invocation of the frozen PumpSwap AMM program `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`;
- transaction logs do NOT contain `Bonding curve already migrated`;
- exactly one qualifying pool-creation boundary exists inside the already-frozen boundary search horizon.

No heuristic nearest-time migration may be selected. Zero qualifying boundaries fails closed. More than one qualifying boundary fails closed.

## What does NOT change

This amendment changes only source parser coverage for the on-chain migration instruction version.

It does NOT change:

- the frozen 1,012-candidate population;
- the 20 mandatory cross-date mints or dates;
- the deterministic selection rule;
- the canonical pool identity;
- the Pump or PumpSwap program IDs;
- the 300-second predictive feature window;
- the source retrieval envelope;
- the ledger ordering rule `(blockTime, slot, transaction_index)`;
- the requirement that predictive evidence be strictly before the actual chain boundary;
- the 20/20 Cross-Date gate;
- the >=1,000 full-population sample gate;
- the 60/20/20 chronological split;
- the 3.00 percentage-point round-trip execution stress;
- any economic hypothesis, threshold or feature formula;
- any outcome rule.

## Mandatory V0.7 cross-date execution

The same 20 frozen rows must be rerun with V0.7 parser semantics.

PASS requires exactly:

- 20 artifacts;
- 20 unique frozen indices;
- 20 unique mints;
- 20 distinct dates;
- zero malformed artifacts;
- outcome wall intact;
- 20/20 unique chain boundaries;
- 20/20 `source_complete`;
- 20/20 `feature_source_eligible`.

Anything less than 20/20 does not authorize the 1,012-row ceiling.

## Governance

- research-only;
- source-only;
- outcome-blind;
- fail-closed;
- no threshold rescue;
- no candidate substitution;
- no economic outcomes before all source gates and subsequent feature/split freezes pass;
- no live trading;
- no exchange mutation;
- no main merge.
