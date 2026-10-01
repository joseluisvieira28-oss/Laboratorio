# DLS — MARGINFI ORCA ELEVATED FLOW REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-elevated-flow-rebound-v01
Status: FROZEN BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-ELEVATED-FLOW-REBOUND-001

## Scientific question

When source-proven Marginfi forced SOL selling through Orca Whirlpools is elevated relative to recent
SOLUSDT perpetual turnover (upper quartile, not only extreme top decile), does SOL exhibit immediate
one-minute exhaustion/rebound after the forced-flow cascade ends?

## Why Q75

The prior Q90 LONG family closed PRE-OUTCOME because the selected sample was structurally too sparse:
20 selected cascades, 6 days, September n=3.

No Jul-Sep OHLC, returns or PnL were opened.

Q75 is chosen as a new conventional upper-quartile exposure definition for statistical support.
It is not selected from any market outcome and no alternative percentile is compared on returns.

## Frozen feature authority

Use the immutable feature-only Orca calibration population:
- run 36816611039
- artifact ID 11141731925
- digest sha256:a87c854c4ea4f35653f21929c1d9ec302f2e38a6dfc3721fccde6f383ce82a72
- 192 valid cascades
- 36 distinct cascade-end days
- OHLC/returns/PnL unopened

Feature:
flow_turnover_intensity =
cascade_sold_sol / prior-five-complete-minute Binance USDT-M SOLUSDT base volume

Threshold method:
nearest-rank 75th percentile.

rank = ceil(0.75 * N)
Q75 = sorted_intensity[rank - 1]

The exact numeric Q75 must be frozen in a feature-only receipt BEFORE any Jul-Sep market outcome opens.

No Q70/Q80/Q85/Q90 performance comparison is authorized.

## Source authority

Jul-Sep Orca signed-flow source:
- run 36780139559
- artifact ID 11127536853
- classification MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS
- direction proven 7,717
- exact input amount proven 100%
- contradictions 0

## Frozen source cascade rule

Exactly the existing Orca 5-minute linkage rule:
- sort by timestamp, signature, instructionAddress
- next event joins same cascade iff <= 5 minutes after immediately previous eligible source event
- one cascade amount = sum exact source-proven SOL input amounts

Decision minute:
A = first full UTC minute strictly after cascade end.

## Frozen pre-outcome sample gate

Use Jul-Sep feature-only cascades and the frozen numeric Q75.

READY only if ALL:
1. selected cascades >= 35
2. distinct selected UTC days >= 10
3. F1 selected count >= 20
4. F2 selected count >= 8

F1:
[2024-07-01, 2024-09-01)

F2:
[2024-09-01, 2024-10-01)

If any fail:
MARGINFI_ORCA_ELEVATED_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

No OHLC/returns/PnL may be opened.

If all pass:
MARGINFI_ORCA_ELEVATED_REBOUND_PREOUTCOME_READY

## Frozen execution

Only if pre-outcome READY:

side = LONG SOLUSDT
entry = OPEN of minute A
exit = OPEN of A + 1 minute
one trade per selected cascade
no pyramiding
no scaling

Funding boundary exclusion:
00:00 / 08:00 / 16:00 UTC.

## Frozen costs

Primary:
- MEXC Futures API taker 8 bps/side
- slippage 2 bps/side
- ~20 bps round trip

Stress:
- slippage 5 bps/side
- ~26 bps round trip

No maker assumption/rebate/VIP/leverage benefit.

## Frozen Development gate

MARGINFI_ORCA_ELEVATED_REBOUND_DEVELOPMENT_SURVIVES only if ALL:
1. n >= 35
2. distinct UTC entry days >= 10
3. nominal mean > 0
4. nominal median > 0
5. nominal PF > 1.10
6. F1 n >= 20
7. F2 n >= 8
8. F1 nominal mean > 0
9. F2 nominal mean > 0
10. UTC-day block-bootstrap 95% CI lower > 0

Bootstrap:
- 20,000 replicates
- UTC entry-day blocks
- seed = 26100103

Otherwise:
MARGINFI_ORCA_ELEVATED_REBOUND_DEVELOPMENT_NO_EDGE

## Future boundary

If Development SURVIVES, no already-opened 2024 period may be used as OOS.
A later protected period requires separate operator authorization and source authority.

## Forbidden rescue

After Jul-Sep outcomes open:
- no Q75 change
- no alternative percentiles
- no LONG->SHORT change
- no hold change
- no amount/event/hop/liability/time filters
- no cost change
- no 2025 opening as rescue without separate authorization

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
