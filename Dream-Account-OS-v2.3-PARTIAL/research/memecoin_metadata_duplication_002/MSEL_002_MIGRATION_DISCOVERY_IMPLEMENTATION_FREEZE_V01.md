# MSEL-002 — MIGRATION DISCOVERY IMPLEMENTATION FREEZE V0.1

Date: 2026-09-20
Branch: `memecoin-metadata-duplication-v0.1`
Status: **IMPLEMENTATION FROZEN BEFORE OUTCOME ACQUISITION**

Upstream authorities:
- `MSEL_002_ECONOMIC_OUTCOME_FREEZE_V01.md`
- cohort run `35500294196` = SUCCESS
- cohort artifact `10601836899`
- artifact digest `sha256:1508c562c61a7644172ec801d23096f93e7b5206cb612ff1f70453a421cb1397`
- cohort payload SHA-256 `5501ee9c35d6a5966b18246a2a7b35f428900d48b7fa3deaa5e9bcb4dc758a0a`
- 51 exposed + 510 controls = 561 total.

## Frozen source route

Provider: SQD Portal `solana-mainnet`, public read-only historical source.

Use:
- timestamp resolver: `GET /datasets/solana-mainnet/timestamps/{timestamp}/block`
- historical instruction stream via `@subsquid/portal-client`.
- only Pump program `migrate` instructions are requested.

Pump program:
`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

Pump migrate discriminator:
`0x9beae792ec9ea21e`

PumpSwap program:
`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

Pinned official IDL account order for Pump `migrate`:
- account[2] = mint
- account[8] = PumpSwap/Pump AMM program
- account[9] = canonical pool account

The collector must require:
- exact program ID;
- exact migrate discriminator;
- at least 10 accounts;
- account[8] == pinned PumpSwap program;
- instruction `isCommitted == true`;
- instruction `error == null`.

The official SQD field `isCommitted` is the frozen success-state authority for the instruction's atomic transaction. Transaction signatures/err may be preserved when present, but missing optional transaction linkage may not convert an uncommitted instruction into success.

## Frozen range

Start slot = minimum launch slot among all 561 frozen cohort candidates.

End timestamp = maximum frozen cohort candidate block_time + 259,200 seconds.

End slot = SQD timestamp resolver's first block at or after the frozen end timestamp.

No period extension is permitted.

## Frozen source completeness

The exact `@subsquid/portal-client` range request must complete successfully from frozen start slot through resolved end slot.

Any client/network/schema/range failure => `SOURCE_DATA_FAILURE`.

No candidate may be dropped.

## Frozen candidate adjudication

For each candidate mint, consider committed exact migrate instructions for that mint.

Earliest qualifying migrate timestamp after the candidate launch is used.

- <= launch + 86,400 s => `MIGRATED_24H`
- > 86,400 and <= 259,200 s => `MIGRATED_72H_ONLY`
- no qualifying event after complete range scan => `NO_MIGRATION_72H_SOURCE_COMPLETE`

Events at or before candidate block_time do not count.

Every candidate must resolve to exactly one state.

## Frozen statistics and verdict

Inherited unchanged from `MSEL_002_ECONOMIC_OUTCOME_FREEZE_V01.md`.

Matched-set effects:
- D24 = mean(exposed MIGRATE_24H - mean 10 matched controls)
- D72 = same with MIGRATE_72H

Bootstrap:
- 100,000 matched-set resamples with replacement
- seed `MSEL-002-MIGRATION-BOOTSTRAP-V1|2026-09-20`
- percentile 95% CI.

`DISCOVERY_SIGNAL` only if:
1. all 561 outcomes source-resolved;
2. D24 <= -0.10;
3. D24 95% bootstrap upper bound < 0;
4. D72 < 0.

Otherwise `DISCOVERY_NO_EDGE_FOR_FROZEN_MIGRATION_MECHANISM`, unless source integrity fails.

No threshold, cohort, horizon, source, matching, decoder, bootstrap or direction rescue after outcomes.

## Safety

This V0.1 may open only migration completion outcomes.

Forbidden:
- prices;
- returns;
- PnL;
- market-cap/winner/catastrophe labels;
- liquidity-profit analysis;
- live trading;
- orders;
- wallets;
- exchange/chain mutation;
- alerts/webhooks;
- merge to main;
- automatic promotion.
