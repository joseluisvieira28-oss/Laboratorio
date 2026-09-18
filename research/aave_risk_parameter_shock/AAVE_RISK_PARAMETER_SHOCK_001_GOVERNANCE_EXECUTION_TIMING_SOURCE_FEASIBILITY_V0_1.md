# AAVE-RISK-PARAMETER-SHOCK-001 — GOVERNANCE / EXECUTION TIMING SOURCE FEASIBILITY V0.1

Date: 2026-09-18
Status: SOURCE-ONLY / OUTCOME-BLIND / NO MARKET OUTCOMES OPENED

## Purpose

Determine whether a later pre-Discovery protocol can distinguish:

1. when a risk-parameter change became publicly knowable or governable; and
2. when the parameter change was actually executed on-chain.

This document does NOT define a trading signal, horizon, direction, threshold, market target or outcome.

## Authoritative source findings

### On-chain execution anchor

The canonical Ethereum V3 PoolConfigurator emits:

`CollateralConfigurationChanged(address asset, uint256 ltv, uint256 liquidationThreshold, uint256 liquidationBonus)`

This event is the deterministic execution-time anchor for the frozen primary mechanism.

### Governance proposal timing

Aave governance proposal pages expose explicit lifecycle fields including:
- Created block/time;
- Started block/time;
- Ended block/time;
- Executed time;
- proposal author and links to supporting discussion/payload.

Example source:
https://governance-v2.aave.com/governance/proposal/247/

That Aave V3 Ethereum proposal reports its Created, Started, Ended and Executed timestamps/blocks and lists liquidation-threshold parameter changes.

### Risk Steward capability

The official Aave risk-stewards repository documents that Risk Stewards can change:
- LTV;
- Liquidation Threshold;
- Liquidation Bonus;
- supply/borrow caps;
- selected interest-rate parameters;
- other bounded risk parameters.

Source:
https://github.com/aave-dao/aave-v3-risk-stewards/blob/main/README.md

Current Aave governance documentation also describes collateral risk configurations and steward controls:
https://aave.com/help/governance/aave-community

### Public recommendation/discussion timing

Aave Governance forum risk posts expose publication timestamps and the proposed parameter changes. These are potentially useful as a public-information timestamp for steward-driven changes, but exact 2023-2024 mapping must be proved event-by-event before any later use.

Forum:
https://governance.aave.com/

## Source-feasibility conclusion

`GOVERNANCE_EXECUTION_TIMING_SOURCE_FEASIBLE`

This conclusion means only that public source families exist for a later deterministic timing lineage.

It does NOT establish:
- that every 2023-2024 liquidation-threshold decrease has a recoverable pre-execution public announcement;
- that proposal/forum timestamps are always the first public information;
- that governance and Risk Steward paths share identical timing semantics;
- any predictive edge.

## Required later lineage audit if source census passes

Before Discovery, every eligible primary-mechanism event must be assigned one of these source classes prospectively:

1. `GOVERNANCE_PROPOSAL_LINEAGE`
   - exact proposal/payload identity;
   - created/start/end/execution fields;
   - exact on-chain configurator event mapping.

2. `RISK_STEWARD_LINEAGE`
   - exact steward transaction;
   - exact public recommendation/discussion source if one exists;
   - exact on-chain configurator event mapping.

3. `UNRESOLVED_PUBLIC_TIMING`
   - no defensible first-public-information timestamp recovered.

No event may be silently assigned an announcement timestamp from a later article, retrospective summary, or post-execution discussion.

## Fail-closed rule

If the later scientific question depends on public anticipation timing, `UNRESOLVED_PUBLIC_TIMING` events must be handled according to a separately frozen rule before outcomes. They may not be dropped after outcomes merely because they hurt the result.

## Hard firewall

No market prices.
No returns.
No PnL.
No health factor.
No overhang.
No future liquidation outcomes.
No 2025/2026 outcome access.
No live trading.
No orders.
No wallets.
No exchange mutation.
No main merge.
