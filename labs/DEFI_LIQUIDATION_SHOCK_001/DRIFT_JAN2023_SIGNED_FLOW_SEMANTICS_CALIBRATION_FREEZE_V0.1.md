# DLS — DRIFT JAN-2023 SIGNED-FLOW SEMANTICS CALIBRATION FREEZE V0.1

Date: 2026-09-29
Status: FROZEN BEFORE SIGNED DIRECTION DECODE
Branch: dls-signed-flow-authority-v01

## Scope

Source-only Tier-B protocol-native position-delta calibration for Drift `liquidate_perp`.

No prices, returns, future market behavior, 2025 outcomes, or 2026 outcomes may be accessed.

Population source is fixed to the already-open canonical partition:
- run: 36264543005
- artifact: dls-field-enrichment-drift-drift-202301
- artifact ID: 10915721179
- artifact digest: sha256:47c9f1af96c29c2c7ea80f2a167d27c932932f956ae8b650a5388cb9b14730c8
- interval: 2023-01-01T00:00:00Z <= timestamp < 2023-02-01T00:00:00Z
- canonical class: liquidate_perp only

Use exactly the same three deterministic references already frozen by
`DRIFT_LIQUIDATION_EVENT_LOG_ROUTE_CALIBRATION_FREEZE_V0.1.md`:
ascending SHA256(signature || "|" || JSON-canonical instructionAddress), first 3.

## Historical protocol source authority

The historical Drift protocol repository is GitHub repository ID 497045217.
The legacy API path `drift-labs/protocol-v2` redirects to the same repository ID now exposed as
`velocity-exchange/protocol-v2`.

Relevant historical anchors:
- 099d7ac15260a2068738af36871bd384c93cade6 — 2023-01-01
- 9a1a83029e995807efe9e15b8a77f59d100fd33b — 2023-01-29

For the January-2023 interval, the following relevant semantics were checked across all commits touching their files:
- `controller/liquidation.rs`: the liquidated user's `user_position_delta` is built from
  `get_direction_to_close()`, and the emitted `LiquidatePerpRecord.base_asset_amount`
  is that signed delta;
- `math/orders.rs::get_position_delta_for_fill`: Long => positive base delta,
  Short => negative base delta;
- `state/user.rs`: positive/non-negative existing base => Long and closes Short;
  negative existing base => Short and closes Long;
- `state/events.rs`: January `LiquidationRecord` / `LiquidatePerpRecord` layout includes
  signed `base_asset_amount: i64`.

January commits touching `math/orders.rs` (321ffa5124..., cb07de38db...) preserve the exact
`get_position_delta_for_fill` section.
The January commit touching `state/user.rs` (fa59098827...) preserves the exact
`get_direction` / `get_direction_to_close` section.
The relevant liquidation, delta, direction, and event-record sections are identical between
the 2023-01-01 and 2023-01-29 anchors.

## Frozen directional semantics

For a successfully decoded and exactly bound `LiquidationRecord` with:
- liquidation_type = LiquidatePerp;
- event user = canonical liquidated_user account;
- event liquidator = canonical liquidator account;
- event liquidate_perp.market_index = canonical perp_market_index;
- event source transaction = exact canonical signature;
- event instructionAddress = exact canonical instructionAddress when supplied by transport;

classification is:

- `base_asset_amount < 0` => `SIGNED_SELL_PRESSURE_PROVEN`
- `base_asset_amount > 0` => `SIGNED_BUY_PRESSURE_PROVEN`
- `base_asset_amount == 0` => `DIRECTION_AMBIGUOUS`

Rationale is exclusively protocol semantics:
negative base delta is a Short execution; positive base delta is a Long execution.
No subsequent price movement is consulted.

## Event decode

Use the January-2023 Borsh layout frozen above.

Anchor event discriminator:
first 8 bytes of SHA256("event:LiquidationRecord").

Only Drift-program data/log items in the exact canonical transaction may be considered.

Transport decoding may accept:
1. raw base64 event payload in the log message; or
2. the same base64 payload preceded only by the literal transport prefix `Program data: `.

After base64 decode, the discriminator must match exactly.

Decode only the historical January layout. Do not use a later SDK schema to reinterpret bytes.

## Exact binding / contradiction rules

A reference is `SOURCE_EVIDENCE_INCOMPLETE` if:
- exact transaction is not recovered;
- no decodable LiquidationRecord exists;
- required identity fields cannot be matched;
- instructionAddress is present and conflicts;
- market index conflicts;
- user or liquidator conflicts.

A reference is a contradiction if:
- two decoded records both satisfy the exact identity binding but imply opposite non-zero directions; or
- decoded event semantics conflict with the canonical instruction identity.

Multiple records that do not bind exactly are not used.

## Calibration PASS

`DRIFT_SIGNED_SEMANTICS_3_OF_3_PASS` only if:
- all 3 exact references are recovered;
- all 3 have exactly one direction-bearing or zero-delta bound LiquidationRecord;
- source evidence incomplete count = 0;
- contradictions = 0;
- at least one of the three has non-zero signed base_asset_amount.

PASS authorizes a separately frozen January-2023 population source-only extraction.
It does not itself satisfy the family >=95% / >=90% authorization rule.

Otherwise:
`DRIFT_SIGNED_SEMANTICS_CALIBRATION_BLOCKED`.

## Firewall

prices=false
returns=false
pnl=false
market_2025_opened=false
market_2026_opened=false
post_outcome_market_inference=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
