# DUAL-LST-RV-001 — SOURCE GATE HARDENING ADDENDUM V0.1A

Frozen: 2026-09-27
Parent: SOURCE_DATA_GATE_FREEZE_V0.1
Stage: SOURCE-ONLY / OUTCOME-BLIND
Scope: provenance / transport hardening only.

## Clarification before authoritative source result

The authoritative direct-market source path must pass at ALL FOUR frozen sentinels:

- block 20,000,000
- block 22,000,000
- block 24,000,000
- finalized block selected once at run start

For protocol anchors:
- rETH getExchangeRate must succeed at 4/4;
- wstETH protocol conversion must succeed at 4/4.

For the selected direct rETH/wstETH Uniswap V3 pool:
- token0/token1 must prove exact pair identity at 4/4;
- slot0 must succeed at 4/4;
- liquidity must be >0 at 4/4.

This clarification is frozen before any authoritative V0.1A source result is observed.

A pool that did not yet exist or had zero liquidity at one of the four sentinels is NOT suitable for this exact historical direct-market design.

No synthetic rETH/ETH divided by wstETH/ETH rescue is permitted.

## Transport hardening

Header authority:
https://ethereum-rpc.publicnode.com

Archive historical-state authority:
https://rpc-eth.blockmachine.io

Multicall3:
0xcA11bde05977b3631167028862bE2a173976CA11

For each sentinel:
1. resolve exact canonical block hash/timestamp from header authority;
2. execute one aggregate3 historical state call on archive authority;
3. pin the call with EIP-1898:
   {"blockHash": H, "requireCanonical": true};
4. no number-only or latest fallback.

The aggregate includes:
- rETH getExchangeRate;
- wstETH stEthPerToken;
- wstETH getStETHByWstETH(1e18) as predeclared fallback;
- token0/token1/slot0/liquidity for every discovered direct pool.

The wstETH anchor is valid when either frozen protocol method succeeds and returns >0.
If both succeed, stEthPerToken is primary and exact agreement is recorded descriptively.

## Retry

Each blockHash-pinned aggregate call may receive deterministic technical retries/backoff.
Retries may not change:
- block;
- pool;
- fee tier;
- contract;
- method set;
- source authority;
- scientific criterion.

## SOURCE_PASS V0.1A

Requires ALL:
- 4/4 rETH anchor valid;
- 4/4 wstETH anchor valid;
- >=1 exact direct pool valid with positive liquidity at 4/4;
- canonical block hash retained at 4/4;
- zero unresolved archive/source errors on the selected path;
- all outcome/PnL flags false.

SOURCE_PASS earns zero promotion credit.
