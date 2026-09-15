# OPTIONS-EXPIRY-GAMMA-001 — SOURCE FEASIBILITY CLOSEOUT V0.1

Date: 2026-09-16

## Classification

**SOURCE_ACCESS_BLOCKED / SOURCE_ENGINEERING_NOT_PROVEN**

This is a source/provenance classification only. It is **not** NO_EDGE, NEGATIVE_EXPECTANCY, INSUFFICIENT_SAMPLE, or any market-outcome verdict.

## Proposed information family

Bitcoin options expiry / dealer-gamma reversal on Deribit. The intended mechanism requires point-in-time historical option-chain state before each tested expiry, including at minimum strike, expiry, option type, open interest and sufficient contemporaneous option valuation/Greek inputs to reconstruct gamma exposure without future information.

This mechanism is distinct from the closed OPTIONS-SPOTPERP-001 trade-IV skew hypothesis.

## Outcome-blind source feasibility findings

Official Deribit documentation currently exposes open interest and option Greeks (including gamma) through current/real-time ticker/order-book market data. The official historical public market-data routes located in this audit provide historical trades and a limited mark-price history; the documented mark-price history is available only for a subset of options participating in volatility-index calculations.

The official Deribit Metrics interface documents current option open interest by strike/expiry and total option open interest over time, including chart CSV export. This does not establish a reproducible historical sequence of point-in-time strike-by-expiry OI snapshots with contemporaneous Greeks sufficient for a causal dealer-gamma reconstruction.

Deribit itself identifies external historical-data partners such as Tardis for historical open-interest/options-chain data. Deribit's 2022 Tardis promotion described high-frequency historical open interest/options-chain access, but the free access window was a temporary 2022 promotion and is not a current reproducible free source contract for the required Discovery history.

## Fail-closed decision

No historical BTC return, expiry response, reversal metric, PnL, hit rate, Sharpe, or strategy outcome was opened or computed.

Do not infer historical OI/gamma from the current chain. Do not forward-fill current OI backward. Do not reconstruct historical gamma using present-day chain state. Do not substitute total-OI-over-time for strike-level point-in-time exposure. Do not use a paid/vendor source unless a future protocol explicitly authorizes and pins that source before outcomes.

The exact source-feasibility attempt is closed as **SOURCE_ACCESS_BLOCKED / SOURCE_ENGINEERING_NOT_PROVEN** under the current free/cheap-data-first governance.

## Firewalls

- 2025 outcome access: FALSE
- 2026 outcome access: FALSE
- BTC market outcomes opened: FALSE
- PnL computed: FALSE
- Live trading: FALSE
- Exchange mutation: FALSE
- Merge to main: FALSE
- Post-outcome tuning: FALSE

## Routing

The mechanism remains scientifically plausible but operationally blocked. A future reopening requires a new or explicitly re-authorized source contract that can reproduce point-in-time historical strike/expiry OI and gamma inputs before any outcome access.
