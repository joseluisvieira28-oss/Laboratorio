# DLS — MARGINFI SOL EXTREME FLOW EXHAUSTION / REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-rebound-v01
Status: FROZEN BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family ID:
DLS-MARGINFI-SOL-EXTREME-FLOW-REBOUND-001

## Scientific question

When source-proven forced SOL selling through Marginfi -> Jupiter is exceptionally large relative to
the immediately preceding SOLUSDT perpetual turnover, does the forced move exhibit immediate one-minute
exhaustion / rebound after the source cascade ends?

This is a new family motivated by the terminal result of:
DLS-MARGINFI-SOL-FLOW-TURNOVER-IMPACT-001

That prior family tested SHORT continuation and closed:
MARGINFI_SOL_FLOW_TURNOVER_DEVELOPMENT_NO_EDGE

Its Apr-Jun gross result was negative before fees.
Apr-Jun outcomes are discovery history only and are prohibited from validating this family.

## Frozen feature authority

Reuse EXACTLY the already-frozen feature definition and numeric threshold from the feature-only
calibration that did not read OHLC/returns/PnL.

Calibration run:
36686002313

Calibration artifact:
dls-marginfi-sol-flow-turnover-calibration-v01
artifact ID 11083738178
digest sha256:6cacadfffce7225984258a634d0df0ac5685c0a7915bedc9e0a0e595fabc1327

Frozen threshold:
FLOW_TURNOVER_INTENSITY_Q90 = 1.0307255992127644e-05

Definition:
flow_turnover_intensity =
cascade_sold_sol / prior-five-complete-minute Binance USDT-M SOLUSDT base-asset volume

No alternative percentile is authorized.
No recalibration on Jul-Sep.
No Q80/Q85/Q95 inspection.

## Source event authority

Eligible source event requires:
- Marginfi lending_account_liquidate;
- asset mint = So11111111111111111111111111111111111111112;
- source-complete Jupiter route;
- classification = DIRECTION_PROVEN;
- route_semantic = COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN;
- asset_label = SIGNED_SELL_PRESSURE_PROVEN;
- first decoded SwapEvent inputMint = SOL;
- first decoded SwapEvent inputAmount > 0.

event_sold_sol =
first decoded SwapEvent inputAmount / 1,000,000,000

## Frozen cascade rule

Exactly unchanged from the parent feature family:

Sort eligible source events by:
timestamp, signature, canonical instructionAddress.

A subsequent event belongs to the same cascade iff its source timestamp is <= 5 minutes after the
immediately previous eligible event timestamp.

Cascade fields:
- first_event_time
- last_event_time
- cascade_sold_sol
- source_event_count
- exact member identities

Decision time:
A = first full UTC minute strictly after last_event_time.

## Frozen turnover denominator

Use Binance public USDT-M SOLUSDT perpetual 1-minute base-asset volume for exactly:

[A-5m, A)

pre5m_base_volume_sol = sum of the five complete minute base volumes.

Signal iff:
flow_turnover_intensity >= 1.0307255992127644e-05

No future volume may enter the feature.

## New hypothesis / execution rule

For every selected extreme-flow cascade:

side = LONG SOLUSDT

entry =
OPEN of minute A

exit =
OPEN of minute A + 1 minute

Only one trade per source cascade.

If a later selected cascade would enter before an existing trade exits:
ignore the later candidate.

No pyramiding.
No scaling.
No threshold by source_event_count.
No source amount threshold beyond the frozen flow-turnover Q90.

This 1-minute LONG rule is the exact directional mirror of the terminal 1-minute SHORT family.
No alternate hold horizon may be inspected inside V0.1.

## Funding firewall

Exclude a candidate if [entry, exit] contains:
00:00 UTC, 08:00 UTC, or 16:00 UTC.

## Market data

Historical research authority:
Binance public USDT-M SOLUSDT perpetual 1-minute daily klines.

