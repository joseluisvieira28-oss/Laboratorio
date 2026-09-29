# DLS — DRIFT JAN-2023 SIGNED-FLOW ADJUDICATION CORRECTION V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: SCIENTIFIC CORRECTION / NO MARKET OUTCOMES OPENED

## Problem

Run 36525438771 produced a source-valid January-2023 population receipt whose internal classification was:

DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_AUTHORIZED

based on the sign of the liquidated user's realized `LiquidatePerpRecord.base_asset_amount`.

That classification cannot be used as signed market-flow authority.

## Pre-existing controlling authority

Before the January population freeze and run, commit
75d9aa09d51fa369bd4b6dfc24527d4802b85091
had already frozen:

DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_SEMANTICS_V0.1.md

That authority establishes that direct `liquidate_perp` is a position transfer:
- liquidated user closes exposure;
- designated liquidator takes the original exposure;
- the two PositionDelta values are opposite;
- the synthetic liquidation Fill is user ↔ liquidator;
- therefore the signed user delta proves transfer direction, not net external market buy/sell pressure.

Its frozen market-pressure label is:
DIRECTION_AMBIGUOUS.

The January population result was therefore over-classified relative to a controlling authority that already existed before the population run.

## Preserved valid evidence

Run 36525438771 remains scientifically useful for source coverage and realized transfer evidence:
- PROVEN_REALIZED: 2,237
- PROVEN_NOT_REALIZED: 920
- SOURCE_EVIDENCE_INCOMPLETE: 22
- CONTRADICTION: 0
- conservative coverage: 0.9902611775121736

The observed base-delta signs remain valid protocol-native position-transfer evidence.

They MUST NOT be interpreted as:
SIGNED_BUY_PRESSURE_PROVEN or SIGNED_SELL_PRESSURE_PROVEN
for external market pressure under the parent signed-flow mission.

## Correct adjudication

Direct Drift `liquidate_perp`:
- source evidence: STRONG
- signed position transfer: PROVEN
- external market pressure: DIRECTION_AMBIGUOUS
- SIGNED_FLOW_AUTHORIZED: FALSE

This correction does not use prices, returns, 2025, 2026, or any market outcome.

## Remaining Drift candidate

`liquidate_perp_with_fill` remains scientifically distinct and may prove signed external pressure
only under its separately frozen source rules.

## Firewall

prices=false
returns=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_market_labeling=false
