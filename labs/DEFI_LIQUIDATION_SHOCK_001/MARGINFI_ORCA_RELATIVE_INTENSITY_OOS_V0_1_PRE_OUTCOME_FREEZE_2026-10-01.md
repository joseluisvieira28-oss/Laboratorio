# DLS — MARGINFI ORCA ROLLING RELATIVE-INTENSITY REBOUND OOS V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-relative-intensity-oos-v01
Status: FROZEN BEFORE OCT-DEC 2024 OHLC / RETURNS / PNL

Family:
DLS-MARGINFI-ORCA-RELATIVE-INTENSITY-OOS-001

## Motivation

The absolute-threshold OOS family closed PRE-OUTCOME because the flow-turnover feature distribution
shifted by orders of magnitude across Oct-Nov-Dec.

No Oct-Dec OHLC, return or PnL has been opened.

This family asks whether the Jul-Sep discovery relationship is portable when intensity is normalized
causally against recent feature history rather than a fixed absolute threshold.

This is a new family, not a rescue inside the prior family.

## Discovery authority

Canonical discovery:
- run 36814416648
- artifact ID 11140333264
- digest sha256:df7e37d1b2ea23052589802cda1d0b0dc37921bae3a1c23fe6dd3bd2fd614162
- classification MARGINFI_ORCA_FLOW_RESPONSE_DISCOVERY_PASS
- discovered sign = POSITIVE_REBOUND
- overall Spearman rho = +0.2806386056764949
- rho day-block bootstrap 95% CI = [+0.10959738083216897, +0.36433335124610083]

Direction and response horizon are frozen from that discovery:
- side LONG
- hold 1 minute

## Source authority

Canonical Oct-Dec Orca source:
- run 36814861360
- artifact ID 11140129257
- digest sha256:8d8b1b9fdf84dcc234e46012a39cc5126fa5b3068e739daf1f5d7e83ee42a4d7
- classification MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS
- canonical SOL population 2,688
- Orca presence 2,263
- source complete 2,263 / 2,263
- direction proven 2,263
- exact input amount proven 2,263
- ambiguity 0
- contradictions 0

## Feature authorities

Historical warmup feature artifact:
Jul-Sep pre-outcome feature-only run 36781289721
artifact ID 11127324942
digest sha256:8dfa5ef296ea65b4e51b46136cd6387b5d0586748ee081737d1ded101c182c87

It contains 192 source cascades and intentionally read:
- source identity
- exact sold SOL amount
- prior-five-minute Binance SOLUSDT base volume

It did NOT read OHLC, returns or PnL.

Current OOS feature artifact:
Oct-Dec pre-outcome run 36815199005
artifact ID 11140992589
digest sha256:b452730607f3db4c7f983ce748c74be1ee7f7a51301a1f3876e7d62698cac470

It contains 77 Oct-Dec cascades and also read feature data only.
No Oct-Dec OHLC, returns or PnL were read.

## Frozen base feature

Exactly unchanged:

flow_turnover_intensity =
cascade_sold_sol / prior-five-complete-minute Binance USDT-M SOLUSDT base-asset volume

Cascade linkage:
5 minutes.

Decision time:
A = first full UTC minute strictly after final cascade event.

## Frozen causal normalization

Maintain an ordered history of feature-valid Orca cascades by:
decision_time, cascade_id

For each Oct-Dec candidate cascade i:

1. Take exactly the 30 immediately preceding feature-valid cascades with decision_time < A_i.
2. These may include Jul-Sep warmup cascades and earlier Oct-Dec cascades.
3. If fewer than 30 prior cascades exist, the candidate is WARMUP_EXCLUDED.
4. Sort the 30 prior flow_turnover_intensity values ascending.
5. Rolling threshold = nearest-rank 75th percentile:
   rank = ceil(0.75 * 30) = 23
   threshold = sorted_prior[22]
6. Signal iff current flow_turnover_intensity >= rolling threshold.
7. Only after adjudicating the current candidate is its feature appended to future history.

No current/future outcome enters the threshold.
No current feature enters its own reference window.
No calendar-month future distribution is used.

## Funding firewall

After feature selection, exclude a signal if [A, A+1m] contains:
00:00 UTC, 08:00 UTC or 16:00 UTC.

## Mandatory pre-outcome sample gate

Before any Oct-Dec OHLC/returns/PnL:

READY only if ALL:
- selected post-funding signal count >= 25
- selected distinct UTC decision days >= 8
- F1 Oct-Nov selected >= 15
- F2 December selected >= 8

If any fail:
MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_INSUFFICIENT_SAMPLE

and the family closes without reading Oct-Dec OHLC/returns/PnL.

## Frozen executable rule

Only after READY:

side = LONG SOLUSDT
entry = OPEN(A)
exit = OPEN(A + 1 minute)

No pyramiding.
No scaling.
Only one trade per selected cascade.

## Frozen execution costs

Primary:
- MEXC Futures API taker fee = 8 bps per side
- slippage = 2 bps per side
- approximate round trip = 20 bps

Stress descriptive only:
- same fee
- slippage = 5 bps per side
- approximate round trip = 26 bps

Primary classification uses nominal only.

No maker fills, rebates, VIP discount or leverage benefit.

## OOS folds

F1:
2024-10-01 through 2024-11-30

F2:
2024-12-01 through 2024-12-31

## Frozen OOS gate

MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_SURVIVES only if ALL:

1. analyzable trade count >= 25
2. distinct UTC entry days >= 8
3. nominal net mean > 0
4. nominal net median > 0
5. nominal net profit factor > 1.10
6. F1 trade count >= 15
7. F2 trade count >= 8
8. F1 nominal net mean > 0
9. F2 nominal net mean > 0
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean > 0

Bootstrap:
- 20,000 replicates
- complete UTC entry-day blocks
- seed = 26100104

Otherwise:
MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_NO_EDGE

Integrity failure:
MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_SOURCE_BLOCKED

## Consequence of SURVIVES

SURVIVES would be an OOS executable edge under the frozen cost model.

It would still NOT authorize live trading.
2025/2026 remain protected pending separate governance.

## Forbidden rescue

After Oct-Dec outcomes open, V0.1 may NOT:
- change lookback 30
- change rolling percentile 75%
- include current feature in its own threshold
- use future-month feature distribution
- change LONG side
- change 1-minute hold
- change cascade linkage
- change turnover denominator
- add amount/event-count/liability/hop/time filters
- change costs
- delete December
- change folds
- open 2025 as rescue after failure

## Firewall

oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
