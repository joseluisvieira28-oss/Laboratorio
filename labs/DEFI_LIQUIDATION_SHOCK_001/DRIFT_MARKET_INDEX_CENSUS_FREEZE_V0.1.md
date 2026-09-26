# DEFI-LIQUIDATION-SHOCK-001 — DRIFT MARKET INDEX CENSUS FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND / STAGED

## Launch prerequisite

Do not launch until the actual Drift population field-enrichment aggregate classifies:

`DRIFT_FIELD_ENRICHMENT_POPULATION_PASS`

The market-index census is derived only from the already frozen realized-event population and cannot
change event membership.

## Input

All accepted Drift enrichment partition receipts from run 36264543005.

Each enriched realized event already carries class-specific protocol-native market identity decoded
from the frozen instruction bytes.

## Index extraction

Collect exact unique indexes and event-role observation counts:

- liquidate_perp:
  - perp_market_index

- liquidate_spot:
  - asset_spot_market_index
  - liability_spot_market_index

- liquidate_borrow_for_perp_pnl:
  - perp_market_index
  - spot_market_index

- liquidate_perp_pnl_for_deposit:
  - perp_market_index
  - spot_market_index

No symbol, mint, oracle, price, notional or market outcome is queried here.

## Exact population check

The census must reconcile exact event counts to terminal Drift source authority:
- liquidate_perp = 1,953,488
- liquidate_spot = 619,719
- liquidate_perp_pnl_for_deposit = 79,343
- liquidate_borrow_for_perp_pnl = 3,370

Every realized event must contain the required market-index identity for its class.

## Terminal result

PASS:
`DRIFT_MARKET_INDEX_CENSUS_POPULATION_PASS`

Blocked:
`DRIFT_MARKET_INDEX_CENSUS_BLOCKED_FAIL_CLOSED`

PASS freezes the exact spot/perp index universe that the later market-unit registry is allowed to map.
No extra market may be added because it looks economically interesting.

## Later unit mapping

After PASS:
- every observed spot index must map to source-defensible SpotMarket mint + decimals;
- every observed perp index must map to source-defensible market identity;
- perp unit semantics are prospectively frozen from historical Drift source:
  - PERP_DECIMALS = 9
  - BASE_PRECISION = 1e9
  - QUOTE_PRECISION = 1e6

No symbol/name-only inference is accepted.

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
requested_max_amount_values=false
limit_price_values=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
