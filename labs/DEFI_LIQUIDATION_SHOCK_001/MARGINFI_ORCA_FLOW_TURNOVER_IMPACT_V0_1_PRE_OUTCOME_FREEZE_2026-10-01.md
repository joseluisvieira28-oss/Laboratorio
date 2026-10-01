# DLS — MARGINFI ORCA FLOW-TO-TURNOVER IMPACT V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-flow-turnover-v01
Status: FROZEN BEFORE OCT-DEC 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-FLOW-TURNOVER-IMPACT-001

## Scientific question

When source-proven Marginfi SOL collateral liquidation is realized through Orca Whirlpools and forced SOL
selling is exceptionally large relative to the immediately preceding SOLUSDT perpetual turnover, does SOL
show immediate 1-minute continuation large enough to survive realistic automated execution costs?

## Source authority

Jul-Sep Orca signed-flow authority:
- run 36780139559
- artifact ID 11127536853
- digest sha256:4cbe2bad99237aee32d1e21c5055b17258897df6c312639678e68f15c4ae8dcb
- classification MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS
- canonical Marginfi SOL population 8,857
- Orca presence 7,744
- direction proven 7,717
- exact input amount proven 7,717 / 7,717
- contradictions 0
- source complete 100%

Eligible event:
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- asset_mint = wrapped/native SOL
- exact_route_input_amount > 0

event_sold_sol = exact_route_input_amount / 1,000,000,000

## Frozen cascade construction

Sort by timestamp, signature, canonical instructionAddress.

A subsequent eligible event belongs to the same cascade iff its source timestamp is <= 5 minutes after
the immediately previous eligible event timestamp.

For each cascade:
- first_event_time
- last_event_time
- cascade_sold_sol = sum(event_sold_sol)
- source_event_count
- exact member identities

Decision minute:
A = first full UTC minute strictly after last_event_time.

No market outcome participates in cascade construction.

## Frozen turnover feature

Market-turnover proxy:
Binance public USDT-M SOLUSDT perpetual 1m base-asset volume.

pre5m_base_volume_sol =
sum of the five complete minutes immediately preceding A:
[A-5m, A)

flow_turnover_intensity =
cascade_sold_sol / pre5m_base_volume_sol

Only timestamp + base-volume column may be read during feature calibration.

No OHLC.
No return.
No PnL.
No post-entry volume.

## Feature-only calibration

Calibration period:
[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

Use all valid source-complete Orca cascades.

Threshold method:
nearest-rank 90th percentile.

rank = ceil(0.90 * N)
Q90 = sorted_intensity[rank - 1]

PASS requires:
- valid cascades >= 100
- distinct UTC cascade-end days >= 20
- checksum/integrity hard errors = 0
- missing required pre-entry volume minutes = 0
- Q90 > 0

Classification:
MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS
or
MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_BLOCKED

No alternate percentile may be inspected.
No threshold grid.
No market outcome may be read before numeric Q90 is frozen.

## Development source window

Oct-Dec 2024:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

Canonical Marginfi field-enrichment artifacts:
- October artifact ID 10924878593
  digest sha256:a6635c5a7ca8b2d1d49670acb5482dda82db56459af068739c6acc535c82b6d7
- November artifact ID 10925847270
  digest sha256:43f749aeca0999f8e35262c73ca5ac8bbf7c0920f04db205d24e969de6a61fd7
- December artifact ID 10927608033
  digest sha256:0228f85921f9a30d6310b0fa3e5798f2695b9750c4add737e82a7611959892a4

Development source census must:
- derive exact SOL collateral population from canonical field partitions;
- adjudicate post-liquidation Orca Whirlpools route under unchanged decoder semantics;
- require population duplicates = 0;
- route-member count > 0;
- source-complete rate >= 95%;
- deterministic direction among source-complete >= 90%;
- contradictions = 0.

PASS:
MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

PARTIAL:
valid source but source thresholds miss.

BLOCKED:
transport, identity, decoder, bank mapping, structural conflict or reconciliation failure.

No Oct-Dec market outcome may open before BOTH calibration PASS and source PASS.

## Frozen market hypothesis

For each Oct-Dec source cascade:
1. compute frozen flow_turnover_intensity using only [A-5m, A)
2. signal iff intensity >= frozen Jul-Sep Q90
3. side = SHORT SOLUSDT
4. entry = OPEN of minute A
5. exit = OPEN of A + 1 minute

No pyramiding.
If a selected cascade enters before an open trade exits, ignore later candidate.
No source-event-count threshold.
No liability filter.
No hop-count filter.
No time-of-day filter.

## Funding firewall

Exclude if [entry, exit] contains 00:00, 08:00 or 16:00 UTC.

## Market-data integrity

Authority:
Binance public USDT-M SOLUSDT perpetual 1m daily archives.

Required:
- published checksum SHA256 PASS
- unique monotonic minute timestamps
- required feature/entry/exit minutes present

Any hard market-data failure:
MARGINFI_ORCA_FLOW_TURNOVER_DEVELOPMENT_SOURCE_BLOCKED

## Frozen costs

Primary:
- MEXC Futures API taker fee 8 bps per side
- slippage 2 bps per side
- approx round trip 20 bps

Stress descriptive:
- same fee
- slippage 5 bps per side
- approx round trip 26 bps

No maker assumption.
No rebates.
No VIP discounts.
No leverage benefit.

## Development folds

F1:
[2024-10-01T00:00:00Z, 2024-12-01T00:00:00Z)

F2:
[2024-12-01T00:00:00Z, 2025-01-01T00:00:00Z)

## Frozen Development gate

MARGINFI_ORCA_FLOW_TURNOVER_DEVELOPMENT_SURVIVES only if ALL:

1. analyzable trade count >= 30
2. distinct UTC entry days >= 8
3. nominal net mean > 0
4. nominal net median > 0
5. nominal net PF > 1.10
6. F1 n >= 20
7. F2 n >= 8
8. F1 nominal net mean > 0
9. F2 nominal net mean > 0
10. UTC-day block-bootstrap 95% CI lower > 0

Bootstrap:
- 20,000 replicates
- UTC entry-day blocks
- seed = 26100101

Otherwise:
MARGINFI_ORCA_FLOW_TURNOVER_DEVELOPMENT_NO_EDGE

## Future boundary

Only if Development SURVIVES:
OOS candidate [2025-01-01, 2025-04-01)

2025 market outcomes remain CLOSED until source authority is separately completed under unchanged rules.

2026 remains protected.

## Forbidden rescue

After Oct-Dec outcomes open, V0.1 may NOT:
- change Q90
- inspect Q80/Q85/Q95
- change 5-minute turnover denominator
- change SHORT to LONG
- change 1-minute hold
- inspect 2m/3m/5m/15m alternatives
- add event-count/amount/hop/liability/time filters
- change costs
- use Jul-Sep market outcomes
- open 2025 if Development fails

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
