# DLS — MARGINFI JUPITER REALIZED SWAP DIRECTION CALIBRATION FREEZE V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE ANY JAN-2024 JUPITER SWAP EVENT IS DECODED
Parent:
- SIGNED_FLOW_SOURCE_AUTHORITY_FREEZE_V0.1.md
- MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_CLASS_FREEZE_V0.1.md
- MARGINFI_JUPITER_ROUTE_CLASS_TRANSPORT_SHARDING_ADDENDUM_V0.2.md

## Purpose

Determine whether the already-frozen Marginfi + post-liquidation Jupiter class contains source-proven
realized external market flow with deterministic asset direction.

No market price, future return or PnL may be used.

## Conditional launch

This calibration may execute only if the independent Jan-2024 class census returns:

MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS

Otherwise:
MARGINFI_JUPITER_SWAP_DIRECTION_CALIBRATION_BLOCKED

## Jupiter source authority

Pinned official source:
jup-ag/instruction-parser@e6f77951377847c579112e6a16d8c17c5c092485

The pinned IDL defines SwapEvent fields exactly:
- amm: publicKey
- inputMint: publicKey
- inputAmount: u64
- outputMint: publicKey
- outputAmount: u64

The pinned parser decodes transaction events named SwapEvent and uses inputMint/outputMint as realized
swap legs.

Therefore a non-zero SwapEvent is source-authorized as realized token market exchange evidence.

## Marginfi bank identity authority

For every canonical member:
- asset_bank is the frozen Marginfi liquidation fixed account 1;
- liab_bank is fixed account 2.

Mint identity for both banks MUST come from the already-frozen source-only Marginfi bank unit registry
route. No symbol/name guess is permitted.

If either bank cannot be mapped uniquely to one mint:
SOURCE_EVIDENCE_INCOMPLETE.

## Frozen calibration population

If class membership PASS:
1. take every Jan-2024 class member;
2. compute SHA256(signature + "|" + canonical JSON instructionAddress);
3. sort ascending;
4. take the first min(64, member_count).

Selection uses only source identity.
No token amount, swap direction, price, return or market outcome participates.

## Exact transaction requirements

For each calibration member require:
- exact canonical signature;
- exact canonical Marginfi liquidation instructionAddress;
- successful parent transaction;
- at least one committed Jupiter V6 instruction strictly after the Marginfi liquidation;
- complete source-authoritative asset_bank and liab_bank mint identity.

## Frozen SwapEvent binding

Decode Jupiter V6 SwapEvent only from the exact canonical transaction.

To receive a deterministic signed-flow label, the transaction must contain exactly ONE source-decodable
Jupiter SwapEvent after applying the exact pinned Jupiter V6 event discriminator/layout.

Because SwapEvent itself does not encode the outer instructionAddress, V0.1 fails closed when:
- more than one Jupiter SwapEvent exists in the exact transaction;
- more than one post-liquidation Jupiter route could own the event;
- event-to-post-liquidation route ownership cannot be uniquely established from transaction execution order/log context.

Required realized fields:
- inputMint != outputMint
- inputAmount > 0
- outputAmount > 0

Any decode/layout/ownership ambiguity:
SOURCE_EVIDENCE_INCOMPLETE.

## Frozen direction labels

Let:
A = source-authoritative asset_bank mint
L = source-authoritative liab_bank mint
I = SwapEvent.inputMint
O = SwapEvent.outputMint

If I == A and O == L:
- asset mint => SIGNED_SELL_PRESSURE_PROVEN
- liability mint => SIGNED_BUY_PRESSURE_PROVEN
- route semantic = COLLATERAL_TO_LIABILITY_SWAP_PROVEN

If I == L and O == A:
- liability mint => SIGNED_SELL_PRESSURE_PROVEN
- asset mint => SIGNED_BUY_PRESSURE_PROVEN
- route semantic = LIABILITY_TO_COLLATERAL_SWAP_PROVEN

If {I,O} does not equal {A,L}:
DIRECTION_AMBIGUOUS

No direction may be inferred merely from Jupiter program presence.

## Amount authority

SwapEvent inputAmount/outputAmount are realized source-native amounts.

They may be recorded for reconciliation only.
No minimum amount threshold is authorized.
No USD conversion is authorized in this calibration.

## Calibration PASS

MARGINFI_JUPITER_SWAP_DIRECTION_CALIBRATION_PASS only if:
- every sampled member is recovered exactly;
- SOURCE_EVIDENCE_INCOMPLETE rate <= 5%;
- among source-complete members, deterministic direction rate >= 90%;
- contradictions = 0.

Direction mix itself is NOT a PASS criterion.

If evidence is valid but directional rate is below threshold:
MARGINFI_JUPITER_SWAP_DIRECTION_CALIBRATION_PARTIAL

If source/event/bank mapping cannot be completed defensibly:
MARGINFI_JUPITER_SWAP_DIRECTION_CALIBRATION_BLOCKED

PASS authorizes a separately frozen full Jan-2024 source-only direction census.
It does not authorize market-return testing.

## Firewall

prices=false
returns=false
pnl=false
usd_notional=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_direction_rule_change=false
