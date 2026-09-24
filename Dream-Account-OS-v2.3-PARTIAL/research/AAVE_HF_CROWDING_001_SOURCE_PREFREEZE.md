# AAVE-HF-CROWDING-001 — OFFICIAL AAVE MCP SOURCE CAPABILITY GATE — PRE-FREEZE

Date frozen: 2026-09-24
Status: SOURCE_CAPABILITY_PRE-FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Primary family: CREDIT
Secondary family: FLOW
Research only: TRUE

## New mechanism family

This lab does NOT reopen AAVE-CREDIT-STRESS-001. The closed MVE tested daily Aave USDC variable-borrow-rate changes as a predictor of next-day BTC and failed Discovery.

This lab asks a materially different prospective question: whether concentration of borrower health-factor stress / liquidation proximity can become a defensible credit-state predictor.

No predictor is finalized until source capability is proven.

## Source gate question

Can the official Aave MCP endpoint, without an API key, provide read-only capabilities sufficient to support:
1. wallet positions / aggregate health;
2. wallet health-factor history over a window;
3. protocol market/reserve state and time-series or histories;
4. read-only operation without requiring signing, wallet mutation or private credentials?

Endpoint authority:
- https://mcp.aave.com/

## Frozen capability requirements

The source capability gate passes only if:
- unauthenticated JSON-RPC POST to the official endpoint succeeds;
- `tools/list` returns at least one tool;
- exact tool `get_user_summary` is present;
- exact tool `get_user_positions` is present;
- exact tool `get_user_summary_history` is present;
- the returned tool catalogue contains at least one read capability whose name or description references market/reserve data;
- the returned tool catalogue contains at least one read capability whose name or description references history/time-series.

The receipt may retain tool names, descriptions and input-schema keys only.
It must NOT call any write/action/prepare/submit/sign tool.

## Classification

PASS:
`OFFICIAL_AAVE_MCP_CREDIT_SOURCE_CAPABILITY_PASS`

FAIL:
`OFFICIAL_AAVE_MCP_CREDIT_SOURCE_CAPABILITY_INSUFFICIENT`

## Firewall

Forbidden:
- wallet addresses;
- borrower outcomes;
- health-factor values;
- liquidation outcomes;
- market prices;
- BTC/ETH returns;
- PnL;
- action preparation;
- signing;
- mutation;
- live trading;
- merge to main.
