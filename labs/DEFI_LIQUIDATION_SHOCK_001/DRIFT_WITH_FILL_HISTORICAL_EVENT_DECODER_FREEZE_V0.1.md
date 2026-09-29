# DLS — DRIFT WITH-FILL HISTORICAL EVENT DECODER FREEZE V0.1

Date: 2026-09-29
Status: FROZEN BEFORE FIRST WITH-FILL TRANSACTION DIRECTION DECODE
Branch: dls-signed-flow-authority-v01

Authority:
- DRIFT_WITH_FILL_SIGNED_MARKET_FLOW_SEMANTICS_FREEZE_V0.1.md
- DRIFT_WITH_FILL_TEMPORAL_SOURCE_AUTHORITY_RECEIPT_V0.1.md

## Event transport

Only Drift-program log/data rows from the exact canonical transaction may be decoded.

Accepted source payload:
- raw base64 message; or
- base64 message preceded only by literal prefix: Program data:

After base64 decode, the first 8 bytes must equal the Anchor event discriminator:

SHA256("event:<EventName>")[0:8]

No other heuristic event identification is authorized.

## Frozen enum ordinals

Historical source-authorized across the full public-source window:

LiquidationType:
- LiquidatePerp = 0

OrderAction:
- Fill = 2

OrderActionExplanation:
- Liquidation = 5

MarketType:
- Spot = 0
- Perp = 1

PositionDirection:
- Long = 0
- Short = 1

Any unrecognized required enum value => SOURCE_EVIDENCE_INCOMPLETE.

## LiquidationRecord decode

Decode the historical Borsh layout beginning immediately after the event discriminator:

- ts: i64
- liquidation_type: u8 enum
- user: Pubkey[32]
- liquidator: Pubkey[32]
- margin_requirement: u128
- total_collateral: i128
- margin_freed: u64
- liquidation_id: u16
- bankrupt: bool/u8
- canceled_order_ids: Vec<u32>

Then decode LiquidatePerpRecord:
- market_index: u16
- oracle_price: i64
- base_asset_amount: i64
- quote_asset_amount: i64
- lp_shares: u64
- fill_record_id: u64
- user_order_id: u32
- liquidator_order_id: u32
- liquidator_fee: u64
- if_fee: u64

Trailing fields for the other liquidation record variants need not be interpreted after the complete
LiquidatePerpRecord has been decoded, because required binding fields are already source-complete.

## OrderActionRecord decode

Decode the historical Borsh layout:

- ts: i64
- action: u8 enum
- action_explanation: u8 enum
- market_index: u16
- market_type: u8 enum

Then, in exact historical order:
- filler: Option<Pubkey>
- filler_reward: Option<u64>
- fill_record_id: Option<u64>
- base_asset_amount_filled: Option<u64>
- quote_asset_amount_filled: Option<u64>
- taker_fee: Option<u64>
- maker_fee: Option<i64>
- referrer_reward: Option<u32>
- quote_asset_amount_surplus: Option<i64>
- spot_fulfillment_method_fee: Option<u64>
- taker: Option<Pubkey>
- taker_order_id: Option<u32>
- taker_order_direction: Option<PositionDirection>
- taker_order_base_asset_amount: Option<u64>
- taker_order_cumulative_base_asset_amount_filled: Option<u64>
- taker_order_cumulative_quote_asset_amount_filled: Option<u64>
- maker: Option<Pubkey>
- maker_order_id: Option<u32>
- maker_order_direction: Option<PositionDirection>
- maker_order_base_asset_amount: Option<u64>
- maker_order_cumulative_base_asset_amount_filled: Option<u64>
- maker_order_cumulative_quote_asset_amount_filled: Option<u64>
- oracle_price: i64

Borsh Option encoding is frozen as:
- 0 => None
- 1 => decode contained value
- other tag => SOURCE_EVIDENCE_INCOMPLETE

## Exact with-fill binding

For one canonical with-fill instruction:

1. recover exact successful canonical signature + instructionAddress;
2. decode exactly one bound LiquidationRecord satisfying:
   - type LiquidatePerp;
   - user equals instruction user;
   - liquidator equals instruction liquidator/filler;
   - market_index equals instruction market index;
3. select all same-transaction OrderActionRecords satisfying:
   - action = Fill;
   - explanation = Liquidation;
   - market_type = Perp;
   - market_index equals bound liquidation market;
   - taker equals bound LiquidationRecord.user;
   - taker_order_id equals bound LiquidatePerpRecord.user_order_id;
   - base_asset_amount_filled exists and > 0;
4. sum(base_asset_amount_filled) must equal abs(LiquidatePerpRecord.base_asset_amount);
5. all selected fills must have one identical non-null taker_order_direction.

No direction may be inferred from the LiquidationRecord base-amount sign.

## Frozen direction and counterparty adjudication

- taker_order_direction Long => buy pressure candidate;
- taker_order_direction Short => sell pressure candidate.

Final PROVEN label requires the already frozen external-market counterparty rule:
- maker=None is external AMM/non-maker market liquidity; or
- maker exists and maker != LiquidationRecord.liquidator.

If any selected filled amount has maker == LiquidationRecord.liquidator:
DIRECTION_AMBIGUOUS.

Any incomplete reconciliation:
SOURCE_EVIDENCE_INCOMPLETE.

Any exact identity/sign contradiction:
CONTRADICTION.

## Calibration population

First decode only the four already source-censused events from:
DRIFT_WITH_FILL_CENSUS_wf-202407tail_V0.1.ndjson

No later partition's transaction direction may be opened until this four-event decoder calibration has been adjudicated.

Calibration PASS requires:
- 4/4 exact canonical transactions recovered;
- 4/4 bound realized LiquidationRecord;
- 4/4 full fill reconciliation;
- 0 decode/identity contradictions.

Direction mix is NOT a calibration PASS criterion.

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
post_decode_schema_change=false
