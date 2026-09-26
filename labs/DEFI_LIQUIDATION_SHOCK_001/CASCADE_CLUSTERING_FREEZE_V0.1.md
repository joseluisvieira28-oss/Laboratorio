# DEFI-LIQUIDATION-SHOCK-001 — CASCADE CLUSTERING FREEZE V0.1

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Convert highly dependent realized liquidation instructions into prospectively defined cascade units before market outcomes are measured.

## Primary analysis unit

Primary key:
`protocol + frozen instruction_class + primary_source_market_identity`

The primary source market identity must come only from GLOBAL_FIELD_COVERAGE_FINAL_PASS metadata.

No market identity may be chosen from future returns.

## Primary-market identity rules

### Lending families
Primary identity is the collateral-underlying asset being seized/withdrawn by the realized liquidation.

Debt asset remains attached as a secondary source field.

### Drift
Primary identity is:
- liquidate_perp: perp_market_index
- liquidate_spot: ordered tuple (asset_spot_market_index, liability_spot_market_index)
- liquidate_borrow_for_perp_pnl: ordered tuple (perp_market_index, spot_market_index)
- liquidate_perp_pnl_for_deposit: ordered tuple (perp_market_index, spot_market_index)

No price direction is implied by this identity.

## Quiet-period cascade rule

Within each primary key:
1. sort realized successful instructions by canonical source ordering;
2. start a cluster at the first event;
3. append the next event if its timestamp is <= 60 seconds after the immediately previous event timestamp;
4. close the cluster when 60 full seconds pass without another event in the same primary key.

Primary cascade T0:
`last_realized_event_timestamp + 60 seconds`

This makes completed cluster membership knowable before any future outcome window begins.

## Same-transaction events

Multiple frozen liquidation instructions in one transaction remain distinct source events but enter the same cluster when they share the same primary key.

They contribute separately to event_count.

## Source-only severity

Primary severity available before amount authority:
- event_count in cluster;
- distinct transaction signature count;
- cluster duration seconds;
- protocol/class identity.

No requested/max instruction argument is treated as realized flow.

## Amount-based severity

Amount/notional severity is DISABLED until a separate realized-transfer authority proves:
- realized debt transfer;
- realized collateral transfer;
- historical units;
- event-time notional without look-ahead.

If that authority never passes, the experiment proceeds without amount-based severity.

## Cross-protocol cascades

Cross-protocol asset cascades are SECONDARY only.

They may merge primary clusters sharing an independently source-mapped underlying asset when their completed-cluster intervals overlap or are separated by <=60 seconds.

They cannot replace the primary protocol/class cluster family after outcomes.

## Sensitivity windows

Pre-frozen source-only sensitivity windows:
- 15 seconds
- 300 seconds

Primary remains 60 seconds.

All three clustering windows, if tested economically, belong to the same multiplicity family.

## Overlap with future return windows

The final market-outcome gate must prevent silent pseudo-replication when distinct primary clusters' future windows overlap.

The exact inference treatment is separately frozen before outcomes.

## Firewall

prices=false
returns=false
pnl=false
directional_outcomes=false
economic_outcomes=false
requested_amount_values=false
post_outcome_tuning=false
protected_2025_2026_market_outcomes=false
live_trading=false
merge_main=false