Required:
- published CHECKSUM SHA256 PASS;
- unique monotonic timestamps;
- every required feature, entry and exit minute present.

Any hard integrity failure:
MARGINFI_SOL_EXTREME_REBOUND_DEVELOPMENT_SOURCE_BLOCKED

## Frozen execution costs

Primary:
- MEXC Futures API taker fee = 8 bps per side;
- slippage = 2 bps per side;
- approximate round-trip cost = 20 bps.

Stress descriptive only:
- same taker fee;
- slippage = 5 bps per side;
- approximate round trip = 26 bps.

Primary classification uses nominal only.

No maker fills.
No rebates.
No VIP fee discount.
No leverage benefit.

## Development source window

Jul-Sep 2024:

[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

Canonical Marginfi field-enrichment partitions:

July:
- artifact ID 10924100354
- digest sha256:849ba0036e88294ba94623e7b0dc7fc1e15c7b53620675f4f082981f01350773
- FIELD_ENRICHMENT_PARTITION_PASS
- 4,907 / 4,907 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic conflicts=0

August:
- artifact ID 10925020784
- digest sha256:d7096c47ff1ba2d3935a06ce10196871060eb42d07ea39e8da87a403d022004a
- FIELD_ENRICHMENT_PARTITION_PASS
- 13,056 / 13,056 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic conflicts=0

September:
- artifact ID 10924302485
- digest sha256:361ea31d4aee8df441d9f44bcfc2a909949d624fdf07c265319540ab03da85a1
- FIELD_ENRICHMENT_PARTITION_PASS
- 1,558 / 1,558 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic conflicts=0

No alternative population scan may redefine these monthly populations.

## Jul-Sep source PASS

Apply exactly the existing Marginfi -> Jupiter multi-hop source semantics.

MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS only if:
1. all three canonical field partitions PASS;
2. population duplicate identities = 0;
3. route-member count > 0;
4. source-complete direction evidence >= 95%;
5. deterministic direction among source-complete >= 90%;
6. contradictions = 0;
7. no unresolved structural/source identity conflict.

PARTIAL:
valid source but scientific source thresholds miss.

BLOCKED:
transport, identity, decoder, registry or structural conflict.

No Jul-Sep market outcome may be opened before source PASS.

## Development folds

Development:
[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

F1:
[2024-07-01T00:00:00Z, 2024-09-01T00:00:00Z)

F2:
[2024-09-01T00:00:00Z, 2024-10-01T00:00:00Z)

## Frozen Development gate

MARGINFI_SOL_EXTREME_REBOUND_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable trade count >= 25;
2. distinct UTC entry days >= 8;
3. nominal net mean > 0;
4. nominal net median > 0;
5. nominal net profit factor > 1.10;
6. F1 trade count >= 15;
7. F2 trade count >= 8;
8. F1 nominal net mean > 0;
9. F2 nominal net mean > 0;
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean > 0.

Bootstrap:
- 20,000 replicates
- complete UTC entry-day blocks
- seed = 26093002

Otherwise:
MARGINFI_SOL_EXTREME_REBOUND_DEVELOPMENT_NO_EDGE

## Future boundary

Only if Development SURVIVES:

OOS candidate:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

Before OOS market outcomes:
- source authority must be completed under unchanged semantics;
- Q90 unchanged;
- cascade rule unchanged;
- LONG unchanged;
- 1-minute hold unchanged;
- costs unchanged.

2025 and 2026 remain protected.

## Forbidden rescue

After Jul-Sep outcomes open, V0.1 may NOT:
- change Q90;
- inspect alternative percentiles;
- change 5-minute denominator;
- change LONG to SHORT;
- change 1-minute hold;
- inspect 2m/3m/5m/15m and select one;
- add event-count, amount, hop-count, liability or time filters;
- change costs;
- reopen Apr-Jun as validation;
- open Oct-Dec if Development fails.

Any materially different hypothesis requires a new family and untouched period.

## Firewall

apr_jun_reused_as_validation=false
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
