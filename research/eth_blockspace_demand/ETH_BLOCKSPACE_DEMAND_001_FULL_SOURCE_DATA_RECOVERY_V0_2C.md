# ETH-BLOCKSPACE-DEMAND-001 — FULL SOURCE/DATA RECOVERY V0.2C

Date: 2026-09-19
Status: **FROZEN PRE-RUN / SOURCE-DATA ONLY / OUTCOME-BLIND**

## Purpose

Complete the exact V0.2 frozen source grid without re-fetching rows that were already acquired successfully.

No market outcome, price, return, PnL, direction, threshold, horizon or protected-period data is authorized.

## Immutable parent source run

Parent non-canonical partial run: **35445718239**
Head SHA: **e03bd8ddf5bfa8a5a6e88b671ed0f30a26878da0**

Exact shard artifacts reused:
- shard 0 — artifact 10585198699 — sha256:9b1d8610e9ef3591fe99e7fbe1731db3d4e5468bf87b6a868ca2049bd4465a57
- shard 1 — artifact 10584384534 — sha256:97a83c29ed264e3b8e72e6e34b8b59d13b2b5005e632fb99c5fb0acc880c1150
- shard 2 — artifact 10584558868 — sha256:ab1df8fb0533ade05a1a3fdf929744c78bd41ee5ff235423f0610392a6c55c14
- shard 3 — artifact 10585359035 — sha256:8634ace59c44c7955d89f5645735b41d0fb6f19b6db51a583fc0b382871ed01f
- shard 4 — artifact 10585078581 — sha256:cbb8bc8bccef4cf266d65d8fbbbcd86e9bc27e22c28b1de062938c7687b5b16d
- shard 5 — artifact 10585109274 — sha256:653beab9deb78806fc7b266f0d3a247d6fe746045e898f605c16f196b6b557ca
- shard 6 — artifact 10584254463 — sha256:362ac939e26eb8b7f8df8cd50b3532554adc27ae1a46e2203b027382d1e169a2
- shard 7 — artifact 10585119402 — sha256:9703ccff65ef6519bc7f98e351710a1aec19cdd79e263456725c394e2bba172f

## Scientific/source identity unchanged

Exactly the V0.2 grid:
- blocks range(13,000,000, 21,500,000+1, 1,800)
- 4,723 targets
- 237 cross-provider audit indices where global_index mod 20 == 0
- DRPC + Flashbots
- same persisted header fields
- same per-block mechanical metrics
- same daily aggregation
- same >=99.5% coverage and >=95% daily-retention gates

## Recovery set

The recovery process may query the network only for:

1. target indices absent from the union of the eight parent shard CSVs;
2. deterministic audit indices whose parent row exists but audit_pass is not TRUE.

It may not re-select targets based on economic values.

## Schema correction inherited from V0.2A

Valid empty blocks are accepted:
- gasLimit > 0
- gasUsed >= 0
- gasUsed <= gasLimit
- baseFeePerGas > 0

gasUsed==0 => utilization 0 and sampled block base-fee burn 0.

## Recovery provenance

Every recovery target is requested from both already-qualified providers when possible.
Exact block hash and timestamp agreement is required for all deterministic audit targets.
Non-audit missing rows require at least one qualified provider, with provider/fallback recorded.

HTTP 429/5xx receives bounded deterministic retry/backoff.

## Final PASS

Final canonical union must satisfy all original V0.2 gates:
- >=99.5% target coverage
- 237/237 audits present and PASS
- zero protected-period rows
- no duplicate indices or blocks
- daily retention >=95%
- prices/returns/PnL closed

## Governance

This recovery cannot alter the hypothesis because no predictive hypothesis exists yet.
2025/2026, market prices, returns, PnL, live trading, orders, wallets, exchange mutation, alerts/webhooks, Render and main remain closed.
