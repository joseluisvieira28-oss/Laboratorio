# RETH-NAV-DISLOCATION-001 — PREDICTOR CENSUS TECHNICAL RETRY V0.1A

Frozen: 2026-09-26
Parent: PREDICTOR_ONLY_CENSUS_FREEZE_V0.1
Scope: TECHNICAL RETRY ONLY.

## Trigger

Initial census run #36264035882 preserved all 8 shard artifacts but failed the frozen 100% coverage gate.
Observed failures were transient transport exhaustion such as:
- exceeded maximum retry limit.

Example shard 0:
- expected 70;
- valid 57;
- invalid 13.

No market returns, direction, horizon or PnL were opened.

## Permitted remediation

The exact same 556 frozen points are rerun from scratch.

UNCHANGED:
- blocks;
- start/end boundaries;
- 7,200-block cadence;
- rETH contract;
- fee-100 pool;
- getExchangeRate;
- getTotalCollateral;
- slot0;
- liquidity;
- exact dislocation formula;
- liquidity > 0 validity rule;
- block-pinned calls;
- 100% coverage requirement;
- no imputation;
- no pool switching.

TECHNICAL CHANGES ONLY:
- replace per-point Promise.all RPC burst with sequential RPC calls;
- workflow shard max-parallel reduced from 4 to 2;
- attempts per point increased from 4 to 8;
- deterministic increasing backoff between failed attempts.

## Scientific interpretation

The V0.1 failed run is retained as technical evidence and contributes zero scientific result.

Only a complete fresh 556/556 rerun may classify PREDICTOR_SOURCE_CENSUS_PASS.

If the clean retry still cannot achieve 100% coverage, classify PREDICTOR_SOURCE_CENSUS_BLOCKED. No threshold or source rescue is authorized.
