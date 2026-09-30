# DLS — MARGINFI SOL AUGUST 2024 SOURCE HASH-SHARDING FALLBACK V0.1

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-rebound-v01
Status: FROZEN OPERATIONAL FALLBACK / SOURCE-ONLY

Parent scientific authority:
MARGINFI_SOL_EXTREME_FLOW_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md

Reason:
The canonical monthly Jul-Sep source run 36767743962 has completed July and September successfully,
while August contains 7,677 canonical SOL-collateral liquidation rows and is transport-heavy.

No Jul-Sep market outcome has been opened.

This addendum changes transport only.

## Canonical August population

Field-enrichment artifact:
dls-field-enrichment-ms-marginfi-202408
artifact ID 10925020784
digest sha256:d7096c47ff1ba2d3935a06ce10196871060eb42d07ea39e8da87a403d022004a

Partition:
marginfi-202408
13,056 / 13,056 successful Marginfi liquidations enriched
missing=0
extra=0
duplicate=0
semantic_conflict=0
baseline_anomaly=0

SOL-collateral subset is defined exactly by the same source-authoritative bank registry used by the
parent source census. No new token mapping is introduced.

## Frozen shard assignment

Exactly 16 shards, indices 0..15.

For each canonical SOL-population identity:

identity =
signature + "|" + canonical-json(instructionAddress)

h =
SHA256(identity as UTF-8)

shard_index =
integer(first 16 hex digits of h, base16) mod 16

No timestamp, amount, token output, direction, market price, return or PnL participates in assignment.

## Shard semantics

Each shard applies exactly the same:
- exact-slot transaction retrieval;
- Marginfi canonical instruction verification;
- post-liquidation Jupiter V6 membership rule;
- route-root semantics;
- SwapEvent decoder;
- ordered simple-chain rule;
- SOL/liability endpoint direction semantics.

Shard COMPLETE requires:
- exact assigned canonical identities processed;
- duplicate identity count = 0;
- unresolved transport errors = 0;
- structural identity conflicts = 0.

Direction incompleteness is preserved for global adjudication and is not hidden.

## Global reconstruction

The fallback merge MUST:
1. read the canonical August field partition and bank registry;
2. reconstruct the full canonical August SOL identity set independently;
3. require all 16 shard receipts COMPLETE;
4. require shard-union population identities exactly equal canonical population identities;
5. require duplicate population identities = 0;
6. require route-member identities be a subset of population;
7. preserve every SOURCE_EVIDENCE_INCOMPLETE / DIRECTION_AMBIGUOUS row;
8. apply the unchanged parent source thresholds.

If the original monthly August job also completes:
- population identity set MUST match exactly;
- route-member identity set MUST match exactly;
- source adjudications MUST reconcile;
- any discrepancy fails closed.

No favorable source result may be selected preferentially.

## Firewall

source_only=true
jul_sep_market_outcomes_opened=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
