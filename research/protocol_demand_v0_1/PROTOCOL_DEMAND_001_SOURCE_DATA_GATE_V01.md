# PROTOCOL-DEMAND-001 — SOURCE/DATA GATE V0.1

Date: 2026-09-14
Branch: `protocol-demand-v0.1`
Program: CRYPTO GAP ANALYSIS V2 — Priority #11

## Governance

- Research-only.
- Source/provenance stage only.
- No market outcomes computed.
- No returns, PnL, beta, PF, drawdown, signal performance or price-response metrics computed.
- 2025 LOCKED.
- 2026 LOCKED.
- No live trading.
- No exchange mutation.
- No merge to main.
- No post-outcome tuning.

## Candidate information family

Protocol demand / fee intensity: economic usage measured from protocol fees and protocol-retained revenue, materially distinct from ordinary OHLC/indicator transforms.

## Source reconnaissance

Primary candidate source: DefiLlama Fees & Revenue.

Observed source semantics from public documentation:

- Fees: total fees paid by users when using a protocol.
- Revenue: subset of fees retained by the protocol / treasury / team / token holders, excluding liquidity-provider distributions under the published definition.
- Public fees endpoints include protocol overview and protocol summaries with historical data.
- Public protocol summary endpoint: `/summary/fees/{protocol}`.
- Historical chart access is exposed as a full-history response; public documentation for the protocol summary does not specify server-side `start` / `end` parameters capable of proving that only <=2024 observations are returned.
- Current official SDK documentation separately identifies dedicated historical chart methods as Pro-gated.

## Fail-closed governance finding

The current laboratory authority locks 2025 and 2026. A source acquisition method that downloads a full-history payload containing locked years and filters them locally afterwards would still constitute access to protected source observations.

Because the public protocol-summary contract does not provide a documented server-side date boundary, this lab cannot prove that acquisition is restricted to <=2024 before bytes are received.

Therefore the candidate free historical source cannot be used for the frozen Discovery under current governance.

## Classification

`SOURCE_GOVERNANCE_BLOCKED`

This is NOT:

- NO_EDGE
- DISCOVERY_FAIL
- NEGATIVE_EXPECTANCY
- INSUFFICIENT_SAMPLE
- DATA_FAILURE

No scientific market-outcome conclusion is permitted.

## What would unblock

One of the following, established prospectively before any protected bytes are accessed:

1. A documented source endpoint supporting server-side end-date <= 2024-12-31 for the required fees/revenue series; or
2. A source-native historical archive/snapshot whose object boundaries end <= 2024-12-31; or
3. Explicit future governance authorization to access later source-only observations without opening market outcomes.

Paid-data rescue is not authorized by this closeout.

## Terminal status

SOURCE/DATA GATE: BLOCKED
OUTCOMES: UNOPENED
2025: UNOPENED
2026: UNOPENED
LIVE TRADING: DISABLED
EXCHANGE MUTATION: DISABLED
