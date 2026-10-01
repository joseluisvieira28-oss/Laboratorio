# DLS — MARGINFI ORCA DAILY-MAX SHOCK REBOUND V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-dailymax-rebound-v01
Status: FROZEN BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-DAILYMAX-REBOUND-001

## Scientific question

Does the single largest source-proven Marginfi -> Orca forced-SOL flow shock of each UTC day exhibit an
immediate one-minute exhaustion/rebound after the cascade ends?

This family is motivated by a source-only structural observation:
high flow-turnover cascades are strongly clustered into a small number of days.

No Jul-Sep OHLC, return or PnL has been opened.

## Source + feature authority

Canonical Orca Jul-Sep signed-flow source:
- run 36780139559
- artifact ID 11127536853
- classification MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS
- direction proven 7,717
- exact input amount proven 100%
- contradictions 0

Canonical feature-only Orca flow-turnover calibration:
- run 36816611039
- artifact ID 11141731925
- classification MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS
- 192 valid source cascades
- 36 distinct cascade-end days
- OHLC/returns/PnL unopened

Feature:
flow_turnover_intensity =
cascade_sold_sol / prior-five-complete-minute Binance USDT-M SOLUSDT base volume

## Frozen daily selection

Partition all calibration/source cascades by UTC date of decision_time.

For each UTC decision day:
- select exactly ONE cascade:
  the cascade with maximum flow_turnover_intensity;
- deterministic tie-break:
  earliest decision_time, then lexicographically smallest cascade_id.

No percentile threshold.
No amount threshold.
No event-count threshold.
No hop-count/liability filter.
No time-of-day filter.

This creates at most one candidate trade per UTC day.

## Frozen pre-outcome sample gate

Before reading Jul-Sep OHLC/returns, daily-max selection must satisfy ALL:
1. selected days >= 25
2. F1 selected days >= 15
3. F2 selected days >= 8

F1:
[2024-07-01, 2024-09-01)

F2:
[2024-09-01, 2024-10-01)

READY:
MARGINFI_ORCA_DAILYMAX_REBOUND_PREOUTCOME_READY

Otherwise:
MARGINFI_ORCA_DAILYMAX_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE

No market outcome may be opened unless READY.

## Frozen execution

Only if pre-outcome READY:

side = LONG SOLUSDT
entry = OPEN of decision minute A
exit = OPEN of A + 1 minute

One trade per selected UTC day.
No pyramiding.
No scaling.

Funding-boundary exclusion:
exclude if [entry, exit] contains 00:00, 08:00 or 16:00 UTC.

## Frozen costs

Primary:
- MEXC Futures API taker fee 8 bps/side
- slippage 2 bps/side
- approx 20 bps round trip

Stress:
- same fee
- slippage 5 bps/side
- approx 26 bps round trip

No maker fills, rebates, VIP discounts or leverage benefit.

## Frozen Development gate

MARGINFI_ORCA_DAILYMAX_REBOUND_DEVELOPMENT_SURVIVES only if ALL:
1. analyzable n >= 25
2. distinct UTC entry days >= 25
3. nominal net mean > 0
4. nominal net median > 0
5. nominal net PF > 1.10
6. F1 n >= 15
7. F2 n >= 8
8. F1 nominal net mean > 0
9. F2 nominal net mean > 0
10. UTC-day block-bootstrap 95% CI lower > 0

Bootstrap:
- 20,000 replicates
- UTC entry-day blocks
- seed = 26100104

Otherwise:
MARGINFI_ORCA_DAILYMAX_REBOUND_DEVELOPMENT_NO_EDGE

## Future boundary

If Development SURVIVES:
all already-opened 2024 periods are ineligible as OOS.
Any 2025 OOS requires separate explicit operator authorization plus source authority.

## Forbidden rescue

After Jul-Sep outcomes open:
- no alternative daily ranking
- no top-2/top-3 per day
- no percentile/amount filters
- no LONG->SHORT flip
- no hold alternatives
- no day/time filters
- no cost changes
- no 2025 rescue without authorization

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
