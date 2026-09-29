# MARGINFI JUPITER MULTI-HOP SWAP DIRECTION CALIBRATION FREEZE V0.2

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE V0.2 CALIBRATION SAMPLE IS DECODED

Parent source authority:
- MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS
- MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS
- official Jupiter V6 SwapEvent source semantics
- V0.1 terminal closeout preserved unchanged

## Scientific distinction

V0.2 does not modify or rescue the V0.1 exactly-one-SwapEvent rule.

V0.2 tests a separate source-semantic question:
can multiple source-decodable Jupiter SwapEvents under one post-liquidation Jupiter route root form a
single deterministic realized token path whose endpoints establish signed external market flow?

No market price, future return or PnL is used.

## Independent calibration population

Start from the immutable Jan-2024 membership population of 2,605 members.

Rank every member by:
SHA256(signature + "|" + canonical JSON instructionAddress)

V0.1 used ranks 1-64.

V0.2 uses exactly ranks 65-128.

No member from V0.1 may enter V0.2 calibration.
No direction/amount/outcome field participates in selection.

## Frozen decoder

Transport decoding and SwapEvent Borsh layout remain exactly as frozen in:
MARGINFI_JUPITER_SWAP_EVENT_DECODER_IMPLEMENTATION_FREEZE_V0.1.md

No new transport encoding or event layout is introduced.

## Frozen route ownership

Require exactly one post-liquidation Jupiter route root in the exact successful transaction.

Decode every source-valid SwapEvent that is a strict descendant of that route root.

Require at least one decoded SwapEvent.

Sort SwapEvents by canonical instructionAddress execution order.

## Frozen simple-path rule

Let events in execution order be E1...En.

Each event must satisfy:
- inputMint != outputMint
- inputAmount > 0
- outputAmount > 0

For n > 1 require for every adjacent pair:
Ei.outputMint == E(i+1).inputMint

Also require:
- no event inputMint/outputMint pair is duplicated;
- no mint appears as an endpoint in a way that creates a cycle;
- the ordered route therefore has exactly one start mint and one final mint.

The realized route endpoints are:
I = E1.inputMint
O = En.outputMint

Intermediate mints do not receive signed-flow labels.

If the events do not form this exact simple ordered chain:
SOURCE_EVIDENCE_INCOMPLETE.

## Direction rule

A = source-authoritative asset_bank mint
L = source-authoritative liab_bank mint

If I == A and O == L:
- asset mint => SIGNED_SELL_PRESSURE_PROVEN
- liability mint => SIGNED_BUY_PRESSURE_PROVEN
- route semantic = COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN

If I == L and O == A:
- liability mint => SIGNED_SELL_PRESSURE_PROVEN
- asset mint => SIGNED_BUY_PRESSURE_PROVEN
- route semantic = LIABILITY_TO_COLLATERAL_MULTI_HOP_PROVEN

Otherwise:
DIRECTION_AMBIGUOUS

No direction may be inferred from transaction composition alone.

## V0.2 calibration gate

PASS only if all:
- exactly 64 disjoint members are adjudicated;
- source evidence incomplete rate <= 5%;
- deterministic direction among non-incomplete members >= 90%;
- contradictions = 0.

PASS:
MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_PASS

Threshold miss with valid source:
MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_PARTIAL

Identity/layout/source failure:
MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_BLOCKED

Direction mix itself is not a PASS criterion.

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
post_decode_rule_change=false
