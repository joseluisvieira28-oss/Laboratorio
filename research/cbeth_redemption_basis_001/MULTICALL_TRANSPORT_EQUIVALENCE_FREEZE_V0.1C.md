# CBETH-REDEMPTION-BASIS-001 — MULTICALL TRANSPORT EQUIVALENCE FREEZE V0.1C

Frozen: 2026-09-27
Timing: BEFORE source-gate execution and before all dense predictor data.
Scope: RPC TRANSPORT ONLY.

## Motivation

The frozen dense census needs, per daily observation block:
1. cbETH exchangeRate();
2. selected direct-pool slot0();
3. selected direct-pool liquidity().

Repeated separate archive calls can trigger public archive transport quotas.
This addendum allows Multicall3 compression only after exact byte-equivalence is proven.

## Multicall authority

Canonical Ethereum Multicall3:
0xcA11bde05977b3631167028862bE2a173976CA11

## Preconditions

Equivalence test runs only after SOURCE_PASS and after the direct pool has been selected using the already-frozen source-only rule.

## Fixed equivalence sentinels

Use exactly:
16,000,000
20,000,000
24,000,000

At each exact canonical blockHash compare:

DIRECT archive eth_call:
- cbETH exchangeRate();
- selected pool slot0();
- selected pool liquidity();

versus ONE Multicall3 aggregate3 containing the exact same three calls.

## PASS

MULTICALL_TRANSPORT_EQUIVALENCE_PASS requires:
- 3/3 sentinel block hashes resolved;
- all 3 direct calls succeed at all 3 blocks;
- all 3 Multicall subcalls succeed at all 3 blocks;
- direct return bytes == Multicall return bytes for every call;
- 9/9 exact byte comparisons PASS;
- EIP-1898 blockHash + requireCanonical used on both direct and Multicall archive calls;
- no latest fallback.

Any mismatch blocks Multicall transport.

## Census effect

Only after PASS may the dense census replace three separate archive state calls with one Multicall3 archive call at the same exact canonical blockHash.

Header resolution, daily clock, pool, predictor formula, calendar, q10/q90, sample gates and all outcomes remain unchanged.

No scientific or promotion credit is earned by transport equivalence.
