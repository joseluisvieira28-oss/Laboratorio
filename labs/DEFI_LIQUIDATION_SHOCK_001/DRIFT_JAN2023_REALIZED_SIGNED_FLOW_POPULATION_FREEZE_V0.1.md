# DLS — DRIFT JAN-2023 REALIZED SIGNED-FLOW POPULATION FREEZE V0.1

Date: 2026-09-29
Status: FROZEN BEFORE POPULATION DIRECTION CENSUS
Branch: dls-signed-flow-authority-v01

## Relationship to the prior calibration

The frozen 3-reference instruction calibration remains preserved as:
DRIFT_SIGNED_SEMANTICS_CALIBRATION_BLOCKED.

It is not reclassified.

That calibration exposed a population-unit mismatch: the deterministic references were selected from
successful `liquidate_perp` instruction candidates, while the parent
`SIGNED_FLOW_SOURCE_AUTHORITY_FREEZE_V0.1.md` explicitly adjudicates realized events.

One of the three pre-existing source logs already proves a no-transfer early return:
`max_base_asset_amount_allowed_to_be_transferred == 0`.

This population phase is a new source-only census. It does not modify the directional mapping
and does not use market returns or later prices.

## Frozen population

Canonical source:
- run: 36264543005
- artifact: dls-field-enrichment-drift-drift-202301
- artifact ID: 10915721179
- digest: sha256:47c9f1af96c29c2c7ea80f2a167d27c932932f956ae8b650a5388cb9b14730c8
- interval: [2023-01-01T00:00:00Z, 2023-02-01T00:00:00Z)
- class: `liquidate_perp`
- canonical instruction candidates observed before this freeze: 3,179

Every canonical candidate is included. No candidate may be selected or discarded based on
the sign of its realized delta.

## Historical protocol semantics authority

Use the same historical authority frozen in
`DRIFT_JAN2023_SIGNED_FLOW_SEMANTICS_CALIBRATION_FREEZE_V0.1.md`.

Repository identity:
- GitHub repository ID: 497045217
- legacy path `drift-labs/protocol-v2` redirects to the same repository now at
  `velocity-exchange/protocol-v2`.

Relevant January semantics are fixed:
- actual perp transfer produces `user_position_delta`;
- `LiquidatePerpRecord.base_asset_amount` equals that signed user delta;
- Long execution => positive base delta;
- Short execution => negative base delta;
- liquidated Long closes Short; liquidated Short closes Long.

## Frozen event decoder

Use the January-2023 Borsh `LiquidationRecord` layout and the Anchor discriminator:
first 8 bytes of SHA256("event:LiquidationRecord").

Exact identity binding requires:
- exact canonical transaction signature;
- successful parent transaction;
- Drift program event;
- liquidation_type = LiquidatePerp;
- event user = canonical liquidated_user;
- event liquidator = canonical liquidator;
- event market_index = canonical perp_market_index;
- if transport supplies instructionAddress, it must equal the canonical instructionAddress.

## Realized-event classification

For each of the 3,179 canonical candidates:

### PROVEN_REALIZED
Exactly one bound `LiquidationRecord` exists and
`liquidate_perp.base_asset_amount != 0`.

Directional label is frozen:
- base_asset_amount < 0 => SIGNED_SELL_PRESSURE_PROVEN
- base_asset_amount > 0 => SIGNED_BUY_PRESSURE_PROVEN

### PROVEN_NOT_REALIZED
A candidate is excluded from the realized-event denominator only if source semantics prove zero
realized perp base transfer through one of these frozen conditions:

1. exactly one bound `LiquidationRecord` exists with `base_asset_amount == 0`; or
2. no bound LiquidationRecord exists and the exact successful transaction contains the
   January-source early-return log:
   - `User has no base asset amount`; or
   - `max_base_asset_amount_allowed_to_be_transferred == 0`.

No other no-event case may be silently treated as non-realized.

### SOURCE_EVIDENCE_INCOMPLETE
Conservatively classify as incomplete if:
- exact successful transaction cannot be recovered;
- query transport is incomplete;
- no bound LiquidationRecord exists and neither frozen explicit no-transfer log is present;
- decoded LiquidationRecord(s) exist but identity binding fails;
- more than one exact bound record exists for one canonical candidate and cannot be uniquely resolved.

Unresolved candidates are treated as POTENTIALLY REALIZED for the conservative source-coverage denominator.

### CONTRADICTION
A contradiction exists if exact bound source records for one canonical candidate imply opposing
non-zero signed directions or if an exact bound event conflicts with the canonical instruction identity.

## Frozen metrics

Let:
- R = count of PROVEN_REALIZED non-zero events;
- I = count of SOURCE_EVIDENCE_INCOMPLETE candidates;
- B = SIGNED_BUY_PRESSURE_PROVEN;
- S = SIGNED_SELL_PRESSURE_PROVEN;
- C = contradictions.

Conservative source coverage:
R / (R + I)

Deterministic directional rate:
(B + S) / R

If R = 0, fail closed.

This conservative coverage is intentionally stricter than assuming unresolved candidates are non-realized.

## Family PASS rule

Drift `liquidate_perp` becomes `SIGNED_FLOW_AUTHORIZED` only if:
1. conservative source coverage >= 0.95;
2. deterministic directional rate >= 0.90;
3. contradictions = 0;
4. R > 0;
5. the label is explainable exclusively from the frozen protocol/transaction semantics.

PASS classification:
`DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_AUTHORIZED`

Otherwise:
`DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_PARTIAL`
unless a hard source failure makes the route unusable, in which case
`DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_BLOCKED`.

A PASS authorizes only a future separately frozen signed-return experiment.
It does not authorize trading.

## Query/reproducibility

Query the public/free SQD Solana finalized stream.
Requests may be deduplicated by exact slot for transport efficiency, but each canonical
signature/instructionAddress must be adjudicated independently.

Concurrency, retry, and slot-query caching are transport-only implementation details and may not alter
population membership or classification rules.

## Firewall

prices=false
returns=false
future_market_direction=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
