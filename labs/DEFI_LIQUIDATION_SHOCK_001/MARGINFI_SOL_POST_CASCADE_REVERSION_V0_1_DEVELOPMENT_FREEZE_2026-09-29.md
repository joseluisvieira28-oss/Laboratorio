# DLS — MARGINFI SOL POST-CASCADE TRANSIENT REVERSION V0.1 — DEVELOPMENT FREEZE

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN BEFORE FEB-MAR 2024 MARKET OUTCOMES AND BEFORE FEB-MAR SOURCE-GATE RESULT

Conditional source prerequisite:
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PASS

If the source prerequisite does not PASS, this market experiment MUST NOT run.

## Scientific question

After a temporally clustered burst of source-proven Marginfi native-SOL collateral selling through Jupiter
has ended, does SOL exhibit a short-horizon rebound consistent with transient market impact / liquidity
replenishment, large enough to survive realistic automated futures execution costs?

This is a new family. January 2024 market outcomes are discovery history only and are prohibited from
validation of this family.

## Frozen source-event eligibility

Use only Feb-Mar source rows satisfying all:
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- asset_mint = So11111111111111111111111111111111111111112

No amount threshold.
No liability-mint filter.
No hop-count filter.
No time-of-day filter.
No market-return field participates in event selection.

## Frozen source-only cascade construction

Sort eligible source events by:
timestamp, signature, canonical instructionAddress.

Start a cascade at the first eligible event.

For each next eligible event:
- if its source timestamp is <= 5 minutes after the immediately previous eligible event timestamp,
  it belongs to the same cascade;
- otherwise the current cascade closes and a new cascade starts.

The 5-minute linkage window is fixed before market outcomes.

Cascade fields:
- first_event_time
- last_event_time
- source_event_count
- exact member identities

No price movement, token amount or return participates in cascade formation.

## Frozen signal and execution

For every completed cascade:

A = first full UTC minute strictly after last_event_time.

Enter:
LONG SOLUSDT at the OPEN of minute A.

Exit:
OPEN of minute A + 15 minutes.

Only one trade per source cascade.
No pyramiding.
No extension when later market movement occurs.
If a newly formed cascade would produce an entry before a previous position's exit, ignore the later
trade candidate as an operational collision.

## Funding firewall

Exclude any candidate whose [entry, exit] interval contains:
00:00 UTC, 08:00 UTC or 16:00 UTC.

Funding itself is not modeled.

## Frozen market data

Historical research authority:
Binance public USDT-M SOLUSDT perpetual futures 1-minute daily archives.

Every archive must pass published CHECKSUM SHA256 verification and timestamp uniqueness/monotonicity.

Any required market-data integrity failure:
MARGINFI_SOL_REVERSION_DEVELOPMENT_SOURCE_BLOCKED

Binance is research-price authority only, not live execution authority.

## Frozen costs

Primary automated execution model:
- MEXC Futures API taker fee = 8 bps per side;
- slippage = 2 bps per side;
- approximate nominal round-trip cost = 20 bps.

Stress, descriptive only:
- same fee;
- slippage = 5 bps per side;
- approximate round-trip cost = 26 bps.

Primary classification uses nominal only.
Stress may not rescue or kill the primary classification.

No maker fills, rebates, fee discounts or leverage benefit are assumed.

## Frozen Development window

Source and market outcomes:
[2024-02-01T00:00:00Z, 2024-04-01T00:00:00Z)

Temporal folds:
F1 = entry in February 2024
F2 = entry in March 2024

January 2024 is NOT part of Development.

## Frozen Development gate

MARGINFI_SOL_REVERSION_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable trade count >= 30;
2. distinct UTC entry days >= 8;
3. nominal net mean > 0;
4. nominal net median > 0;
5. nominal net profit factor > 1.10;
6. F1 trade count >= 10;
7. F2 trade count >= 10;
8. F1 nominal net mean > 0;
9. F2 nominal net mean > 0;
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean > 0.

Bootstrap:
- 20,000 replicates
- complete UTC entry-day blocks
- seed = 26092915

Otherwise:
MARGINFI_SOL_REVERSION_DEVELOPMENT_NO_EDGE

## Frozen future boundary

Only if Development SURVIVES:
- OOS/holdout candidate period = [2024-04-01T00:00:00Z, 2024-07-01T00:00:00Z)
- no Apr-Jun market outcome may open until its source population and signed-flow authority are acquired
  under the unchanged source semantics;
- the exact same 5-minute cascade rule, LONG side, 15-minute hold, collision handling and primary cost
  model must be used.

2025/2026 market outcomes stay closed.

## Forbidden rescue

After Feb-Mar outcomes open, V0.1 may NOT:
- change LONG to SHORT;
- change the 5-minute cascade linkage;
- change the 15-minute hold;
- add event-count or amount thresholds;
- select hop count;
- select liability mint;
- select specific days/hours;
- optimize delay or exit;
- change primary costs;
- reinterpret January as validation;
- open Apr-Jun unless Development SURVIVES.

Any materially distinct idea requires a new family and untouched validation period.

## Firewall

jan_2024_validation_used=false
feb_mar_2024_market_outcomes_opened_after_freeze=true
apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
