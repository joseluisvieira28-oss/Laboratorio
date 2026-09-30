# DLS — MARGINFI ORCA EXTREME FLOW REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-09-30
Branch: dls-marginfi-orca-impact-v01
Status: FROZEN BEFORE FULL ORCA CENSUS VERDICT AND BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-EXTREME-FLOW-REBOUND-001

## Scientific question

When source-proven Marginfi forced SOL selling is executed through Orca Whirlpools and is exceptionally
large relative to immediately preceding SOLUSDT perpetual turnover, does the route exhibit an immediate
one-minute rebound consistent with transient concentrated-liquidity impact and cross-venue arbitrage
replenishment?

This is a route-specific family.
It is distinct from:
- Jupiter/simple SOL continuation NO_EDGE;
- Jupiter post-cascade 15m reversion NO_EDGE;
- Jupiter-derived extreme-flow 1m SHORT continuation NO_EDGE;
- the prior Jul-Sep Jupiter-only rebound family, which closed PRE-OUTCOME for insufficient F2 sample.

Jul-Sep 2024 OHLC/returns remain unopened at this freeze.

## Source prerequisite

Market outcomes may open only after:

MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS

under:
MARGINFI_ORCA_FULL_JULSEP_SIGNED_FLOW_CENSUS_FREEZE_V0.1.md

Eligible source event requires:
- classification = DIRECTION_PROVEN;
- route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN;
- asset_label = SIGNED_SELL_PRESSURE_PROVEN;
- asset_mint = So11111111111111111111111111111111111111112;
- exact_route_input_amount is source-proven and > 0.

Event sold SOL:
exact_route_input_amount / 1,000,000,000

Events with direction proven but exact input amount unproven are excluded from V0.1 without estimation.

## Frozen cascade rule

Sort eligible events by:
timestamp, signature, canonical instructionAddress.

Start a cascade at the first event.

A subsequent event belongs to the same cascade iff its source timestamp is <= 5 minutes after the
immediately previous eligible event timestamp.

Otherwise close the cascade and start a new one.

For each cascade:
cascade_sold_sol = sum(event sold SOL)

Decision time:
A = first full UTC minute strictly after last_event_time.

No price/return participates in cascade formation.

## Frozen turnover feature

Historical feature authority:
Binance public USDT-M SOLUSDT perpetual 1-minute base-asset volume.

Use exactly the five complete minutes:
[A-5m, A)

pre5m_base_volume_sol =
sum base-asset volume over those five minutes.

flow_turnover_intensity =
cascade_sold_sol / pre5m_base_volume_sol

Required:
- published daily CHECKSUM SHA256 PASS;
- unique monotonic minute timestamps;
- all five feature minutes present;
- pre5m_base_volume_sol > 0.

No post-A volume may enter the feature.

## Frozen threshold

Reuse the outcome-blind feature-only calibration from run 36686002313.

Artifact:
11083738178

Frozen numeric threshold:
FLOW_TURNOVER_INTENSITY_Q90 = 1.0307255992127644e-05

No Orca-specific recalibration.
No Q80/Q85/Q95 inspection.
No threshold grid.

Signal iff:
flow_turnover_intensity >= 1.0307255992127644e-05

## Mandatory pre-outcome sample gate

Before any Jul-Sep OHLC/return/PnL is read, compute source + pre-entry-volume selection only.

READY only if ALL:
- selected signal count >= 25;
- selected distinct UTC decision days >= 8;
- F1 Jul-Aug selected >= 15;
- F2 September selected >= 8.

If any fail:
MARGINFI_ORCA_EXTREME_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

and V0.1 closes without opening Jul-Sep returns.

## Frozen market rule

Only after source PASS + pre-outcome READY:

side = LONG SOLUSDT

entry:
OPEN of minute A

exit:
OPEN of minute A + 1 minute

Only one trade per cascade.
If a later selected cascade would enter before an existing position exits, ignore that later candidate.

No pyramiding.
No scaling.

## Funding firewall

Exclude any candidate if [entry, exit] contains:
00:00 UTC, 08:00 UTC or 16:00 UTC.

## Frozen execution costs

Primary:
- MEXC Futures API taker fee = 8 bps per side;
- slippage = 2 bps per side;
- approximate round trip = 20 bps.

Stress descriptive only:
- same fee;
- slippage = 5 bps per side;
- approximate round trip = 26 bps.

Primary classification uses nominal only.

No maker assumption, rebate, VIP discount or leverage benefit.

## Development window and folds

Development:
[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

F1:
[2024-07-01T00:00:00Z, 2024-09-01T00:00:00Z)

F2:
[2024-09-01T00:00:00Z, 2024-10-01T00:00:00Z)

## Frozen Development gate

MARGINFI_ORCA_EXTREME_REBOUND_DEVELOPMENT_SURVIVES only if ALL:

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
- seed = 26093003

Otherwise:
MARGINFI_ORCA_EXTREME_REBOUND_DEVELOPMENT_NO_EDGE

Source/market-integrity failure:
MARGINFI_ORCA_EXTREME_REBOUND_DEVELOPMENT_SOURCE_BLOCKED

## Future boundary

Only if Development SURVIVES:

OOS candidate:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

Before OOS:
- Orca source authority must be acquired under unchanged semantics;
- exact same Q90;
- same cascade rule;
- same LONG side;
- same 1-minute hold;
- same costs.

2025/2026 remain protected.

## Forbidden rescue

After Jul-Sep outcomes open, V0.1 may NOT:
- change Q90;
- change five-minute denominator;
- change cascade linkage;
- flip LONG to SHORT;
- inspect/select another hold horizon;
- add event-count, amount, hop-count, liability or time-of-day filters;
- change costs;
- delete September;
- lower F2 sample threshold;
- open Oct-Dec after Development failure.

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
