# DLS — MARGINFI SOL EXCEPTIONAL-FLOW EXHAUSTION / REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-flow-exhaustion-rebound-v01
Status: FROZEN BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family ID:
DLS-MARGINFI-SOL-FLOW-EXHAUSTION-REBOUND-001

## Why this is a new family

The prior family DLS-MARGINFI-SOL-FLOW-TURNOVER-IMPACT-001 tested:
- source-proven exceptional forced SOL selling;
- frozen flow-turnover Q90;
- SHORT SOLUSDT;
- 1-minute hold;
- Apr-Jun 2024 Development.

It terminated:
MARGINFI_SOL_FLOW_TURNOVER_DEVELOPMENT_NO_EDGE

Its gross result was negative before costs. This new family does NOT reopen, retune, or rescue Apr-Jun.
It tests a materially different mechanism in a still-unopened market period:

exceptional forced selling may represent temporary exhaustion/overshoot, followed by immediate rebound.

Jul-Sep 2024 is reserved as this new family's Development and MUST remain unopened until source authority
passes under the frozen rules below.

## Immutable feature definition

Reuse exactly the already-frozen feature from:
MARGINFI_SOL_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md

For each source cascade:

cascade_sold_sol =
sum(first decoded Jupiter SwapEvent inputAmount / 1e9)

Decision time A =
first full UTC minute strictly after cascade end.

pre5m_base_volume_sol =
sum Binance public USDT-M SOLUSDT perpetual 1m base-asset volume across [A-5m, A).

flow_turnover_intensity =
cascade_sold_sol / pre5m_base_volume_sol

No OHLC, future volume, returns, or PnL enters signal construction.

## Immutable threshold

Reuse EXACTLY the feature-only calibration threshold frozen before Apr-Jun outcomes:

FLOW_TURNOVER_INTENSITY_Q90 = 1.0307255992127644e-05

Authority:
- calibration run 36686002313
- artifact ID 11083738178
- digest sha256:6cacadfffce7225984258a634d0df0ac5685c0a7915bedc9e0a0e595fabc1327
- classification MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_PASS
- N=203 feature-only cascades
- nearest-rank Q90
- OHLC/returns/PnL unopened during calibration.

No re-calibration is permitted.
No alternative percentile may be inspected.

## Source semantics

Eligible event requires:
- protocol Marginfi;
- lending_account_liquidate;
- asset mint wrapped/native SOL:
  So11111111111111111111111111111111111111112
- post-liquidation Jupiter V6 route;
- SOURCE COMPLETE;
- classification DIRECTION_PROVEN;
- route_semantic COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN;
- asset_label SIGNED_SELL_PRESSURE_PROVEN;
- first decoded SwapEvent inputMint = SOL;
- first decoded SwapEvent inputAmount > 0.

No liability-mint filter.
No hop-count filter.
No amount filter.
No event-count filter.
No time-of-day filter.

## Frozen cascade construction

Sort source events by:
timestamp, signature, canonical instructionAddress.

A subsequent eligible event remains in the current cascade iff its source timestamp is <= 5 minutes
after the immediately preceding eligible event timestamp.

Otherwise close the cascade and start a new one.

This is the exact structural source rule used by the prior family. It is not re-estimated here.

## Development source window

