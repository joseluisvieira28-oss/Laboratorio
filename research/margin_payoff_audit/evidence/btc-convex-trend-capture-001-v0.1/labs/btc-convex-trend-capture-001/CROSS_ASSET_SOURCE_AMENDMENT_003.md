# BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE AMENDMENT 003

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE ANY CROSS-ASSET ECONOMIC OUTCOME IS OPENED  
**Scope:** funding transport and mark-price provenance only  
**Authority:** additive; preserves Amendments 001 and 002 history

## Trigger

The original USD-M Futures funding transport at:
`https://fapi.binance.com/fapi/v1/fundingRate`
returned HTTP 451 from GitHub Actions.

A transport-only probe opened no economic outcomes and found:

`https://www.binance.com/fapi/v1/fundingRate`

returns HTTP 200 and the same public funding-history record shape, including:
- symbol;
- fundingTime;
- fundingRate;
- markPrice;
- rateType.

This route removes the need to approximate funding notional with a market-bar fallback.

## Prior runs

Any cross-asset economic workflow launched before this amendment that:
- used Binance Vision funding archives without record-level markPrice; or
- substituted an hourly market OPEN/CLOSE for an available official funding markPrice

is classified:

**INVALID_UNOPENED_DO_NOT_USE**

Its economic logs and artifacts must not be inspected, cited, or used for decisions.

## Authorized funding source

Use:

`https://www.binance.com/fapi/v1/fundingRate`

with chronological pagination over the frozen evaluation interval.

Every in-window funding record must contain:
- fundingTime;
- fundingRate;
- markPrice.

Validation:
- fundingTime integer and strictly chronological after deduplication;
- fundingRate finite;
- markPrice finite and > 0;
- first event must cover the start boundary within the natural funding schedule;
- last event must cover the end boundary within the natural funding schedule.

If any required record lacks markPrice:
**DATA_BLOCKED**.

No market-price fallback is permitted in this cross-asset experiment after Amendment 003.

## Funding cashflow

For a long held across an official funding timestamp:

`funding_cashflow = -qty × markPrice × fundingRate`

using that exact record's markPrice.

## Unchanged science

Unchanged:
- ETHUSDT / SOLUSDT / BNBUSDT;
- 1h;
- 2021-01-01 through 2025-12-31;
- 2026 locked;
- exact Parent V5;
- exact Sticky H1;
- causal execution;
- 95% sizing;
- 10 bps commission/side;
- REPRO 0 bps slippage;
- BASE 2 bps adverse slippage/side;
- STRESS 5 bps adverse slippage/side;
- scientific gates;
- no-rescue rules.

## Gate

A fresh Source Gate under Amendment 003 must PASS before any newly launched economic result may be opened.
