# RETH-NAV-DISLOCATION-001 — MULTICALL TRANSPORT EQUIVALENCE FREEZE V0.1B

Frozen: 2026-09-26
Parent: PREDICTOR_CENSUS_TECHNICAL_RETRY_V0.1A
Scope: RPC transport compression only.

## Trigger

V0.1A low-concurrency retry still showed deterministic transport exhaustion:
- shard 0 invalid indices 13,20,27,34,41,48,55,62,69;
- shard 1 invalid indices 82,89,96,103,110,117,124,131,138.

Spacing is exactly 7 census points between failures, consistent with a recurring RPC quota window rather than historical-block invalidity.

## Proposed transport

Use canonical Multicall3:
0xcA11bde05977b3631167028862bE2a173976CA11

At each exact block N, aggregate the same four read-only calls:
1. rETH getExchangeRate()
2. rETH getTotalCollateral()
3. fee-100 rETH/WETH slot0()
4. fee-100 rETH/WETH liquidity()

Block metadata remains read separately at exact N.

No call semantics, block, contract, pool, predictor formula or validity rule changes.

## Mandatory equivalence test BEFORE census

At fixed blocks:
20,000,000
22,000,000
24,000,000

query both:
- the four direct calls; and
- the same calls through Multicall3 aggregate3 at the identical block.

MULTICALL_TRANSPORT_EQUIVALENCE_PASS requires:
- every direct call succeeds;
- every Multicall subcall succeeds;
- return bytes are exactly identical for all four calls at all three blocks;
- exact block hashes are retained;
- no latest fallback.

If equivalence fails:
MULTICALL_TRANSPORT_EQUIVALENCE_FAIL and this transport is forbidden.

## Census use

Only after equivalence PASS may a clean census rerun use Multicall3.

The census still requires:
- exact original 556 blocks;
- 100% valid coverage;
- exact fee-100 pool;
- exact predictor formula;
- no imputation or block substitution.

This remediation changes HTTP/RPC transport only and earns zero scientific/promotion credit.
