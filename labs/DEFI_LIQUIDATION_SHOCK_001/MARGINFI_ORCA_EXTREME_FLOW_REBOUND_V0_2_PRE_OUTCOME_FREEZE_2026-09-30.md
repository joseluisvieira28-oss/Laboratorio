# DLS — MARGINFI ORCA EXTREME FLOW REBOUND V0.2 — OCT-DEC PRE-OUTCOME FREEZE

Date: 2026-09-30
Branch: dls-marginfi-orca-impact-v02
Status: FROZEN BEFORE OCT-DEC 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-EXTREME-FLOW-REBOUND-002

## Why V0.2 exists

V0.1 Jul-Sep closed PRE-OUTCOME because its frozen F2 September sample gate produced 7 selected
signals vs required 8.

No Jul-Sep OHLC, return or PnL was opened.

V0.2 does not lower any threshold and does not reuse Jul-Sep as validation.
It moves the first market-outcome Development to the still-unopened Oct-Dec 2024 period while keeping
the economic hypothesis and execution rule unchanged.

## Source semantics

Use the exact source semantics frozen and validated under:
- MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_FREEZE_V0.1.md
- MARGINFI_ORCA_FULL_JULSEP_SIGNED_FLOW_CENSUS_FREEZE_V0.1.md

Orca program:
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc

Pinned Orca upstream commit:
f4b99e79e7140f3917e4ce81a2e8ad06ccdf8ce4

Eligible market event requires:
- Marginfi SOL collateral liquidation;
- post-liquidation Orca route;
- classification = DIRECTION_PROVEN;
- route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN;
- asset_label = SIGNED_SELL_PRESSURE_PROVEN;
- exact_route_input_amount source-proven and >0.

event_sold_sol =
exact_route_input_amount / 1,000,000,000

## Canonical Oct-Dec Marginfi field populations

All three were created before this family and are immutable input authority.

October 2024:
- artifact ID 10924878593
- digest sha256:a6635c5a7ca8b2d1d49670acb5482dda82db56459af068739c6acc535c82b6d7
- partition marginfi-202410
- FIELD_ENRICHMENT_PARTITION_PASS
- 1,432 / 1,432 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic_conflict=0, baseline_anomaly=0

November 2024:
- artifact ID 10925847270
- digest sha256:43f749aeca0999f8e35262c73ca5ac8bbf7c0920f04db205d24e969de6a61fd7
- partition marginfi-202411
- FIELD_ENRICHMENT_PARTITION_PASS
- 10,141 / 10,141 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic_conflict=0, baseline_anomaly=0

December 2024:
- artifact ID 10927608033
- digest sha256:0228f85921f9a30d6310b0fa3e5798f2695b9750c4add737e82a7611959892a4
- partition marginfi-202412
- FIELD_ENRICHMENT_PARTITION_PASS
- 4,880 / 4,880 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic_conflict=0, baseline_anomaly=0

Marginfi bank->mint authority remains:
run 36312418451
artifact ID 10929339072
MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS

## Frozen SOL population construction

From each canonical monthly enriched population:
- select rows whose semantic_accounts.asset_bank maps exactly to
  So11111111111111111111111111111111111111112;
- preserve exact signature, slot, timestamp, transactionIndex, instructionAddress, asset_bank,
  liab_bank, asset_mint and liab_mint;
- no other source or market field participates.

The exact union of October + November + December SOL rows becomes the immutable V0.2 canonical source
population.

Population duplicates, missing bank mappings or field-authority conflicts => SOURCE_BLOCKED.

## Full Orca source census

Every canonical Oct-Dec SOL population identity must receive exactly one adjudication using the unchanged
Orca decoder semantics.

Deterministic sharding:
int(SHA256(signature + "|" + canonical-json(instructionAddress)),16) mod 16.

No population identity may be dropped.

