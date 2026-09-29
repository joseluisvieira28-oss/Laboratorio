# DLS — DRIFT WITH-FILL TEMPORAL SOURCE AUTHORITY RECEIPT V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Classification: DRIFT_WITH_FILL_TEMPORAL_SOURCE_AUTHORITY_PASS

## Scope

Source-only audit for the already frozen public-source window:

2024-07-30T17:21:13Z <= source timestamp < 2025-01-01T00:00:00Z

No transaction direction outcome, price, return, PnL, 2025 market outcome, or 2026 market outcome was used.

Parent authorities:
- DRIFT_WITH_FILL_PUBLIC_SOURCE_WINDOW_ADDENDUM_V0.1.md
- DRIFT_WITH_FILL_SIGNED_MARKET_FLOW_SEMANTICS_FREEZE_V0.1.md

Canonical historical repository:
- GitHub repository ID 497045217
- current path velocity-exchange/protocol-v2

Introduction anchor:
- a259778564afcf563b21399359eb2781753db20a
- 2024-07-30T17:21:13Z
- program: add liquidation via fill (#1106)

## Audit A — event serialization

File:
programs/drift/src/state/events.rs

States checked:
- a259778564afcf563b21399359eb2781753db20a
- bf1d2be9ec76cbd5e6a4d64569e769fe45a08e49
- fc708459164ae88ddce0c5eaa80257a233ec7f60
- 8271524a3966bec14ee1b048c97e70a8a0d9578f
- 44dd77e6d17a4013e83340c43e169c14a0889dbf

Across every source state that changed this file in the frozen window:
- LiquidationRecord / LiquidatePerpRecord critical serialization section: identical;
- OrderActionRecord serialization section: identical;
- OrderAction / OrderActionExplanation enum section: identical.

Distinct critical event layouts:
1

## Audit B — MarketType serialization

File:
programs/drift/src/state/user.rs

Every revision of this file in the frozen window was inspected, including the introduction anchor and
all changes through 2024-12-05.

MarketType remained exactly:

Spot
Perp

Distinct MarketType layouts:
1

Therefore historical Borsh ordinal:
- Spot = 0
- Perp = 1

## Audit C — PositionDirection serialization

File:
programs/drift/src/controller/position.rs

Relevant source states:
- a259778564afcf563b21399359eb2781753db20a
- 0d5d30044b8870248b90941374d8a99291cc5c46

PositionDirection remained exactly:

Long
Short

and opposite() remained:
- Long -> Short
- Short -> Long

Distinct PositionDirection layouts:
1

Historical Borsh ordinals:
- Long = 0
- Short = 1

## Audit D — liquidation order construction

File:
programs/drift/src/math/liquidation.rs

Every revision in the frozen window:
- a259778564afcf563b21399359eb2781753db20a
- 6bfadc83c46c70fae94375ada1dcd40583d12ce6
- 8ea8c73526170d49671190e0b50a21672a2d5504

The full get_liquidation_order_params function remained byte-for-byte identical across these states.

Invariant semantics:
- direction = existing_direction.opposite();
- market_type = Perp;
- reduce_only = true.

PASS.

## Audit E — liquidate_perp_with_fill control flow

File:
programs/drift/src/controller/liquidation.rs

Fourteen source states affecting this file were inspected from introduction through 2024-12-23.

Every state preserved all required invariants:
- liquidate_perp_with_fill exists;
- existing direction is read from the user's perp position;
- get_liquidation_order_params is used;
- the liquidation order is placed for the liquidated user;
- fill_perp_order is called with FillMode::Liquidation;
- zero filled base amount fails;
- a LiquidationRecord is emitted for a realized fill;
- the record binds user_order_id and fill_record_id.

PASS: 14 / 14 source states.

## Audit F — realized OrderActionRecord semantics

File:
programs/drift/src/controller/orders.rs

Nineteen source states affecting this file were inspected from introduction through 2024-12-05.

Every state preserved:
- two liquidation-specific OrderActionExplanation::Liquidation emission paths;
- realized records use OrderAction::Fill;
- AMM/non-post-only route records the liquidation user as taker and maker=None;
- matched route records the exact taker key/order and exact maker key/order;
- matched liquidation fills retain OrderActionExplanation::Liquidation;
- the maker in a matched record is the actual maker account, not merely the filler/executor.

PASS: 19 / 19 source states.

## Adjudication

All serialization and semantic prerequisites required by
DRIFT_WITH_FILL_SIGNED_MARKET_FLOW_SEMANTICS_FREEZE_V0.1.md
are temporally source-authorized across the full frozen public-source window.

Classification:

DRIFT_WITH_FILL_TEMPORAL_SOURCE_AUTHORITY_PASS

This authorizes a historical source-only decoder frozen to the single admitted layout.

It does NOT authorize:
- market-return testing;
- 2025/2026 market outcomes;
- trading;
- reinterpretation of counterparty rules.

## Firewall

prices=false
returns=false
pnl=false
market_2025_opened=false
market_2026_opened=false
transaction_direction_outcomes_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_schema_change=false
