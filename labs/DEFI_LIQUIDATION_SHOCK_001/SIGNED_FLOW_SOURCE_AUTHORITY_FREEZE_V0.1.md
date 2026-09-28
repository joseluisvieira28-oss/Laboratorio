# DEFI-LIQUIDATION-SHOCK-001 — SIGNED-FLOW SOURCE AUTHORITY FREEZE V0.1

Date: 2026-09-28
Branch: dls-signed-flow-authority-v01
Status: FROZEN SOURCE-FIRST MISSION / NO NEW MARKET OUTCOMES REQUIRED

## Purpose

Determine whether realized liquidation source transactions can support a defensible signed economic-flow direction before any new protected market outcome is opened.

V0.1 established direction-agnostic volatility expansion.
This mission must not assume that seized collateral is sold, that repaid debt implies buy pressure, or that a Drift liquidation has one universal signed direction.

## Scientific question

For each frozen protocol/class, can source transaction evidence prove a deterministic signed market-flow interpretation that is known at or immediately after the liquidation transaction and does not depend on later price movement?

## Candidate evidence hierarchy

Tier A — realized token balance / transfer evidence:
- realized collateral transferred to liquidator;
- realized debt repayment/transfer;
- destination owner/account identity;
- same-transaction token transfers or swaps.

Tier B — protocol-native position deltas:
- Drift perp base-position change;
- Drift quote/PnL settlement;
- spot borrow/deposit deltas;
- liquidation transfer semantics proven from program/source authority.

Tier C — same-transaction DEX execution:
- exact token swap after liquidation within the same transaction;
- exact sold/bought asset and realized amount;
- source program identity.

Tier D — post-transaction wallet behavior:
NOT authorized in V0.1 for directional labeling because it introduces discretionary temporal linking.

## Required labels

For every realized liquidation source event:
- SIGNED_SELL_PRESSURE_PROVEN
- SIGNED_BUY_PRESSURE_PROVEN
- DIRECTION_AMBIGUOUS
- SOURCE_EVIDENCE_INCOMPLETE

No event may be direction-labeled from later market return.

## Family authority rule

A protocol/class can become SIGNED_FLOW_AUTHORIZED only if:
1. >= 95% of realized events in its source-audited period receive a non-incomplete source evidence record;
2. >= 90% of those records admit one deterministic signed interpretation under a single pre-frozen rule;
3. contradictions = 0 after canonical source reconciliation;
4. the rule is explainable from transaction/program semantics alone.

Otherwise the family remains DIRECTION_AMBIGUOUS / SOURCE_BLOCKED and cannot enter a signed-return experiment.

## Amount authority

Requested/max instruction arguments are forbidden as realized flow.

Realized amount may be used only if supported by:
- token balance delta;
- transfer amount;
- protocol-native settled position delta;
- exact unit/decimal authority already frozen in V0.1.

## Market-outcome firewall

This source mission does not need 2025/2026 market returns.

2025_market_outcomes_opened=false
2026_market_outcomes_opened=false
new_returns_opened=false
post_outcome_direction_labeling=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false

## Terminal classifications

SIGNED_FLOW_SOURCE_PASS
- at least one protocol/class satisfies the family authority rule.

SIGNED_FLOW_SOURCE_PARTIAL
- source evidence is valid but no family reaches the required directional coverage threshold.

SIGNED_FLOW_SOURCE_BLOCKED
- required source transaction evidence cannot be acquired or reconciled defensibly.

A PASS only authorizes a separately frozen signed-return experiment.
It does not authorize trading.