[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

Canonical Marginfi field-enrichment authority:

July 2024:
- artifact ID 10924100354
- digest sha256:849ba0036e88294ba94623e7b0dc7fc1e15c7b53620675f4f082981f01350773
- partition marginfi-202407
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched 4,907 / 4,907
- missing=0 extra=0 duplicate=0 semantic_conflict=0 baseline_anomaly=0

August 2024:
- artifact ID 10925020784
- digest sha256:d7096c47ff1ba2d3935a06ce10196871060eb42d07ea39e8da87a403d022004a
- partition marginfi-202408
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched 13,056 / 13,056
- missing=0 extra=0 duplicate=0 semantic_conflict=0 baseline_anomaly=0

September 2024:
- artifact ID 10924302485
- digest sha256:361ea31d4aee8df441d9f44bcfc2a909949d624fdf07c265319540ab03da85a1
- partition marginfi-202409
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched 1,558 / 1,558
- missing=0 extra=0 duplicate=0 semantic_conflict=0 baseline_anomaly=0

Bank registry authority remains:
- run 36312418451
- artifact ID 10929339072
- classification MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS

No new population scan may redefine these partitions.

## Development source PASS gate

All three monthly partitions must:
- retain FIELD_ENRICHMENT_PARTITION_PASS;
- adjudicate every SOL-population identity for Jupiter route membership;
- have no duplicate population identities;
- produce route_member_count > 0 globally;
- source-complete rate >= 95%;
- deterministic direction rate among complete >= 90%;
- direction ambiguity = 0;
- contradictions = 0;
- global source errors = 0.

PASS:
MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS

Otherwise fail closed:
MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_BLOCKED

## Frozen market hypothesis

ONLY after source PASS may Jul-Sep market outcomes be opened.

For each source cascade:
1. compute the immutable flow_turnover_intensity from source amount and [A-5m,A) base volume;
2. signal iff intensity >= immutable Q90;
3. side = LONG SOLUSDT;
4. entry = OPEN of minute A;
5. exit = OPEN of A + 1 minute.

Mechanism:
exceptional forced SOL selling relative to immediately preceding execution-market turnover may exhaust
forced sellers / temporarily overshoot, producing a short-lived rebound after the cascade ends.

The LONG direction is frozen before Jul-Sep outcomes.
The 1-minute horizon is deliberately symmetric with the prior immediate-impact test.
No alternate hold is authorized.

## Funding firewall

Exclude candidate if [entry, exit] contains:
00:00 UTC, 08:00 UTC, or 16:00 UTC.

## Frozen execution costs

Primary:
- MEXC Futures API taker fee = 8 bps per side;
- slippage = 2 bps per side;
- approximate round trip = 20 bps.

Stress descriptive:
- taker fee unchanged;
- slippage = 5 bps per side;
- approximate round trip = 26 bps.

Gross is always reported separately.

## Development folds

Development:
[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

F1:
[2024-07-01T00:00:00Z, 2024-09-01T00:00:00Z)

F2:
[2024-09-01T00:00:00Z, 2024-10-01T00:00:00Z)

## Frozen Development gate

MARGINFI_SOL_EXHAUSTION_REBOUND_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable trade count >= 25;
2. distinct UTC entry days >= 8;
3. nominal net mean > 0;
4. nominal net median > 0;
5. nominal net PF > 1.10;
6. F1 trade count >= 15;
7. F2 trade count >= 8;
8. F1 nominal net mean > 0;
9. F2 nominal net mean > 0;
10. UTC-day block-bootstrap 95% CI lower bound of nominal net mean > 0.

Bootstrap:
- 20,000 replicates
- UTC entry-day blocks
- seed 26100101

Else:
MARGINFI_SOL_EXHAUSTION_REBOUND_DEVELOPMENT_NO_EDGE

## Future boundary

ONLY if Development SURVIVES may a later untouched period be considered for OOS.

No later market period is automatically authorized by this freeze.
A separate OOS source/data binding must be frozen before opening it.

2025 and 2026 remain protected.

## Forbidden rescue

After Jul-Sep market outcomes open, V0.1 may NOT:
- alter Q90;
- inspect/select Q80/Q85/Q95;
- alter the 5-minute turnover denominator;
- use quote volume instead of base volume;
- alter 5-minute cascade linkage;
- flip LONG to SHORT;
- change 1-minute hold;
- add event-count, notional, amount, hop, liability, venue or time filters;
- alter costs;
- remove funding firewall;
- tune using Jul-Sep;
- open a later period if Development fails.

## Firewall

jul_sep_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
