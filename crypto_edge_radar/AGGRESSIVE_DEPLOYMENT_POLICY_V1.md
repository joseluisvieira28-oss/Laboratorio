# CRYPTO EDGE RADAR — AGGRESSIVE DEPLOYMENT POLICY V1

Status: **FROZEN FOR DEPLOYMENT PREP — 2026-09-16**  
Branch: `crypto-edge-radar-aggressive-v0.3`  
Scope: deployment/risk governance only. This policy does **not** rewrite any historical scientific verdict.

## Objective

Reduce unnecessary calendar waiting after a candidate has already accumulated strong independent evidence, while preserving fail-closed scientific and risk controls.

The deployment ladder is no longer a rigid time queue. Scientific tier and capital state are separate dimensions.

## Scientific-state mapping

- **Tier 1 / Validated Edge**: may be evaluated for micro-live deployment after the execution and risk gates below pass.
- **Tier 2 / Promoted Candidate**: may be evaluated for micro-live deployment after the execution and risk gates below pass. Fragility flags remain binding.
- **Tier 3 / Watchlist / Weak Candidate**: shadow-only. No real-money deployment.
- **Tier 4 / Rejected / Stone**: blocked. No shadow signal may be promoted into a capital signal.
- **Blocked / provenance / data / technical / insufficient-sample**: no capital deployment until the blocker is resolved under its own prospective governance.
- **Post-outcome secondary survivor / subgroup diagnostic**: shadow/diagnostic only unless separately re-certified prospectively. It cannot inherit capital permission from a failed primary candidate.

## Micro-live eligibility gates

A Tier 1 or Tier 2 candidate is `MICRO_LIVE_READY` only when **all** are true:

1. exact immutable strategy identity is known;
2. exact source/provider and market family are bound;
3. deterministic strategy adapter is implemented and tested;
4. the adapter reproduces the frozen rule without added filters or tuning;
5. execution instrument and venue are explicitly frozen;
6. realistic fees/slippage assumptions are recorded;
7. a strategy-specific maximum-loss / sizing model exists;
8. account-level risk limits are active;
9. signal, proposed order parameters and execution receipt are logged before/after any manual execution;
10. no scientific rule changes are made from live outcomes.

Any missing gate => `BLOCKED_FROM_MICRO_LIVE` while shadow observation may continue when scientifically authorized.

## Default account risk envelope

These are conservative launch defaults, not a claim about expected profitability:

- planned risk per trade: **0.10% of account equity**;
- maximum simultaneous planned risk: **0.30%**;
- daily stop: **0.30% of account equity**;
- weekly stop: **0.75% of account equity**;
- no size escalation during the initial validation block;
- no martingale;
- no averaging down outside the frozen strategy;
- no revenge/recovery trades;
- no late entry after the frozen entry window;
- leverage may implement exposure but may not increase planned account risk above the limits.

### Strategies without a deterministic stop / maximum-loss model

The 0.10% risk-per-trade rule must **not** be converted into arbitrary notional size when a strategy has no frozen stop or bounded loss definition.

Such a strategy remains `BLOCKED_MISSING_STRATEGY_RISK_MODEL` until the execution instrument and a defensible loss/exposure model are frozen prospectively. This prevents pretending that notional exposure equals risk.

## Evidence and execution log

Every prospective signal must preserve at minimum:

- strategy ID and scientific tier;
- signal timestamp and source timestamp;
- source/provider identity;
- direction and frozen reason;
- theoretical entry and execution window;
- proposed size and risk budget;
- expected fees/slippage;
- actual fill if manually executed;
- actual fees/slippage;
- exit/invalidation rule;
- realized result in currency, percent and R where R is well-defined;
- whether the signal was shadow-only or micro-live;
- immutable evidence hash/receipt.

## Capital escalation

No automatic escalation exists in V1. Capital increases require a separate explicit review of live execution evidence. A winning streak alone is not sufficient.

## Safety boundary

This branch adds **advisory sizing, eligibility and signal-preparation infrastructure only**. It must not contain authenticated exchange credentials, balance access, order creation, cancellation, amendment, wallet signing or autonomous live execution.
