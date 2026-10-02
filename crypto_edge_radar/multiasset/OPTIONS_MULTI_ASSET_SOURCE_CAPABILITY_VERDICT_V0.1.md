# OPTIONS MULTI-ASSET — SOURCE CAPABILITY VERDICT V0.1

Date: 2026-10-02
Status: SOURCE-CAPABILITY ADJUDICATION
Scope: ETH / SOL / XRP preparation only
No outcomes opened. No exchange mutation. No live orders.

## Verdict

ETH: SOURCE_CAPABILITY_PASS_WITH_ADAPTER_WORK
SOL: SOURCE_CAPABILITY_PASS_WITH_ADAPTER_WORK
XRP: SOURCE_CAPABILITY_PASS_WITH_ADAPTER_WORK

This is NOT a scientific edge verdict and NOT a promotion.

## Evidence

Current Deribit contract documentation lists linear USDC options for BTC, ETH, SOL and XRP. SOL and XRP are explicitly linear USDC option families; ETH has both inverse and linear availability.

Current Deribit contract-introduction policy lists option expiries for:
- ETH inverse and linear;
- SOL linear;
- XRP linear.

Therefore all three proposed new hooks have a currently documented native options family suitable for a source adapter/probe.

## Critical implementation finding

The existing BTC V2.1 parser cannot be copied blindly.

Current BTC parser expects exactly:
BTC-DDMMMYY-STRIKE-C/P

Current linear USDC options use an asset-plus-USDC instrument family. Therefore ETH/SOL/XRP require an explicit parser/normalizer and convention proof before any historical source gate.

The adapter must bind:
- asset identity;
- quote/settlement convention;
- expiry;
- strike;
- side;
- trade timestamp;
- trade_id;
- IV;
- index/underlying price;
- pagination completeness;
- duplicate handling.

## Science firewall

No BTC thresholds are authorized for ETH/SOL/XRP by this verdict.

The source capability result answers only:
"Can a defensible native options source family exist for this asset?"

It does not answer:
"Does the BTC skew mechanism transfer profitably?"

Each asset remains PROTECTED / OUTCOMES LOCKED until a pre-outcome scientific freeze is committed.

## Next state

ETH: READY_FOR_PRE_OUTCOME_FREEZE_AND_SOURCE_ADAPTER
SOL: READY_FOR_PRE_OUTCOME_FREEZE_AND_SOURCE_ADAPTER
XRP: READY_FOR_PRE_OUTCOME_FREEZE_AND_SOURCE_ADAPTER

BTC: UNCHANGED
