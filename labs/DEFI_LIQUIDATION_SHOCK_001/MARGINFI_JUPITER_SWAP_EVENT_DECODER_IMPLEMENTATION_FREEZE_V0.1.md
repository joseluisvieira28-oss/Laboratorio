# DLS — MARGINFI JUPITER SWAP EVENT DECODER IMPLEMENTATION FREEZE V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE FIRST JAN-2024 SWAP EVENT DECODE

Parent:
- MARGINFI_JUPITER_REALIZED_SWAP_DIRECTION_CALIBRATION_FREEZE_V0.1.md
- MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_CLASS_FREEZE_V0.1.md
- MARGINFI_JUPITER_ROUTE_CLASS_TRANSPORT_SHARDING_ADDENDUM_V0.2.md

## Official Jupiter event authority

Pinned repository:
jup-ag/instruction-parser@e6f77951377847c579112e6a16d8c17c5c092485

Pinned files:
- src/idl/jupiter.ts
- src/lib/get-events.ts

The pinned IDL defines SwapEvent:
- amm: publicKey
- inputMint: publicKey
- inputAmount: u64
- outputMint: publicKey
- outputAmount: u64

The pinned get-events implementation:
1. inspects Jupiter V6 inner instructions;
2. decodes instruction data;
3. removes the first 8 bytes;
4. passes the remaining bytes to the Anchor event decoder.

## Frozen raw-data transport decode

For SQD instruction.data, the implementation may attempt only these transport encodings:
- hex with optional 0x prefix;
- base58;
- base64.

After transport decoding:
1. remove exactly the first 8 raw bytes;
2. require the next 8 bytes to equal SHA256("event:SwapEvent")[0:8];
3. decode the exact frozen SwapEvent Borsh field order.

A source instruction is accepted as SwapEvent only if exactly one decoded semantic tuple exists.

If zero interpretations match:
not a SwapEvent.

If multiple distinct semantic tuples match:
SOURCE_EVIDENCE_INCOMPLETE.

No parser rule may be added after observing direction labels.

## Frozen route ownership

Consider only committed successful Jupiter V6 instructions in the exact canonical transaction that sort
strictly after the canonical Marginfi liquidation instructionAddress.

A post-liquidation Jupiter route root is a Jupiter instructionAddress that is not a strict descendant of
another post-liquidation Jupiter instructionAddress.

A decoded SwapEvent belongs to a route root only if:
- its instructionAddress is a strict descendant of that route root.

Calibration direction requires:
- exactly one decoded SwapEvent in the exact transaction; and
- that SwapEvent has exactly one route-root owner.

Otherwise:
SOURCE_EVIDENCE_INCOMPLETE.

## Frozen bank registry

Canonical bank identity authority:
- run 36312418451
- artifact dls-marginfi-bank-unit-source-completion-v02
- artifact ID 10929339072
- digest sha256:e859ffdce4a628a90b270a96324c4a75c2e2739662d8f7a8b148483f76155a3d
- classification MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS
- registry bank count 58
- unmapped banks 0
- conflicts 0

No mint identity may be guessed from symbol or token name.

## Direction adjudication

Unchanged from parent freeze:

asset_bank mint = A
liab_bank mint = L
SwapEvent inputMint = I
SwapEvent outputMint = O

I=A and O=L:
- collateral => SIGNED_SELL_PRESSURE_PROVEN
- liability => SIGNED_BUY_PRESSURE_PROVEN

I=L and O=A:
- liability => SIGNED_SELL_PRESSURE_PROVEN
- collateral => SIGNED_BUY_PRESSURE_PROVEN

Otherwise:
DIRECTION_AMBIGUOUS

## Firewall

swap_direction_outcomes_opened=false
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
post_decode_rule_change=false