Global source PASS:
MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS only if:
- all 16 shards transport PASS;
- every canonical population identity adjudicated exactly once;
- missing=0, extra=0, duplicate=0;
- Orca route presence >0;
- source-complete among Orca-presence >=95%;
- direction-proven among source-complete >=90%;
- contradictions=0.

## Frozen cascade rule

Sort eligible events by:
timestamp, signature, canonical instructionAddress.

A subsequent event joins the current cascade iff its timestamp is <=5 minutes after the immediately
previous eligible event.

Otherwise close the cascade and start another.

cascade_sold_sol = sum(event_sold_sol)

Decision time:
A = first full UTC minute strictly after cascade last_event_time.

## Frozen feature

Binance public USDT-M SOLUSDT perpetual 1m base-asset volume.

Use exactly:
[A-5m, A)

pre5m_base_volume_sol = sum of the five complete minute base volumes

flow_turnover_intensity =
cascade_sold_sol / pre5m_base_volume_sol

Daily archive CHECKSUM must PASS.
Required minutes must exist.
No post-A volume enters the feature.

## Frozen threshold

Reuse the original outcome-blind calibration:

run 36686002313
artifact ID 11083738178

Q90 =
1.0307255992127644e-05

No recalibration.
No threshold grid.
No alternative percentile inspection.

Signal iff:
flow_turnover_intensity >= Q90.

## Mandatory pre-outcome sample gate

Before any Oct-Dec OHLC/return/PnL is opened:

READY only if:
- selected count >=25;
- selected distinct UTC days >=8;
- F1 Oct-Nov selected >=15;
- F2 December selected >=8.

Otherwise:
MARGINFI_ORCA_EXTREME_REBOUND_V02_PREOUTCOME_INSUFFICIENT_SAMPLE

and V0.2 closes without market outcomes.

## Frozen market hypothesis

Only after source PASS + pre-outcome READY:

side = LONG SOLUSDT

entry =
OPEN of minute A

exit =
OPEN of minute A + 1 minute

Only one trade per cascade.
No pyramiding, scaling or hold extension.

## Funding firewall

Exclude if [entry, exit] contains:
00:00 UTC, 08:00 UTC or 16:00 UTC.

## Frozen execution costs

Primary:
- MEXC Futures API taker fee 8 bps per side;
- slippage 2 bps per side;
- ~20 bps round trip.

Stress descriptive only:
- same fee;
- slippage 5 bps per side;
- ~26 bps round trip.

Primary classification uses nominal only.

## Development

Window:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

F1:
[2024-10-01T00:00:00Z, 2024-12-01T00:00:00Z)

F2:
[2024-12-01T00:00:00Z, 2025-01-01T00:00:00Z)

## Frozen Development gate

MARGINFI_ORCA_EXTREME_REBOUND_V02_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable trade count >=25;
2. distinct UTC entry days >=8;
3. nominal net mean >0;
4. nominal net median >0;
5. nominal net PF >1.10;
6. F1 n >=15;
7. F2 n >=8;
8. F1 nominal net mean >0;
9. F2 nominal net mean >0;
10. UTC-day block-bootstrap 95% CI lower bound >0.

Bootstrap:
- 20,000 replicates
- complete UTC entry-day blocks
- seed 26093004

Otherwise:
MARGINFI_ORCA_EXTREME_REBOUND_V02_DEVELOPMENT_NO_EDGE

## Future boundary

2025 market outcomes remain CLOSED regardless of this freeze.

If Development survives, a separately frozen OOS family is required before any 2025 outcome can open.

## Forbidden rescue

After Oct-Dec outcomes open, V0.2 may NOT:
- change Q90;
- change 5-minute cascade/turnover windows;
- flip LONG to SHORT;
- inspect alternate hold horizons;
- add amount/event-count/hop/liability/time filters;
- change costs;
- alter folds;
- lower F2 sample or Development gates;
- open 2025 as rescue after failure.

## Firewall

jul_sep_market_outcomes_opened=false
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
