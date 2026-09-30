# DLS — MARGINFI SOL FLOW-TO-TURNOVER IMPACT V0.1 — PRE-OUTCOME FREEZE

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-impact-v01
Status: FROZEN BEFORE APR-JUN 2024 MARKET OUTCOMES

Family ID:
DLS-MARGINFI-SOL-FLOW-TURNOVER-IMPACT-001

## Scientific question

When source-proven forced SOL selling through Marginfi -> Jupiter is exceptionally large relative to
recent SOLUSDT perpetual market turnover, is there an immediately tradable continuation effect after
the forced-flow cascade ends?

This is a materially new family.

Prior families are terminal and may not be rescued:
- Marginfi SOL 5-minute simple continuation: NO_EDGE
- Marginfi SOL 15-minute post-cascade reversion: NO_EDGE

Their market outcomes may not be reused as validation for this family.

## Source event authority

A source event is eligible only if:
- protocol = Marginfi;
- liquidation instruction = lending_account_liquidate;
- asset mint = wrapped/native SOL:
  So11111111111111111111111111111111111111112
- Jupiter route is source-complete;
- classification = DIRECTION_PROVEN;
- route_semantic = COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN;
- asset_label = SIGNED_SELL_PRESSURE_PROVEN;
- first decoded SwapEvent inputMint = SOL;
- first decoded SwapEvent inputAmount > 0.

No liability-mint filter.
No hop-count filter.
No event-count filter.
No time-of-day filter.

## SOL amount

For each eligible source event:

event_sold_sol =
first decoded SwapEvent inputAmount / 1,000,000,000

The 1e9 divisor is fixed for SOL atomic units.

For a source cascade:

cascade_sold_sol = sum(event_sold_sol over all eligible member events)

No output amount or USD notional is used.

## Frozen cascade construction

Exactly reuse the already frozen source-only cascade rule:

Sort eligible events by:
timestamp, signature, canonical instructionAddress.

Start a cascade at the first event.

Each subsequent event belongs to the same cascade iff its source timestamp is <= 5 minutes after the
immediately previous eligible event timestamp.

Otherwise the current cascade closes and a new cascade starts.

For each cascade:
- first_event_time
- last_event_time
- cascade_sold_sol
- source_event_count
- exact member identities

No market price or future return participates in cascade formation.

## Decision time

A = first full UTC minute strictly after last_event_time.

## Market-turnover feature

Execution-market turnover proxy:
Binance public USDT-M SOLUSDT perpetual 1-minute base-asset volume.

For each cascade, use exactly the five complete minutes immediately preceding A:

[A-5m, A)

pre5m_base_volume_sol =
sum of Binance SOLUSDT 1m base-asset volume across those five minutes.

Required integrity:
- daily archive published checksum must pass;
- timestamps unique and monotonic;
- all five required minutes present;
- pre5m_base_volume_sol > 0.

Then:

flow_turnover_intensity =
cascade_sold_sol / pre5m_base_volume_sol

This is a turnover ratio, not claimed to be order-book depth.

No future minute or post-entry volume may enter the feature.

## Feature-only calibration period

Calibration period:
[2024-02-01T00:00:00Z, 2024-04-01T00:00:00Z)

Canonical source artifact:
run 36589912203 attempt 2
artifact ID 11053637340
digest sha256:8100803148ead42807322446fcbf9f7c678b6a6589e0c4509f4ddcf930afab3d

Calibration is FEATURE-ONLY:
- source event identity;
- source sold amount;
- pre-entry Binance base volume.

The calibration script MUST NOT read:
- open/high/low/close;
- post-entry volume;
- return;
- PnL.

## Frozen exceptional-flow threshold

Compute flow_turnover_intensity for every valid calibration cascade.

Sort ascending.

Threshold = nearest-rank 90th percentile:

rank = ceil(0.90 * N), using 1-based indexing.

Q90 = sorted_intensity[rank - 1]

The exact numeric Q90 is then frozen into an immutable calibration receipt BEFORE any Apr-Jun market
return is opened.

No alternative percentile may be inspected for selection.
No Q80/Q85/Q95 comparison.
No threshold grid.
No outcome-based threshold adjustment.

Calibration PASS requires:
- >= 100 valid calibration cascades;
- >= 20 distinct UTC cascade-end days;
- 0 checksum/integrity hard errors;
- 0 missing required pre-entry volume minutes;
- Q90 > 0.

Otherwise:
MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_BLOCKED

## Development source window

Apr-Jun 2024:

[2024-04-01T00:00:00Z, 2024-07-01T00:00:00Z)

