# RETH-NAV-DISLOCATION-001 — ARCHIVE SOURCE REDUNDANCY PROBE V0.1C

Frozen: 2026-09-26
Scope: transport redundancy only.

Primary passing transport remains:
https://rpc-eth.blockmachine.io

Goal:
Identify an independent public/keyless backup capable of satisfying the exact already-frozen SOURCE_GATE_V0.1.

No source, block, pool, ABI, fee-tier, or gate changes are permitted.

Backup candidates:
1. https://public.1rpc.io/eth
2. https://eth.llamarpc.com
3. https://rpc.builder0x69.io
4. https://rpc.flashbots.net

Each candidate runs the same source probe:
- rETH getExchangeRate at 18M/20M/22M/24M + finalized;
- Uniswap V3 rETH/WETH fee tiers;
- historical block-pinned slot0/liquidity;
- no latest fallback.

A candidate is BACKUP_SOURCE_PASS only if the existing SOURCE_PASS criteria are met unchanged.

No account creation, API key, paid service, market return, PnL or hypothesis result is involved.
