# DLS — MARGINFI SOL EXHAUSTION — BINANCE FEE-FLOOR VALIDATION V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-binance-bbo-execution-v01
Status: FROZEN BEFORE OCT-DEC 2024 MARKET OUTCOMES

Family ID:
DLS-MARGINFI-SOL-EXHAUSTION-BINANCE-FEE-FLOOR-001

## Scientific status inherited

Parent signal family:
DLS-MARGINFI-SOL-FLOW-EXHAUSTION-REBOUND-001

Parent Jul-Sep 2024 Development:
MARGINFI_SOL_EXHAUSTION_REBOUND_DEVELOPMENT_NO_EDGE under its frozen MEXC execution model.

Parent gross observation:
- 33 trades
- mean gross +12.4353 bps/trade
- median gross +3.6214 bps
- gross PF 3.3801

This parent result MUST NOT be reclassified by changing costs after outcome observation.

## New question

Does the unchanged parent signal survive the current standard Binance USD-M Futures taker FEE FLOOR
on a fresh untouched market period, before any spread/slippage allowance?

This is an execution-feasibility screening family, NOT a claim of executable net edge.

A PASS means only that the signal clears the explicit fee floor strongly enough to justify a later
execution-shadow / BBO phase.

A FAIL closes this venue route for the frozen signal under V0.1.

## Venue fee authority

Venue:
Binance USD-M Futures, SOLUSDT.

Current regular-user taker fee authority as checked 2026-10-01:
0.0500% = 5 bps per taker fill.

Frozen two-fill fee floor:
5 bps entry + 5 bps exit = approximately 10 bps round trip.

No VIP discount, BNB discount, maker rebate, referral reduction or promotional fee is assumed.

This family intentionally sets modeled slippage to ZERO because the question is a necessary-condition
fee-floor screen. Zero slippage MUST NOT be interpreted as an executable-cost estimate.

## Immutable signal

No signal parameter may change from the parent:

- protocol Marginfi
- liquidation instruction lending_account_liquidate
- asset wrapped/native SOL only
- source-complete post-liquidation Jupiter route
- DIRECTION_PROVEN
- COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN
- SIGNED_SELL_PRESSURE_PROVEN
- first SwapEvent inputMint = SOL
- first SwapEvent inputAmount > 0
- source events linked into cascades using exactly 5 minutes
- decision time A = first full UTC minute strictly after cascade end
- prior-turnover feature = cascade_sold_sol / Binance SOLUSDT prior 5 complete 1m base-volume
- immutable threshold Q90 = 1.0307255992127644e-05
- signal iff intensity >= Q90
- side LONG SOLUSDT
- entry OPEN minute A
- exit OPEN minute A+1m
- funding boundary exclusion unchanged

No liability filter.
No hop filter.
No event-count filter.
No source amount filter.
No time-of-day filter.
No new threshold.
No new hold horizon.

## Q90 authority

Feature-only calibration:
- run 36686002313
- artifact 11083738178
- digest sha256:6cacadfffce7225984258a634d0df0ac5685c0a7915bedc9e0a0e595fabc1327
- classification MARGINFI_SOL_FLOW_TURNOVER_CALIBRATION_PASS
- Q90 1.0307255992127644e-05
- calibration used no OHLC, returns or PnL.

## Fresh validation market period

Oct-Dec 2024:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

These market outcomes were unopened when this freeze was committed.

F1:
[2024-10-01T00:00:00Z, 2024-12-01T00:00:00Z)

F2:
[2024-12-01T00:00:00Z, 2025-01-01T00:00:00Z)

## Canonical Marginfi field-enrichment source partitions

October:
- artifact 10924878593
- digest sha256:a6635c5a7ca8b2d1d49670acb5482dda82db56459af068739c6acc535c82b6d7
- marginfi-202410
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched 1,432 / 1,432
- source-only SOL population observed before market outcomes: 64

November:
- artifact 10925847270
- digest sha256:43f749aeca0999f8e35262c73ca5ac8bbf7c0920f04db205d24e969de6a61fd7
- marginfi-202411
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched 10,141 / 10,141
- source-only SOL population observed before market outcomes: 275

December:
- artifact 10927608033
- digest sha256:0228f85921f9a30d6310b0fa3e5798f2695b9750c4add737e82a7611959892a4
- marginfi-202412
- FIELD_ENRICHMENT_PARTITION_PASS
- baseline/enriched 4,880 / 4,880
- source-only SOL population observed before market outcomes: 2,349

Bank registry:
- run 36312418451
- artifact 10929339072
- MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS

## Source gate before market open

Exact Jul-Sep validated multi-hop source semantics are reused unchanged.

Global source PASS requires:
- all three canonical partitions PASS
- every SOL-population identity adjudicated for Jupiter route membership
- population duplicates 0
- route duplicates 0
- route members > 0
- source-complete >= 95%
- direction rate among complete >= 90%
- direction ambiguous = 0
- contradictions = 0
- global source errors = 0

PASS:
MARGINFI_SOL_OCTDEC_SIGNED_FLOW_SOURCE_PASS

Otherwise:
MARGINFI_SOL_OCTDEC_SIGNED_FLOW_SOURCE_BLOCKED

Market outcomes may not be opened before source PASS.

## Fee-floor return model

Gross LONG return:
exit_open / entry_open - 1

Fee-only execution model:
- entry taker fee = 5 bps of entry fill notional
- exit taker fee = 5 bps of exit fill notional
- no slippage term
- no spread term

The executor must account for fees on each leg, not subtract a flat 10 bps shortcut.

This is explicitly a FEE FLOOR, not an executable realized model.

## Frozen fee-floor gate

Classification:
MARGINFI_SOL_BINANCE_FEE_FLOOR_SURVIVES

only if ALL:
1. analyzable trades >= 25
2. distinct UTC entry days >= 8
3. fee-floor net mean > 0
4. fee-floor net median > 0
5. fee-floor net PF > 1.10
6. F1 trades >= 10
7. F2 trades >= 10
8. F1 fee-floor net mean > 0
9. F2 fee-floor net mean > 0
10. UTC-day block-bootstrap 95% lower bound of fee-floor net mean > 0

Bootstrap:
- 20,000 replicates
- UTC day blocks
- seed 26100102

Otherwise:
MARGINFI_SOL_BINANCE_FEE_FLOOR_NO_EDGE

## Consequence of PASS

PASS is NOT executable-edge promotion.

It authorizes only a next-stage execution-friction investigation that must independently measure or
bound spread/slippage before any production or live-trading claim.

No live order is authorized.

## Consequence of FAIL

The Binance standard-taker fee-floor route is closed for this exact signal under V0.1.
No threshold/horizon/side/filter rescue is allowed using Oct-Dec outcomes.

## Forbidden rescue

After Oct-Dec outcomes open, V0.1 may NOT:
- change Q90
- change 5-minute cascade linkage
- change prior-volume denominator
- change LONG direction
- change 1-minute hold
- change entry/exit timestamps
- change Binance fee floor
- invoke VIP/BNB/maker discounts
- add source amount/event/hop/liability/time filters
- select months after seeing outcomes
- open 2025/2026 as a rescue period

## Firewall

oct_dec_2024_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
