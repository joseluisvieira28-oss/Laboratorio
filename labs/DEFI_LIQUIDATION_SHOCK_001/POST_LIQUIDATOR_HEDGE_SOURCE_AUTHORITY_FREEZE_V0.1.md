# DLS — POST-LIQUIDATOR-HEDGE-001 — SOURCE AUTHORITY FREEZE V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Motivation

DLS V0.1 proved direction-agnostic post-liquidation volatility expansion.
Signed-Flow V0.1 established that direct protocol liquidation transfers do not automatically prove net external market pressure.

This distinct mission asks whether the liquidation actor subsequently externalizes the received exposure.

## Scientific question

After a realized liquidation transfer, does the same liquidator authority execute a source-provable hedge/disposal action within a fixed, pre-frozen short window?

## Primary window

Primary post-event source window:
0 < elapsed_time <= 60 seconds after the canonical realized liquidation transaction timestamp.

The 60-second window is frozen before any post-event wallet-behavior query and matches the already-established cascade quiet-period scale. It is not selected from later returns.

No alternate window may rescue a failed primary result under V0.1.

## Eligible source families

Phase 1 feasibility:
- Drift direct liquidate_perp;
- Save0c;
- Save11;
- Kamino.

Only canonical V0.1 source events may seed the probe.

## Actor identity

Use only protocol/source-authoritative actor accounts already present in the canonical liquidation instruction:
- Drift: authority and liquidator account roles;
- lending families: canonical liquidator/transfer destination roles where source authority exists.

Do not infer actor identity from later profitable behavior.

## Post-event source labels

For each seed event:
- EXTERNAL_HEDGE_SELL_PROVEN
- EXTERNAL_HEDGE_BUY_PROVEN
- INTERNAL_REBALANCE_ONLY
- NO_EXTERNAL_ACTION_OBSERVED
- SOURCE_EVIDENCE_INCOMPLETE

A directional hedge label requires a successful source transaction/action after the seed event whose exact asset direction is decoded from program/instruction semantics.

Wallet/account appearance alone is insufficient.

## Phase 1 feasibility gate

Use three deterministic source events per family where available.

PASS for a family feasibility route requires:
- exact seed identity recovered 3/3;
- post-event search interval reproducible 3/3;
- actor identity queryable 3/3;
- source transactions can be reconstructed without price/return fields;
- contradictions = 0.

This only opens a population census. It does not prove direction prevalence.

## Family population authority

A later population-level family may become HEDGE_FLOW_AUTHORIZED only if:
- source evidence coverage >= 95%;
- deterministic external signed hedge/disposal label >= 90% among covered events;
- contradictions = 0.

Otherwise it remains descriptive / ambiguous.

## Firewalls

prices=false
returns=false
market_2025_opened=false
market_2026_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets_mutation=false
exchange_mutation=false
merge_main=false
