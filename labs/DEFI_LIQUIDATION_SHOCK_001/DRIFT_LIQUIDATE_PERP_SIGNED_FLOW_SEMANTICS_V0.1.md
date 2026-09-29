# DEFI-LIQUIDATION-SHOCK-001 — DRIFT LIQUIDATE-PERP SIGNED-FLOW SEMANTICS V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-ONLY SEMANTIC ADJUDICATION
Parent: SIGNED_FLOW_SOURCE_AUTHORITY_FREEZE_V0.1.md

## Source evidence

Drift controller semantics establish two distinct mechanisms:

1. liquidate_perp:
- user delta uses get_direction_to_close();
- liquidator delta uses the user's existing direction;
- the user and liquidator receive opposite PositionDelta values;
- the emitted OrderActionRecord is a synthetic liquidation Fill between:
  taker = liquidated user;
  maker = liquidator;
- the liquidator takes over the user's perp exposure.

2. liquidate_perp_with_fill:
- places a liquidation order for the user;
- calls fill_perp_order(... FillMode::Liquidation ...);
- therefore may interact with AMM / external makers and must be treated separately.

## Calibrated historical records

Three deterministic historical LiquidatePerp transactions were inspected.

- one produced no realized transfer: max_base_asset_amount_allowed_to_be_transferred == 0.
- two produced LiquidationRecord + OrderActionRecord.

For both realized examples:
- LiquidationRecord discriminator matched event:LiquidationRecord;
- liquidation type = LiquidatePerp;
- base_asset_amount was positive;
- OrderActionRecord action = Fill;
- OrderActionExplanation = Liquidation;
- taker pubkey exactly matched LiquidationRecord.user;
- maker was the liquidator;
- taker direction = Long;
- maker direction = Short;
- fill_record_id matched the LiquidationRecord fill_record_id.

These are consistent with the direct user-to-liquidator position-transfer route.

## Direction labels

For direct liquidate_perp transfers:

SIGNED_POSITION_TRANSFER_PROVEN = true.

Market-pressure label:
DIRECTION_AMBIGUOUS.

Reason:
the user's closing delta is exactly offset by the liquidator taking the original exposure. The synthetic Fill record does not prove net external AMM/orderbook buy or sell pressure.

No later market return may be used to relabel it.

## Potential external-fill subfamily

liquidate_perp_with_fill remains a separate candidate source family.

It may receive SIGNED_BUY_PRESSURE_PROVEN / SIGNED_SELL_PRESSURE_PROVEN only if source evidence proves:
- the historical instruction route is liquidate_perp_with_fill or equivalent source-authoritative variant;
- the realized fill is against AMM or a maker other than the designated liquidation position-taker;
- fill direction is decoded from source event semantics;
- source reconciliation contradictions = 0.

## Firewall

prices=false
returns=false
market_2025_opened=false
market_2026_opened=false
post_outcome_direction_labeling=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
