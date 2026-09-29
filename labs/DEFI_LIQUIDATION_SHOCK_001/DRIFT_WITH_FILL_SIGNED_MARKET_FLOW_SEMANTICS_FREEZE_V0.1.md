# DLS — DRIFT WITH-FILL SIGNED MARKET-FLOW SEMANTICS FREEZE V0.1

Date: 2026-09-29
Status: FROZEN BEFORE WITH-FILL TRANSACTION DIRECTION DECODE
Branch: dls-signed-flow-authority-v01
Parent: SIGNED_FLOW_SOURCE_AUTHORITY_FREEZE_V0.1.md
Source window: DRIFT_WITH_FILL_PUBLIC_SOURCE_WINDOW_ADDENDUM_V0.1.md

## Historical source authority

Canonical repository ID:
497045217

Public source anchor introducing liquidate_perp_with_fill:
a259778564afcf563b21399359eb2781753db20a
2024-07-30T17:21:13Z

The source proves:

1. get_liquidation_order_params:
- direction = existing_direction.opposite();
- order is Perp / Limit / reduce_only.

2. liquidate_perp_with_fill:
- places the liquidation order for the liquidated user;
- calls fill_perp_order(... FillMode::Liquidation ...);
- rejects zero fill;
- emits LiquidationRecord after the realized fill.

3. fill_perp_order:
- the liquidated user is the taker order owner;
- the supplied liquidator account is the filler/executor unless it independently appears as a maker;
- actual OrderActionRecord fills expose taker, maker, taker_order_id, taker_order_direction,
  base_asset_amount_filled and market identity.

4. PositionDirection semantics:
- Long is positive/buy base direction;
- Short is negative/sell base direction.

## Important sign rule

For liquidate_perp_with_fill, DO NOT use the sign of
LiquidationRecord.liquidate_perp.base_asset_amount
as the market-pressure sign.

The implementation constructs that record from existing_direction after the fill.
Market-flow direction is determined only from the bound realized OrderActionRecord taker direction.

Frozen mapping:
- taker_order_direction = Long => SIGNED_BUY_PRESSURE_PROVEN
- taker_order_direction = Short => SIGNED_SELL_PRESSURE_PROVEN

## Exact event binding

For each canonical successful with-fill instruction:

A realized with-fill event must have:
- exact canonical transaction signature;
- exact canonical instructionAddress;
- successful parent transaction;
- one exactly bound LiquidationRecord with type LiquidatePerp;
- event user = the liquidated user of the instruction;
- event liquidator = the instruction liquidator/filler account;
- event market_index = instruction market_index;
- non-zero realized fill.

Bind all OrderActionRecord items in the same exact transaction satisfying:
- action = Fill;
- action_explanation = Liquidation;
- market_type = Perp;
- market_index = the bound liquidation market;
- taker = bound LiquidationRecord.user;
- taker_order_id = LiquidationRecord.liquidate_perp.user_order_id;
- base_asset_amount_filled > 0.

The sum of bound base_asset_amount_filled must equal
abs(LiquidationRecord.liquidate_perp.base_asset_amount).

All bound fill records must agree on taker_order_direction.

## External-market counterparty rule

SIGNED_BUY_PRESSURE_PROVEN / SIGNED_SELL_PRESSURE_PROVEN requires that the entire reconciled filled amount
is against market liquidity under at least one of these source-proven forms:

A. AMM / non-maker fill:
- maker is None.

B. explicit maker fill:
- maker is present;
- maker != LiquidationRecord.liquidator.

If any portion of the reconciled fill has maker == LiquidationRecord.liquidator,
the event is DIRECTION_AMBIGUOUS under this V0.1 rule.

This preserves the earlier controlling semantic requirement that the experiment must not relabel
a designated liquidation position transfer as external market pressure.

## Event classifications

SIGNED_BUY_PRESSURE_PROVEN
- exact complete reconciliation;
- all bound fills Long;
- all reconciled filled amount satisfies the external-market counterparty rule.

SIGNED_SELL_PRESSURE_PROVEN
- exact complete reconciliation;
- all bound fills Short;
- all reconciled filled amount satisfies the external-market counterparty rule.

DIRECTION_AMBIGUOUS
- realized fill exists but counterparty rule is not fully external;
- bound fills disagree in direction;
- or source semantics are internally transfer-like despite successful fill.

SOURCE_EVIDENCE_INCOMPLETE
- exact transaction/event/fill binding cannot be completed;
- historical event layout is unresolved;
- realized amount cannot be reconciled;
- source transport is incomplete.

CONTRADICTION
- exact source records conflict on identity or imply incompatible signed semantics.

## Family rule

Over the frozen public-source-audited with-fill period:

SIGNED_FLOW_AUTHORIZED only if:
1. >=95% of realized with-fill events have non-incomplete source evidence;
2. >=90% of those complete events are SIGNED_BUY_PRESSURE_PROVEN or SIGNED_SELL_PRESSURE_PROVEN;
3. contradictions = 0;
4. direction follows only the frozen transaction/program semantics above.

Otherwise PARTIAL/BLOCKED under the parent authority.

## Required temporal-layout authority

Before full transaction population direction decode, enumerate the historical source layouts needed to decode:
- LiquidationRecord / LiquidatePerpRecord;
- OrderActionRecord;
- PositionDirection;
- OrderAction;
- OrderActionExplanation

for the public-source window.

Only source-admitted layouts may be used.
No decoder may be introduced after observing direction outcomes.

## Firewall

prices=false
returns=false
pnl=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_direction_rule_change=false
