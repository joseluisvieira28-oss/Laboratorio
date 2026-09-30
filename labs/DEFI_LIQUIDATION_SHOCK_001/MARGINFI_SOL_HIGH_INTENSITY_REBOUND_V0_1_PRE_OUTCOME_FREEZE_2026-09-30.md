# DLS — MARGINFI SOL HIGH-INTENSITY REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-09-30
Branch: dls-marginfi-high-intensity-rebound-v01
Status: FROZEN BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family ID:
DLS-MARGINFI-SOL-HIGH-INTENSITY-REBOUND-001

## Scientific provenance

This family is NEW.

It is motivated by a failed prior family whose frozen SHORT hypothesis showed negative gross returns
after exceptional flow-to-turnover events in Apr-Jun 2024.

That prior family remains terminally closed:
MARGINFI_SOL_FLOW_TURNOVER_DEVELOPMENT_NO_EDGE

Apr-Jun market outcomes are discovery history only and may not validate this family.

Jul-Sep 2024 market outcomes remain unopened as of this freeze.

## Source event authority

Eligible source events require:
- Marginfi lending_account_liquidate
- asset mint = So11111111111111111111111111111111111111112
- Jupiter route member
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- first decoded SwapEvent inputMint = SOL
- first decoded SwapEvent inputAmount > 0

No liability filter.
No hop filter.
No amount threshold.
No event-count threshold.
No time-of-day filter.

## Frozen source cascade

Exactly the already-validated 5-minute source-only linkage rule:

Sort eligible events by:
timestamp, signature, canonical instructionAddress.

Start a cascade at the first event.

Each next event belongs to the same cascade iff its source timestamp is <= 5 minutes after the
immediately previous eligible event timestamp.

Otherwise close the current cascade and start a new one.

For each cascade:
- first_event_time
- last_event_time
- source_event_count
- cascade_sold_sol = sum(first SwapEvent inputAmount / 1e9)
- exact source identities

No market outcome participates in cascade construction.

## Decision time

A = first full UTC minute strictly after last_event_time.

## Frozen flow-to-turnover feature

Execution-market turnover proxy:
Binance public USDT-M SOLUSDT perpetual 1-minute base-asset volume.

Use exactly the five complete minutes:
[A-5m, A)

pre5m_base_volume_sol =
sum of 1m base-asset volume over those five complete minutes.

flow_turnover_intensity =
cascade_sold_sol / pre5m_base_volume_sol

Required:
- checksum PASS
- unique monotonic minute timestamps
- all required five minutes present
- pre5m_base_volume_sol > 0

No post-entry volume may enter the feature.

## Frozen exceptional-flow threshold

Reuse exactly the outcome-blind feature calibration from Feb-Mar 2024:

Calibration run:
36686002313

Calibration artifact:
11083738178

Classification:
MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_PASS

Frozen Q90:
1.0307255992127644e-05

No recalibration.
No alternate percentile.
No threshold grid.
No Apr-Jun outcome-derived threshold.

## Jul-Sep canonical source partitions

July 2024:
- artifact ID 10924100354
- digest sha256:849ba0036e88294ba94623e7b0dc7fc1e15c7b53620675f4f082981f01350773
- partition marginfi-202407
- window [2024-07-01T00:00:00Z, 2024-08-01T00:00:00Z)
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched = 4,907 / 4,907
- missing=0, extra=0, duplicate=0, semantic conflicts=0

August 2024:
- artifact ID 10925020784
- digest sha256:d7096c47ff1ba2d3935a06ce10196871060eb42d07ea39e8da87a403d022004a
- partition marginfi-202408
- window [2024-08-01T00:00:00Z, 2024-09-01T00:00:00Z)
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched = 13,056 / 13,056
- missing=0, extra=0, duplicate=0, semantic conflicts=0

September 2024:
- artifact ID 10924302485
- digest sha256:361ea31d4aee8df441d9f44bcfc2a909949d624fdf07c265319540ab03da85a1
- partition marginfi-202409
- window [2024-09-01T00:00:00Z, 2024-10-01T00:00:00Z)
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched = 1,558 / 1,558
- missing=0, extra=0, duplicate=0, semantic conflicts=0

No source scan may redefine these populations.

## Jul-Sep source gate

For SOL-collateral rows from the fixed monthly populations:
- recover exact successful historical transaction;
- apply the exact validated Marginfi -> Jupiter multi-hop source semantics;
- preserve decoded SwapEvent amounts.

PASS requires:
1. all three monthly field partitions PASS;
2. population duplicate identities = 0;
3. route member count > 0;
4. source-complete rate >= 95%;
5. deterministic direction among source-complete >= 90%;
6. contradictions = 0.

PASS:
MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS

Threshold miss:
MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PARTIAL

Transport/source/identity conflict:
MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_BLOCKED

## Market hypothesis

Only if Jul-Sep source PASS:

For each Jul-Sep source cascade:
1. compute frozen flow_turnover_intensity using only [A-5m, A);
2. signal iff intensity >= frozen Q90;
3. enter LONG SOLUSDT at OPEN of minute A;
4. exit LONG at OPEN of A + 1 minute.

Hypothesis:
exceptionally large forced SOL selling relative to recent turnover produces immediate one-minute rebound
after the source cascade ends.

The LONG side and 1-minute hold are frozen before Jul-Sep market outcomes.

## Funding firewall

Exclude candidate if [entry, exit] contains:
00:00 UTC, 08:00 UTC, or 16:00 UTC.

## Frozen costs

Primary:
- MEXC Futures API taker fee = 8 bps per side
- slippage = 2 bps per side
- approximate round trip = 20 bps

Stress descriptive only:
- taker fee unchanged
- slippage = 5 bps per side
- approximate round trip = 26 bps

No maker fills.
No rebates.
No VIP assumptions.
No leverage benefit.

## Development window

[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

F1:
[2024-07-01T00:00:00Z, 2024-09-01T00:00:00Z)

F2:
[2024-09-01T00:00:00Z, 2024-10-01T00:00:00Z)

## Frozen Development gate

MARGINFI_SOL_HIGH_INTENSITY_REBOUND_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable trade count >= 25
2. distinct UTC entry days >= 8
3. nominal net mean > 0
4. nominal net median > 0
5. nominal net PF > 1.10
6. F1 trade count >= 15
7. F2 trade count >= 5
8. F1 nominal net mean > 0
9. F2 nominal net mean > 0
10. UTC-day block-bootstrap 95% CI lower bound > 0

Bootstrap:
- 20,000 replicates
- UTC entry-day blocks
- seed = 26093011

Otherwise:
MARGINFI_SOL_HIGH_INTENSITY_REBOUND_DEVELOPMENT_NO_EDGE

Source/market integrity failure:
MARGINFI_SOL_HIGH_INTENSITY_REBOUND_DEVELOPMENT_SOURCE_BLOCKED

## Future boundary

Only if Development SURVIVES:

Next OOS candidate:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

OOS remains CLOSED until source authority is separately acquired under unchanged semantics.

2025/2026 market outcomes remain protected.

## Forbidden rescue

After Jul-Sep outcomes open, V0.1 may NOT:
- change LONG to SHORT;
- change Q90;
- inspect/select Q80/Q85/Q95;
- change 5-minute pre-entry turnover;
- change 5-minute source cascade linkage;
- change 1-minute hold;
- add amount/event-count/hop/liability filters;
- optimize entry delay;
- filter hours/days;
- change primary costs;
- reuse Apr-Jun as validation;
- open Oct-Dec if Development fails.

Any materially distinct hypothesis requires a new family and untouched market period.

## Firewall

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