The canonical Marginfi field-enrichment partitions are fixed:

April 2024:
- artifact ID 10922050090
- digest sha256:5ad6ddfdd9ffc101b67ab7a6080896b4ff4d7bcb25e12800969cced6eff57c5c
- FIELD_ENRICHMENT_PARTITION_PASS
- 11,738 / 11,738 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic conflicts=0

May 2024:
- artifact ID 10923362198
- digest sha256:0ef091e91e762678d70ccbd4a81d258eb50e511803c3503fdf9021fc8529e8a2
- FIELD_ENRICHMENT_PARTITION_PASS
- 9,197 / 9,197 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic conflicts=0

June 2024:
- artifact ID 10940537035
- digest sha256:07dedceef8f53ce7fc3286dc3621694129c8f65349b5d2ca959b9a4c00e17811
- FIELD_ENRICHMENT_PARTITION_PASS
- 6,215 / 6,215 successful liquidations enriched
- missing=0, extra=0, duplicate=0, semantic conflicts=0

No new population scan may redefine these partitions.

For SOL-population rows, recover exact historical successful transaction and apply exactly the already
validated Marginfi -> Jupiter V0.2 multi-hop source semantics.

Development source PASS requires:
- all three canonical monthly field partitions PASS;
- every SOL-population identity adjudicated for Jupiter route membership;
- population duplicate identities = 0;
- route-member count > 0;
- source-complete rate >= 95%;
- deterministic direction among source-complete >= 90%;
- contradictions = 0.

PASS classification:
MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_PASS

Threshold miss with valid source:
MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_PARTIAL

Source/identity/transport conflict:
MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_BLOCKED

## Market hypothesis

Only if BOTH:
- feature calibration PASS, and
- Apr-Jun source PASS

may Apr-Jun market outcomes be opened.

For each Apr-Jun source cascade:
1. compute frozen flow_turnover_intensity using only [A-5m, A);
2. signal iff intensity >= frozen Q90 calibration threshold;
3. side = SHORT SOLUSDT;
4. enter at OPEN of minute A;
5. exit at OPEN of A + 1 minute.

Rationale frozen before outcomes:
exceptional forced selling relative to recent execution-market turnover is hypothesized to create
immediate short-lived continuation from liquidity depletion / incomplete absorption.

The 1-minute hold is chosen as an immediate-impact hypothesis and is not derived from Apr-Jun outcomes.

## Funding firewall

Exclude a candidate if [entry, exit] contains:
00:00 UTC, 08:00 UTC, or 16:00 UTC.

Funding itself is not modeled.

## Frozen execution costs

Primary:
- MEXC Futures API taker fee = 8 bps per side;
- slippage = 2 bps per side;
- approximate round trip = 20 bps.

Stress descriptive only:
- same taker fee;
- slippage = 5 bps per side;
- approximate round trip = 26 bps.

Primary classification uses nominal only.

No maker fills, rebates, VIP discounts or leverage benefit.

## Development folds

Development:
[2024-04-01T00:00:00Z, 2024-07-01T00:00:00Z)

F1:
[2024-04-01T00:00:00Z, 2024-06-01T00:00:00Z)

F2:
[2024-06-01T00:00:00Z, 2024-07-01T00:00:00Z)

## Frozen Development gate

MARGINFI_SOL_FLOW_TURNOVER_DEVELOPMENT_SURVIVES only if ALL:

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
- seed = 26093001

Otherwise:
MARGINFI_SOL_FLOW_TURNOVER_DEVELOPMENT_NO_EDGE

## Future boundary

Only if Development SURVIVES:

OOS candidate:
[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

Before OOS market outcomes:
- source authority must be acquired under unchanged semantics;
- exact frozen Q90 threshold must remain unchanged;
- cascade construction unchanged;
- side SHORT unchanged;
- 1-minute hold unchanged;
- costs unchanged.

2025/2026 market outcomes remain protected.

## Forbidden rescue

After Apr-Jun outcomes open, V0.1 may NOT:
- change percentile threshold;
- inspect/select alternative percentiles;
- change 5-minute turnover denominator;
- switch to quote volume;
- change cascade linkage;
- change SHORT to LONG;
- change 1-minute hold;
- add amount/event-count/hop/liability filters;
- optimize time-of-day;
- change costs;
- open Jul-Sep if Development fails;
- use Fev-Mar returns as a rescue validation set.

Any materially distinct hypothesis requires a new family and untouched market period.

## Firewall

apr_jun_market_outcomes_opened=false
jul_sep_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
